# Veritas: Autonomous Multi-Agent Verification Pipeline

An autonomous cyclical multi-agent research and factual verification pipeline built with **LangGraph**, **Gemini 3.8 Flash**, and **Pydantic v2**.

## Architecture Overview

```mermaid
flowchart TD
    Q[User Query] --> Planner[Planner Node]
    Planner --> Research[Research Node<br/><i>DuckDuckGo Retrieval</i>]
    Research --> Synth[Synthesizer Node]
    Synth --> Verifier[Verifier Node]

    Verifier -->|Verdict: REVISE<br/>Iter &lt; 2| Planner
    Verifier -->|Verdict: APPROVED or Max Iterations| Report[Final Markdown Report]

    style Planner fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#fff
    style Research fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#fff
    style Synth fill:#1f2937,stroke:#3b82f6,stroke-width:2px,color:#fff
    style Verifier fill:#1f2937,stroke:#e11d48,stroke-width:2px,color:#fff
    style Report fill:#1f2937,stroke:#10b981,stroke-width:2px,color:#fff
```
[Final Markdown Report]


## Key Technical Characteristics
* **State Machine Graph:** Orchestrated via `langgraph.graph.StateGraph` with conditional routing edges.
* **Deterministic Structured Outputs:** Uses Pydantic v2 schemas (`VerificationVerdict`, `FactCheckResult`) for claim-by-claim verification matrices.
* **Self-Correcting Verification:** Detects ungrounded claims and triggers targeted re-queries prior to final output generation.
* **Resilient API Architecture:** Employs strict network timeouts across model calls and web search retrieval to prevent deadlocks.

## Setup & Execution

### 1. Environment Setup
```powershell
conda activate agentic_ai
pip install -r requirements.txt
