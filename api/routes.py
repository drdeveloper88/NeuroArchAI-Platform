"""NeoArchAI - FastAPI Routes

Endpoints:
  POST /api/design                   – Start new design (async)
  GET  /api/design/{id}              – Poll status + results
  GET  /api/design/{id}/stream       – SSE progress stream
  GET  /api/files/{id}/{filename}    – Serve output files
  GET  /api/designs                  – List recent designs
  DELETE /api/design/{id}            – Delete design
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse

from config import OUTPUT_DIR
from models.schemas import (
    DesignInitResponse, DesignRequest, DesignResult, DesignStatus
)
from graph.design_graph import design_graph

logger = logging.getLogger(__name__)
router = APIRouter()

# ── In-memory design registry ──────────────────────────────────────────────────
# { design_id: DesignResult dict }
_designs: Dict[str, dict] = {}


# ── Background task: run the LangGraph pipeline ──────────────────────────────

async def _run_design_pipeline(design_id: str, requirements: dict) -> None:
    """Execute the LangGraph design pipeline and update the registry."""
    _designs[design_id]["status"]       = DesignStatus.ANALYZING
    _designs[design_id]["current_stage"]= "analyzing"
    _designs[design_id]["progress"]     = 5

    initial_state = {
        "design_id":    design_id,
        "requirements": requirements,
        "basic_design": {},
        "floor_plans":  [],
        "model_3d":     {},
        "report_url":   "",
        "current_stage":"start",
        "progress":     0,
        "errors":       [],
        "messages":     [],
    }

    try:
        # Stream events from LangGraph so we can update progress in real-time
        async for event in design_graph.astream_events(initial_state, version="v2"):
            kind  = event.get("event", "")
            name  = event.get("name", "")
            data  = event.get("data", {})

            if kind == "on_chain_start":
                stage_map = {
                    "analyze_requirements":  (DesignStatus.ANALYZING,  10),
                    "generate_basic_design": (DesignStatus.DESIGNING,  30),
                    "generate_2d_layout":    (DesignStatus.LAYOUT_2D,  55),
                    "generate_3d_model":     (DesignStatus.MODEL_3D,   75),
                    "compile_report":        (DesignStatus.REPORTING,  88),
                }
                if name in stage_map:
                    status, prog = stage_map[name]
                    _designs[design_id]["status"]        = status
                    _designs[design_id]["current_stage"] = name
                    _designs[design_id]["progress"]      = prog

            elif kind == "on_chain_end" and name == "LangGraph":
                # Final state available
                output = data.get("output", {})
                if output:
                    _update_registry_from_state(design_id, output)

    except Exception as exc:
        logger.exception("Pipeline failed for design %s", design_id)
        _designs[design_id]["status"]       = DesignStatus.ERROR
        _designs[design_id]["current_stage"]= "error"
        _designs[design_id]["error"]        = str(exc)
        return

    # Final update
    if _designs[design_id]["status"] != DesignStatus.ERROR:
        _designs[design_id]["status"]       = DesignStatus.COMPLETE
        _designs[design_id]["current_stage"]= "complete"
        _designs[design_id]["progress"]     = 100
        _designs[design_id]["completed_at"] = datetime.utcnow().isoformat()


def _update_registry_from_state(design_id: str, state: dict) -> None:
    """Merge LangGraph final state into the registry."""
    reg = _designs[design_id]
    if state.get("basic_design"):
        reg["basic_design"] = state["basic_design"]
    if state.get("floor_plans"):
        reg["floor_plans"] = state["floor_plans"]
    if state.get("model_3d"):
        reg["model_3d"] = state["model_3d"]
    if state.get("report_url"):
        reg["report_url"] = state["report_url"]
    reg["progress"] = state.get("progress", reg.get("progress", 0))


# ── Route: Start new design ───────────────────────────────────────────────────

@router.post("/design", response_model=DesignInitResponse, status_code=202,
             summary="Start a new house design",
             tags=["Design"])
async def create_design(
    request: DesignRequest,
    background_tasks: BackgroundTasks,
) -> DesignInitResponse:
    """
    Submit house requirements and receive a design_id.
    The pipeline runs asynchronously; poll GET /design/{id} for results.
    """
    design_id = str(uuid.uuid4())

    _designs[design_id] = {
        "design_id":     design_id,
        "status":        DesignStatus.PENDING,
        "current_stage": "pending",
        "progress":      0,
        "requirements":  request.requirements.model_dump(),
        "basic_design":  None,
        "floor_plans":   [],
        "model_3d":      None,
        "report_url":    None,
        "error":         None,
        "created_at":    datetime.utcnow().isoformat(),
        "completed_at":  None,
    }

    background_tasks.add_task(
        _run_design_pipeline, design_id, request.requirements.model_dump()
    )

    return DesignInitResponse(
        design_id     = design_id,
        message       = "Design pipeline started. Poll status_url for progress.",
        status_url    = f"/api/design/{design_id}",
        websocket_url = f"/api/design/{design_id}/stream",
    )


# ── Route: Get design status / result ─────────────────────────────────────────

@router.get("/design/{design_id}", response_model=DesignResult,
            summary="Get design status and results",
            tags=["Design"])
async def get_design(design_id: str) -> DesignResult:
    """Poll this endpoint to track progress and retrieve results."""
    if design_id not in _designs:
        raise HTTPException(status_code=404, detail="Design not found")
    data = _designs[design_id]
    # Map internal field names to schema field names
    return DesignResult(
        design_id    = data["design_id"],
        status       = data.get("status", DesignStatus.PENDING),
        stage        = data.get("current_stage", ""),
        progress     = data.get("progress", 0),
        requirements = data.get("requirements"),
        basic_design = data.get("basic_design"),
        floor_plans  = data.get("floor_plans") or [],
        model_3d     = data.get("model_3d"),
        report_url   = data.get("report_url"),
        error        = data.get("error"),
        created_at   = data.get("created_at", ""),
        completed_at = data.get("completed_at"),
    )


# ── Route: SSE Progress Stream ────────────────────────────────────────────────

@router.get("/design/{design_id}/stream",
            summary="Server-Sent Events progress stream",
            tags=["Design"])
async def stream_design_progress(design_id: str) -> StreamingResponse:
    """
    Opens an SSE stream that emits design progress events until completion.
    """
    if design_id not in _designs:
        raise HTTPException(status_code=404, detail="Design not found")

    async def _event_generator():
        last_progress = -1
        while True:
            design = _designs.get(design_id)
            if not design:
                break

            progress = design.get("progress", 0)
            status   = design.get("status", "pending")
            stage    = design.get("current_stage", "")

            if progress != last_progress:
                payload = json.dumps({
                    "design_id": design_id,
                    "status":    status,
                    "stage":     stage,
                    "progress":  progress,
                })
                yield f"data: {payload}\n\n"
                last_progress = progress

            if status in (DesignStatus.COMPLETE, DesignStatus.ERROR):
                # Send final snapshot
                final = json.dumps({"event": "complete", **design}, default=str)
                yield f"data: {final}\n\n"
                break

            await asyncio.sleep(1.0)

    return StreamingResponse(
        _event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":               "no-cache",
            "X-Accel-Buffering":           "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── Route: List all designs ───────────────────────────────────────────────────

@router.get("/designs",
            summary="List all designs",
            tags=["Design"])
async def list_designs() -> list:
    return [
        {
            "design_id":     d["design_id"],
            "status":        d["status"],
            "progress":      d["progress"],
            "style":         d.get("requirements", {}).get("style", ""),
            "area":          d.get("requirements", {}).get("total_area_sqft", 0),
            "created_at":    d.get("created_at"),
            "completed_at":  d.get("completed_at"),
        }
        for d in _designs.values()
    ]


# ── Route: Delete design ──────────────────────────────────────────────────────

@router.delete("/design/{design_id}",
               summary="Delete a design and its output files",
               tags=["Design"])
async def delete_design(design_id: str) -> dict:
    if design_id not in _designs:
        raise HTTPException(status_code=404, detail="Design not found")
    _designs.pop(design_id)

    import shutil
    design_dir = OUTPUT_DIR / design_id
    if design_dir.exists():
        shutil.rmtree(design_dir)

    return {"message": f"Design {design_id} deleted."}


# ── Route: Serve output files ─────────────────────────────────────────────────

@router.get("/files/{design_id}/{filename}",
            summary="Download a generated file",
            tags=["Files"])
async def get_file(design_id: str, filename: str) -> FileResponse:
    """Serve generated floor plans, 3D model HTML, report, etc."""
    # Security: prevent path traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = OUTPUT_DIR / design_id / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")

    # Determine media type
    suffix = file_path.suffix.lower()
    media_map = {
        ".png":  "image/png",
        ".svg":  "image/svg+xml",
        ".html": "text/html",
        ".json": "application/json",
        ".pdf":  "application/pdf",
    }
    media_type = media_map.get(suffix, "application/octet-stream")
    return FileResponse(str(file_path), media_type=media_type)


# ── Route: Health check ───────────────────────────────────────────────────────

@router.get("/health", tags=["System"])
async def health() -> dict:
    from config import LLM_PROVIDER, LLM_MODEL, GROQ_API_KEY
    return {
        "status":       "healthy",
        "llm_provider": LLM_PROVIDER,
        "llm_model":    LLM_MODEL,
        "llm_ready":    bool(GROQ_API_KEY) or LLM_PROVIDER == "ollama",
        "designs_in_memory": len(_designs),
    }
