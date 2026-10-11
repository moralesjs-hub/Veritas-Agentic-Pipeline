import os
import sys
from typing import Annotated, Dict, List, TypedDict
from dotenv import load_dotenv

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

# --- 1. State Definition ---
class AgentState(TypedDict):
    topic: str
    queries: List[str]
    sources: List[Dict[str, str]]
    draft: str
    verdict: str
    feedback: str
    iteration: int


# --- 2. Structured Output Schemas ---
class ResearchQueries(BaseModel):
    queries: List[str] = Field(
        description="3-5 specific search queries targeting technical architectures and ground truths."
    )


class VerificationReport(BaseModel):
    verdict: str = Field(description="Must be 'PASSED' or 'NEEDS_REVISION'.")
    feedback: str = Field(
        description="Detailed critique identifying hallucinations, unsupported claims, or missing citations."
    )


# --- 3. Model & Tool Setup ---
def get_model():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is missing.")
    return ChatGoogleGenerativeAI(
        model="gemini-3.8-flash",
        temperature=0.2,
        google_api_key=api_key,
    )


# --- 4. Graph Nodes ---
def research_node(state: AgentState) -> Dict:
    """Formulates technical search queries and collects simulated/retrieved evidence."""
    llm = get_model()
    structured_llm = llm.with_structured_output(ResearchQueries)

    prompt = (
        f"You are a Senior Technical Researcher. Generate 3 precise search queries "
        f"to gather factual, state-of-the-art documentation for the topic: '{state['topic']}'."
    )
    result: ResearchQueries = structured_llm.invoke([HumanMessage(content=prompt)])

    # Simulated retrieval aggregation (or replace with live DuckDuckGo / Tavily tool calls)
    collected_sources = [
        {
            "query": q,
            "snippet": f"Ground-truth documentation snippet addressing {q} in 2026 architectures.",
            "url": f"https://arxiv.org/abs/{hash(q) % 1000000}",
        }
        for q in result.queries
    ]

    return {
        "queries": result.queries,
        "sources": collected_sources,
        "iteration": state.get("iteration", 0) + 1,
    }


def synthesis_node(state: AgentState) -> Dict:
    """Drafts a structured technical report grounded strictly in retrieved sources."""
    llm = get_model()
    sources_text = "\n\n".join(
        [f"- [{s['url']}]: {s['snippet']}" for s in state["sources"]]
    )

    feedback_context = (
        f"\n\nCRITICAL - Previous Verifier Feedback to fix:\n{state['feedback']}"
        if state.get("feedback")
        else ""
    )

    system_prompt = (
        "You are an Elite AI Systems Engineer. Draft a thorough, highly technical markdown report. "
        "Every claim must cite one of the provided source URLs. Avoid generic summaries; focus on "
        "concrete workflows, data flows, and trade-offs."
    )
    user_prompt = (
        f"Topic: {state['topic']}\n\n"
        f"Retrieved Evidence:\n{sources_text}"
        f"{feedback_context}"
    )

    response = llm.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)]
    )
    return {"draft": response.content}


def verifier_node(state: AgentState) -> Dict:
    """Audits the draft against evidence, checking for hallucinations and uncited assertions."""
    llm = get_model()
    structured_llm = llm.with_structured_output(VerificationReport)

    sources_text = "\n".join([f"- {s['url']}: {s['snippet']}" for s in state["sources"]])

    audit_prompt = (
        f"You are an Adversarial Fact Verifier.\n\n"
        f"Original Topic: {state['topic']}\n"
        f"Evidence Sources:\n{sources_text}\n\n"
        f"Draft Under Review:\n{state['draft']}\n\n"
        f"Verify that every technical claim is grounded in the sources. If there are unsupported assertions, "
        f"set verdict to 'NEEDS_REVISION' with corrective feedback. If accurate and cited, set verdict to 'PASSED'."
    )

    audit: VerificationReport = structured_llm.invoke([HumanMessage(content=audit_prompt)])
    return {"verdict": audit.verdict, "feedback": audit.feedback}


# --- 5. Conditional Routing ---
def route_after_verification(state: AgentState) -> str:
    """Determines whether to finalize or loop back for revisions (max 3 loops)."""
    if state["verdict"] == "PASSED":
        return END
    if state.get("iteration", 1) >= 3:
        return END
    return "synthesis"


# --- 6. Graph Compilation ---
def build_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("research", research_node)
    workflow.add_node("synthesis", synthesis_node)
    workflow.add_node("verifier", verifier_node)

    workflow.set_entry_point("research")
    workflow.add_edge("research", "synthesis")
    workflow.add_edge("synthesis", "verifier")

    workflow.add_conditional_edges(
        "verifier",
        route_after_verification,
        {"synthesis": "synthesis", END: END},
    )

    return workflow.compile()


# Global graph instance
pipeline_app = build_graph()


# --- 7. Execution Interface ---
def run_pipeline(topic: str) -> Dict:
    """
    Entry point for CLI, Streamlit, and FastAPI.
    Executes the full agent graph and returns final state.
    """
    initial_state: AgentState = {
        "topic": topic,
        "queries": [],
        "sources": [],
        "draft": "",
        "verdict": "",
        "feedback": "",
        "iteration": 0,
    }
    return pipeline_app.invoke(initial_state)


if __name__ == "__main__":
    test_topic = "Hierarchical Agentic AI Memory Architectures in 2026"
    if len(sys.argv) > 1:
        test_topic = " ".join(sys.argv[1:])

    print(f"🚀 Running Veritas Pipeline for: '{test_topic}'\n")
    final_output = run_pipeline(test_topic)

    print("=" * 60)
    print(f"VERDICT: {final_output['verdict']}")
    print(f"ITERATIONS: {final_output['iteration']}")
    print("=" * 60)
    print("\n--- FINAL REPORT ---\n")
    print(final_output["draft"])