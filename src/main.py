import sys
from src.graph import agent_app

def main():
    topic = "What are the latest breakthroughs in agentic AI memory architectures in 2025-2026?"
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])

    print("=== Starting Autonomous Research Pipeline ===")
    print(f"Topic: {topic}\n")

    initial_state = {
        "query": topic,
        "search_queries": [],
        "retrieved_docs": [],
        "draft": "",
        "fact_check_results": [],
        "critique": "",
        "verification_status": "PENDING",
        "iteration_count": 0
    }

    final_state = agent_app.invoke(initial_state)

    print("\n" + "=" * 50)
    print("FINAL VERIFIED REPORT")
    print("=" * 50 + "\n")
    print(final_state["draft"])
    print("\n" + "-" * 50)
    print(f"Iterations: {final_state['iteration_count']}")
    print(f"Verification Status: {final_state['verification_status']}")
    print("-" * 50)

if __name__ == "__main__":
    main()