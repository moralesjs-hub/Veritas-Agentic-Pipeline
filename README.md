# Veritas: Autonomous Multi-Agent Verification Pipeline

An enterprise agentic research and factual verification platform featuring cyclical multi-agent workflows built with **LangGraph**, **Gemini 2.5 Flash**, **FastAPI**, and a **Next.js 16** real-time control plane.

---

## Architecture Overview

```mermaid
flowchart TD
    UI[Next.js 16 Control Plane] -->|POST /api/runs| API[FastAPI Gateway]
    API -->|SSE Stream /api/runs/:id/stream| UI
    
    subgraph Pipeline [LangGraph State Machine]
        R[01 // RESEARCHER<br/>Web Grounding & Literature Queries] --> D[02 // DRAFTER<br/>Synthesis Drafting]
        D --> HITL{Human Review Gate}
        
        HITL -->|Action: REJECT / Critique| D
        HITL -->|Action: APPROVE| V[03 // VERIFIER<br/>Factuality Check & Multi-Pass Scoring]
    end
    
    API --> R
    V --> DB[(SQLite / PostgreSQL + Node Traces)]
    V --> UI
