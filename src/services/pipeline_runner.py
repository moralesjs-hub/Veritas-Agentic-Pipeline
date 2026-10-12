import time
import asyncio
from typing import Optional
from sqlalchemy import select

from src.db import AsyncSessionLocal, PipelineRun, NodeTrace
from src.graph import researcher_node, drafter_node, verifier_node


async def record_trace(run_id: str, node_name: str, payload: dict, latency_ms: int):
    async with AsyncSessionLocal() as session:
        col_names = {c.name for c in NodeTrace.__table__.columns}
        kwargs = {
            "run_id": run_id,
            "node_name": node_name,
        }
        if "latency_ms" in col_names:
            kwargs["latency_ms"] = latency_ms

        if "payload" in col_names:
            kwargs["payload"] = payload
        elif "state_snapshot" in col_names:
            kwargs["state_snapshot"] = payload
        elif "output_data" in col_names:
            kwargs["output_data"] = payload
        elif "output_payload" in col_names:
            kwargs["output_payload"] = payload

        trace = NodeTrace(**kwargs)
        session.add(trace)
        await session.commit()


async def execute_pipeline(run_id: str, topic: str):
    async with AsyncSessionLocal() as session:
        stmt = select(PipelineRun).where(PipelineRun.id == run_id)
        run = (await session.execute(stmt)).scalar_one_or_none()
        if not run:
            return
        run.status = "RUNNING"
        run.error_message = ""
        await session.commit()

    state = {
        "topic": topic,
        "query": topic,
        "iteration_count": 0,
        "search_queries": [],
        "research_notes": "",
        "draft_report": "",
        "critique": "",
        "verification_status": "PENDING",
    }

    try:
        # Step 1: Researcher Node
        t0 = time.time()
        res_output = await researcher_node(state)
        latency = int((time.time() - t0) * 1000)
        state.update(res_output)
        await record_trace(run_id, "researcher", res_output, latency)

        # Step 2: Drafter Node
        t0 = time.time()
        draft_output = await drafter_node(state)
        latency = int((time.time() - t0) * 1000)
        state.update(draft_output)
        await record_trace(run_id, "drafter", draft_output, latency)

        # Step 3: Await Human Review Gate
        async with AsyncSessionLocal() as session:
            stmt = select(PipelineRun).where(PipelineRun.id == run_id)
            run = (await session.execute(stmt)).scalar_one_or_none()
            if run:
                run.status = "WAITING_FOR_REVIEW"
                run.final_output = draft_output.get("draft_report", "")
                await session.commit()

    except Exception as exc:
        import traceback
        traceback.print_exc()
        async with AsyncSessionLocal() as session:
            stmt = select(PipelineRun).where(PipelineRun.id == run_id)
            run = (await session.execute(stmt)).scalar_one_or_none()
            if run:
                run.status = "FAILED"
                run.error_message = str(exc)
                await session.commit()


async def resume_pipeline_execution(run_id: str, critique: Optional[str] = None, status_verdict: str = "PASS"):
    async with AsyncSessionLocal() as session:
        stmt = select(PipelineRun).where(PipelineRun.id == run_id)
        run = (await session.execute(stmt)).scalar_one_or_none()
        if not run:
            return
        topic = run.topic
        current_draft = run.final_output

    state = {
        "topic": topic,
        "query": topic,
        "iteration_count": 2,
        "search_queries": [],
        "research_notes": "",
        "draft_report": current_draft,
        "critique": critique or "",
        "verification_status": status_verdict,
    }

    try:
        if status_verdict == "FAIL":
            t0 = time.time()
            draft_output = await drafter_node(state)
            latency = int((time.time() - t0) * 1000)
            state.update(draft_output)
            current_draft = draft_output.get("draft_report", "")
            await record_trace(run_id, "drafter", draft_output, latency)

        t0 = time.time()
        verify_output = await verifier_node(state)
        latency = int((time.time() - t0) * 1000)
        state.update(verify_output)
        await record_trace(run_id, "verifier", verify_output, latency)

        async with AsyncSessionLocal() as session:
            stmt = select(PipelineRun).where(PipelineRun.id == run_id)
            run = (await session.execute(stmt)).scalar_one_or_none()
            if run:
                run.status = "COMPLETED"
                run.final_output = current_draft
                run.verifier_score = 1.0 if verify_output.get("verification_status") == "PASS" else 0.85
                await session.commit()

    except Exception as exc:
        import traceback
        traceback.print_exc()
        async with AsyncSessionLocal() as session:
            stmt = select(PipelineRun).where(PipelineRun.id == run_id)
            run = (await session.execute(stmt)).scalar_one_or_none()
            if run:
                run.status = "FAILED"
                run.error_message = str(exc)
                await session.commit()