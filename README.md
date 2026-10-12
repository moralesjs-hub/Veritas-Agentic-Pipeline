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

# Navigate to project root and activate virtual environment
.venv-1\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server on port 8000
uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# In a separate terminal
cd web
npm install
npm run dev

---

### Commit the Changes

1. Click the **Preview** tab next to **Edit** (above line 1) to verify that the Mermaid diagram flowchart renders with no syntax warnings.
2. Click the green **Commit changes...** button in the top right.
3. In the modal:
   * **Commit message:** `docs: fix Mermaid syntax and finalize project architecture documentation`
   * Select **Commit directly to the main branch**.
4. Click **Commit changes**.
