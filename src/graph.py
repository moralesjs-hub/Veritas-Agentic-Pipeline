import os
from dotenv import load_dotenv
from typing import Literal
from pydantic import BaseModel, Field

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, END

from src.state import AgentState, FactCheckResult
from src.tools.search import run_web_search

load_dotenv()

# Initialize Gemini Model
# Initialize Gemini Model with strict request timeout
llm = ChatGoogleGenerativeAI(
    model="gemini-3.8-flash",
    google_api_key=os.getenv("GEMINI_API_KEY"),
    temperature=0.2,
    request_timeout=30.0
)

# Schemas for Structured Output
class SearchQueries(BaseModel):
    queries: list[str] = Field(description="2 to 3 targeted search queries to investigate the topic")

class VerificationVerdict(BaseModel):
    is_fully_supported: bool = Field(description="True only if every claim is backed by evidence")
    critique: str = Field(description="Feedback on ungrounded claims or missing citations")
    claims: list[FactCheckResult] = Field(description="Detailed verification for each claim")

def extract_text(content) -> str:
    """Normalizes response content to plain text regardless of SDK format."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        text_parts = [item.get("text", "") if isinstance(item, dict) else str(item) for item in content]
        return "\n".join(text_parts)
    return str(content)

# Agent Nodes
def planner_node(state: AgentState) -> dict:
    """Generates focused search queries."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert Research Planner. Generate 2-3 specific search engine queries to gather factual evidence."),
        ("human", "Topic to research: {query}\nPrevious critique (if any): {critique}")
    ])
    
    structured_planner = llm.with_structured_output(SearchQueries)
    result = structured_planner.invoke(
        prompt.format_messages(query=state["query"], critique=state.get("critique", "None"))
    )
    return {
        "search_queries": result.queries,
        "status": "RESEARCHING"
    }

def research_node(state: AgentState) -> dict:
    """Executes searches and gathers evidence snippets."""
    new_docs = []
    for q in state.get("search_queries", []):
        snippets = run_web_search(q, max_results=2)
        new_docs.extend(snippets)
        
    return {
        "retrieved_docs": new_docs,
        "status": "SYNTHESIZING"
    }

def synthesizer_node(state: AgentState) -> dict:
    """Drafts a cited markdown summary based on retrieved evidence."""
    evidence_block = "\n\n---\n\n".join(state.get("retrieved_docs", []))
    sys_instruction = (
        "You are a Rigorous Research Synthesizer. Write a structured Markdown report answering the query.\n"
        "STRICT RULES:\n"
        "1. Ground every claim directly in the provided evidence.\n"
        "2. Cite sources where applicable.\n"
        "3. If evidence is insufficient, explicitly state the gap rather than guessing."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_instruction),
        ("human", "Topic: {query}\n\nEvidence:\n{evidence}\n\nPrevious Critique (if any): {critique}")
    ])
    
    response = llm.invoke(
        prompt.format_messages(
            query=state["query"],
            evidence=evidence_block,
            critique=state.get("critique", "None")
        )
    )
    return {
        "draft": extract_text(response.content),
        "status": "VERIFYING"
    }

def verifier_node(state: AgentState) -> dict:
    """Validates draft claims against raw evidence to prevent hallucinations."""
    current_iter = state.get("iteration_count", 0) + 1
    evidence_block = "\n\n---\n\n".join(state.get("retrieved_docs", []))
    sys_instruction = (
        "You are a Skeptical Fact-Checker. Inspect the draft against the raw evidence.\n"
        "Verify every factual assertion. If any claim is ungrounded or contradictory, flag is_fully_supported as False."
    )
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", sys_instruction),
        ("human", "Evidence:\n{evidence}\n\nDraft Report:\n{draft}")
    ])
    
    structured_verifier = llm.with_structured_output(VerificationVerdict)
    verdict = structured_verifier.invoke(
        prompt.format_messages(evidence=evidence_block, draft=state.get("draft", ""))
    )
    
    next_status = "APPROVED" if verdict.is_fully_supported or current_iter >= 2 else "REVISE"
    
    return {
        "fact_check_results": verdict.claims,
        "critique": verdict.critique,
        "verification_status": next_status,
        "iteration_count": current_iter
    }

# Conditional Routing
def route_next_step(state: AgentState) -> Literal["planner_node", "__end__"]:
    critique_msg = state.get("critique", "Refining search scope.")
    if state.get("verification_status") == "REVISE" and state.get("iteration_count", 0) < 2:
        print(f"\n[Verifier] Revision requested: {critique_msg}. Re-planning...\n")
        return "planner_node"
    return END

# Graph Construction
builder = StateGraph(AgentState)

builder.add_node("planner_node", planner_node)
builder.add_node("research_node", research_node)
builder.add_node("synthesizer_node", synthesizer_node)
builder.add_node("verifier_node", verifier_node)

builder.set_entry_point("planner_node")
builder.add_edge("planner_node", "research_node")
builder.add_edge("research_node", "synthesizer_node")
builder.add_edge("synthesizer_node", "verifier_node")
builder.add_conditional_edges("verifier_node", route_next_step)

agent_app = builder.compile()