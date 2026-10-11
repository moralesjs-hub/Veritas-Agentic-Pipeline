import pytest
from src.state import AgentState
from src.graph import route_next_step

def test_route_next_step_approved():
    """Graph must terminate when status is APPROVED."""
    state: AgentState = {
        "query": "Test query",
        "search_queries": [],
        "retrieved_docs": [],
        "draft": "Valid test draft.",
        "fact_check_results": [],
        "critique": "",
        "verification_status": "APPROVED",
        "iteration_count": 1
    }
    assert route_next_step(state) == "__end__"

def test_route_next_step_retry_under_cap():
    """Graph must loop back to planner when verification fails and under retry cap."""
    state: AgentState = {
        "query": "Test query",
        "search_queries": [],
        "retrieved_docs": [],
        "draft": "Draft with hallucinated claim.",
        "fact_check_results": [],
        "critique": "Claim unsupported by evidence.",
        "verification_status": "REVISE",
        "iteration_count": 1
    }
    assert route_next_step(state) == "planner_node"

def test_route_next_step_caps_at_max_iterations():
    """Graph must terminate even on REVISE if max iteration threshold is reached."""
    state: AgentState = {
        "query": "Test query",
        "search_queries": [],
        "retrieved_docs": [],
        "draft": "Draft needing revision.",
        "fact_check_results": [],
        "critique": "Unresolved critique.",
        "verification_status": "REVISE",
        "iteration_count": 2
    }
    assert route_next_step(state) == "__end__"