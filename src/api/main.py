import os
import json
import asyncio
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select

from src.db import init_db, AsyncSessionLocal, PipelineRun, NodeTrace
from src.services.pipeline_runner import execute_pipeline, resume_pipeline_execution

app = FastAPI(title="Veritas Agentic Control Plane")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await init_db()


class RunCreateRequest(BaseModel):
    topic: str


class ReviewPayload(BaseModel):
    action: str
    critique: Optional[str] = "Insufficient technical depth; revise paradigms and empirical trade-offs."


@app.post("/api/runs", status_code=202)
async def create_run(request: RunCreateRequest, background_tasks: BackgroundTasks):
    async with AsyncSessionLocal() as session:
        new_run = PipelineRun(
            topic=request.topic,
            status="PENDING",
            final_output="",
            verifier_score=None,
            error_message="",
        )
        session.add(new_run)
        await session.commit()
        await session.refresh(new_run)
        run_id = str(new_run.id)

    background_tasks.add_task(execute_pipeline, run_id, request.topic)
    return {"id": run_id, "status": "PENDING"}


@app.get("/api/runs/{run_id}")
async def get_run_status(run_id: str):
    async with AsyncSessionLocal() as session:
        stmt = select(PipelineRun).where(PipelineRun.id == run_id)
        run = (await session.execute(stmt)).scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        return {
            "id": str(run.id),
            "topic": run.topic,
            "status": run.status,
            "verifier_score": run.verifier_score,
            "final_output": run.final_output,
            "error_message": run.error_message,
        }


@app.post("/api/runs/{run_id}/review")
async def review_run(run_id: str, payload: ReviewPayload):
    async with AsyncSessionLocal() as session:
        stmt = select(PipelineRun).where(PipelineRun.id == run_id)
        run = (await session.execute(stmt)).scalar_one_or_none()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")

        run.status = "RUNNING"
        await session.commit()

        if payload.action == "REJECT":
            asyncio.create_task(
                resume_pipeline_execution(run_id, critique=payload.critique, status_verdict="FAIL")
            )
            return {"status": "REVISION_TRIGGERED", "critique": payload.critique}

        asyncio.create_task(
            resume_pipeline_execution(run_id, critique=None, status_verdict="PASS")
        )
        return {"status": "APPROVED"}


@app.get("/api/runs/{run_id}/stream")
async def stream_run(run_id: str):
    async def event_generator():
        last_trace_count = 0
        while True:
            async with AsyncSessionLocal() as session:
                run_stmt = select(PipelineRun).where(PipelineRun.id == run_id)
                run = (await session.execute(run_stmt)).scalar_one_or_none()
                if not run:
                    break

                trace_stmt = select(NodeTrace).where(NodeTrace.run_id == run_id).order_by(NodeTrace.created_at.asc())
                traces = (await session.execute(trace_stmt)).scalars().all()

                if len(traces) > last_trace_count:
                    for t in traces[last_trace_count:]:
                        payload_data = getattr(t, "payload", None) or getattr(t, "state_snapshot", {})
                        yield f"event: node_trace\ndata: {json.dumps({'node_name': t.node_name, 'latency_ms': t.latency_ms, 'payload': payload_data})}\n\n"
                    last_trace_count = len(traces)

                yield f"event: status\ndata: {json.dumps({'status': run.status, 'final_output': run.final_output, 'verifier_score': run.verifier_score})}\n\n"

                if run.status in ["COMPLETED", "FAILED", "WAITING_FOR_REVIEW"]:
                    yield f"event: complete\ndata: {json.dumps({'status': run.status, 'final_output': run.final_output, 'verifier_score': run.verifier_score})}\n\n"
                    if run.status != "WAITING_FOR_REVIEW":
                        break

            await asyncio.sleep(1.0)

    return StreamingResponse(event_generator(), media_type="text/event-stream")