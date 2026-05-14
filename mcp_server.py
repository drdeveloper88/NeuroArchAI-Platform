"""NeoArchAI - FastMCP Server

Exposes the house architecture design system as MCP tools
that can be consumed by AI assistants (Claude, Copilot, etc.)

Run standalone:  python mcp_server.py
Or alongside FastAPI:  the main.py mounts it at /mcp
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any, Dict, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)

mcp = FastMCP(
    name="NeoArchAI",
    instructions=(
        "NeoArchAI generates complete house architecture designs. "
        "Use generate_house_design to start a design, then poll "
        "get_design_status until status is 'complete'. "
        "Results include room schedules, 2D floor plan URLs, "
        "interactive 3D model URL, and a full HTML/PDF report."
    ),
)

# Shared in-memory state (synced with api.routes when embedded)
_mcp_designs: Dict[str, Any] = {}


@mcp.tool(
    description=(
        "Generate a complete house architecture design including room layout, "
        "2D floor plans, interactive 3D model, and cost estimate. "
        "Returns a design_id – use get_design_status to retrieve results."
    )
)
async def generate_house_design(
    style: str = "modern",
    total_area_sqft: float = 2000.0,
    floors: int = 1,
    bedrooms: int = 3,
    bathrooms: int = 2,
    has_garage: bool = False,
    has_garden: bool = True,
    budget_level: str = "standard",
    climate: str = "temperate",
    roof_type: str = "gable",
    special_features: Optional[list] = None,
    custom_notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Start an asynchronous house design job.
    """
    from models.schemas import HouseRequirements
    from graph.design_graph import design_graph
    from config import OUTPUT_DIR
    from pathlib import Path

    requirements = HouseRequirements(
        style=style,
        total_area_sqft=total_area_sqft,
        floors=floors,
        bedrooms=bedrooms,
        bathrooms=bathrooms,
        has_garage=has_garage,
        has_garden=has_garden,
        budget_level=budget_level,
        climate=climate,
        roof_type=roof_type,
        special_features=special_features or [],
        custom_notes=custom_notes,
    )

    design_id = str(uuid.uuid4())
    req_dict  = requirements.model_dump()

    _mcp_designs[design_id] = {
        "design_id":     design_id,
        "status":        "pending",
        "current_stage": "pending",
        "progress":      0,
        "requirements":  req_dict,
        "basic_design":  None,
        "floor_plans":   [],
        "model_3d":      None,
        "report_url":    None,
        "error":         None,
    }

    async def _run():
        from api.routes import _run_design_pipeline, _designs
        _designs[design_id] = _mcp_designs[design_id]
        await _run_design_pipeline(design_id, req_dict)
        _mcp_designs[design_id].update(_designs[design_id])

    # Fire and forget
    asyncio.create_task(_run())

    return {
        "design_id":  design_id,
        "status":     "started",
        "message":    f"Design pipeline started. Poll get_design_status('{design_id}') for results.",
        "poll_hint":  "Call get_design_status every 15 seconds until status=='complete'.",
    }


@mcp.tool(
    description=(
        "Poll the status of a house design job. "
        "Returns current stage, progress percentage (0-100), "
        "and results when status is 'complete'."
    )
)
async def get_design_status(design_id: str) -> Dict[str, Any]:
    """
    Get the current status and results of a design job.
    """
    # Try local MCP store first, then shared API store
    design = _mcp_designs.get(design_id)
    if not design:
        try:
            from api.routes import _designs
            design = _designs.get(design_id)
        except ImportError:
            pass

    if not design:
        return {"error": f"Design '{design_id}' not found."}

    response: Dict[str, Any] = {
        "design_id":     design["design_id"],
        "status":        design.get("status", "unknown"),
        "stage":         design.get("current_stage", ""),
        "progress":      design.get("progress", 0),
    }

    if design.get("status") == "complete":
        bd = design.get("basic_design") or {}
        response["results"] = {
            "title":        bd.get("title", ""),
            "total_area":   bd.get("total_area_sqft", 0),
            "floors":       bd.get("floors", 0),
            "room_count":   len(bd.get("rooms", [])),
            "cost_estimate": bd.get("cost_estimate", {}),
            "floor_plan_urls": [
                fp.get("image_url") for fp in (design.get("floor_plans") or [])
            ],
            "model_3d_url": (design.get("model_3d") or {}).get("html_url", ""),
            "report_url":   design.get("report_url", ""),
        }

    if design.get("error"):
        response["error"] = design["error"]

    return response


@mcp.tool(
    description="List all available house design styles supported by NeoArchAI."
)
async def list_design_styles() -> Dict[str, Any]:
    """Return available design styles with brief descriptions."""
    return {
        "styles": {
            "modern":        "Clean lines, open plan, large windows, minimalist palette",
            "contemporary":  "Current trends, flexible spaces, sustainable materials",
            "traditional":   "Symmetrical facade, detailed moldings, classic proportions",
            "mediterranean": "Stucco exterior, terracotta roof, arched openings, courtyards",
            "craftsman":     "Natural materials, exposed beams, covered porch, built-ins",
            "colonial":      "Formal symmetry, brick exterior, shuttered windows, columns",
            "ranch":         "Single-story, long horizontal form, attached garage",
            "victorian":     "Ornate detailing, asymmetric facade, wraparound porch",
            "minimalist":    "Stripped-back design, neutral palette, hidden storage",
        },
        "budget_levels":  ["basic", "standard", "luxury"],
        "roof_types":     ["gable", "hip", "flat", "shed", "mansard"],
        "climate_zones":  ["tropical", "temperate", "cold", "arid", "mediterranean"],
    }


@mcp.tool(
    description="Calculate estimated construction cost for a house design."
)
async def estimate_construction_cost(
    total_area_sqft: float,
    budget_level: str = "standard",
    climate: str = "temperate",
    floors: int = 1,
) -> Dict[str, Any]:
    """Provide a quick cost estimate without running the full design pipeline."""
    from agents.design_crew import COST_PER_SQFT
    key  = (budget_level, climate)
    cpf  = COST_PER_SQFT.get(key, COST_PER_SQFT.get(("standard", "temperate"), (160, 235)))
    low  = round(total_area_sqft * cpf[0])
    high = round(total_area_sqft * cpf[1])
    return {
        "area_sqft":     total_area_sqft,
        "budget_level":  budget_level,
        "climate":       climate,
        "cost_low_usd":  low,
        "cost_high_usd": high,
        "cost_per_sqft": f"${cpf[0]}–${cpf[1]}",
        "note":          f"Estimate for {budget_level} construction in {climate} climate zone.",
    }


if __name__ == "__main__":
    # Run as standalone MCP server (stdio transport)
    mcp.run()
