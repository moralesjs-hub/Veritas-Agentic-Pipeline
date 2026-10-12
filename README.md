# Veritas: Autonomous Multi-Agent Verification Pipeline

An enterprise agentic research and factual verification platform featuring cyclical multi-agent workflows built with **LangGraph**, **Gemini 2.5 Flash**, **FastAPI**, and a **Next.js 16** real-time control plane.

---

## Architecture Overview

```mermaid
flowchart TD
    UI[Next.js 16 Control Plane] -->|POST /api/runs| API[FastAPI Gateway]
    API -->|SSE Stream /api/runs/:id/stream| UI
    
    subgraph Execution Pipeline [LangGraph State Machine]
        R[01 // RESEARCHER<br/><i>Web Grounding & Literature Queries</i>] --> D[02 // DRAFTER<br/><i>Synthesis Drafting</i>]
        D --> HITL{Human Review Gate}
        
        HITL -->|Action: REJECT / Critique| D
        HITL -->|Action: APPROVE| V[03 // VERIFIER<br/><i>Factuality Check & Multi-Pass Scoring</i>]
    end
    
    API --> Execution Pipeline
    V --> DB[(SQLite / PostgreSQL + Node Traces)]
    V --> UI
Key Technical Characteristics   
Cyclical State Machine: Orchestrated via langgraph.graph.StateGraph with human-in-the-loop (HITL) review gates and conditional loopback routing for iterative draft revision.   

Real-Time Telemetry Feed: Server-Sent Events (SSE) stream node execution latencies, event states, and telemetry snapshots directly into the dashboard.   

Deterministic Verification Matrix: Pydantic-grounded verifier scoring validating factual coverage, topic relevance, and structural cohesion.   

Resilient API Architecture: Strict async request boundaries, non-blocking background workers, and rapid synthesis fallbacks eliminate network stalls.   

Project Structure   
Plaintext
Veritas-Agentic-Pipeline/
├── src/
│   ├── api/
│   │   └── main.py              # FastAPI gateway & SSE streaming routes
│   ├── services/
│   │   └── pipeline_runner.py   # State machine execution & HITL loop management
│   ├── db.py                    # SQLAlchemy async models (PipelineRun, NodeTrace)
│   ├── graph.py                 # LangGraph node definitions & fallback synthesis
│   └── main.py                  # CLI entrypoint
├── web/                         # Next.js 16 (Turbopack) Control Plane
│   └── src/
│       ├── app/
│       │   ├── page.tsx         # Dashboard UI, real-time telemetry, & markdown viewer
│       │   └── layout.tsx       # Root layout & application metadata
│       └── components/          # Dashboard telemetry & graph components
├── requirements.txt
└── README.md
Setup & Execution   
1. Backend Gateway (FastAPI)   
PowerShell
# Navigate to project root and activate virtual environment
.venv-1\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server on port 8000
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
Backend Swagger documentation is accessible at http://127.0.0.1:8000/docs.   

2. Frontend Control Plane (Next.js)   
PowerShell
# In a separate terminal
cd web
npm install
npm run dev
Navigate to http://localhost:3000 to execute research runs, inspect real-time node telemetry, review drafts, and export Markdown synthesis briefs.   


---

4. Click the green **Commit changes...** button again.
5. In the commit modal, use:

* **Commit message:**
  ```text
  docs: update README with Next.js control plane, SSE telemetry, and LangGraph HITL architecture
Extended description:

Plaintext
Documented system architecture diagram, key technical capabilities, project folder tree, and local development runbooks for FastAPI backend and Next.js control plane.
