"""NeoArchAI - LangGraph Node Functions

Each node receives the full DesignState, does its work, and returns
a partial dict with only the fields it changed.
"""
from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path
from typing import Any

from config import get_llm, OUTPUT_DIR
from graph.state import DesignState
from models.schemas import (
    BasicDesign, MaterialSpec, CostEstimate, RoomSpec,
    FloorPlanOutput, Model3DOutput, HouseRequirements
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

async def _call_llm(prompt: str, fallback: str) -> str:
    """Call the LLM async, return fallback string if unavailable."""
    llm = get_llm()
    if llm is None:
        return fallback
    try:
        from langchain_core.messages import HumanMessage
        response = await llm.ainvoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as exc:
        logger.warning("LLM call failed: %s", exc)
        return fallback


def _design_dir(design_id: str) -> Path:
    d = OUTPUT_DIR / design_id
    d.mkdir(parents=True, exist_ok=True)
    return d


# ─────────────────────────────────────────────────────────────────────────────
# Node 1: Analyze Requirements
# ─────────────────────────────────────────────────────────────────────────────

async def analyze_requirements_node(state: DesignState) -> dict:
    """Validate, enrich, and understand house requirements via LLM."""
    req = state["requirements"]
    style = req.get("style", "modern")
    bedrooms = req.get("bedrooms", 3)
    area = req.get("total_area_sqft", 2000)
    floors = req.get("floors", 1)
    climate = req.get("climate", "temperate")

    prompt = f"""You are a senior architect. Analyze these house design requirements and provide concise insights:

Style: {style}
Total Area: {area} sq ft across {floors} floor(s)
Bedrooms: {bedrooms}, Bathrooms: {req.get('bathrooms', 2)}
Garage: {req.get('has_garage', False)}, Garden: {req.get('has_garden', True)}
Budget: {req.get('budget_level', 'standard')}, Climate: {climate}
Special features: {req.get('special_features', [])}

Provide:
1. Key design priorities for this style and climate
2. Recommended spatial allocation percentages
3. Important structural or code considerations
4. One unique design suggestion that elevates this project

Keep response under 300 words, be specific and actionable."""

    fallback = (
        f"Design analysis: {style.title()} house with {bedrooms} bedrooms, "
        f"{area} sq ft over {floors} floor(s). "
        f"Climate-responsive design for {climate} conditions."
    )

    analysis = await _call_llm(prompt, fallback)

    return {
        "messages": [{"role": "analyst", "content": analysis, "stage": "requirements"}],
        "current_stage": "requirements_analyzed",
        "progress": 12,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 2: Generate Basic Design (uses CrewAI crew)
# ─────────────────────────────────────────────────────────────────────────────

async def generate_basic_design_node(state: DesignState) -> dict:
    """
    Use CrewAI design crew to produce full architectural specifications.
    Falls back to algorithmic generation if LLM is unavailable.
    """
    req = state["requirements"]
    design_id = state["design_id"]

    # Run CrewAI crew in a thread (CrewAI is synchronous)
    try:
        from agents.design_crew import run_design_crew
        basic_design_dict = await asyncio.get_event_loop().run_in_executor(
            None, run_design_crew, req
        )
    except Exception as exc:
        logger.warning("CrewAI crew failed (%s), using algorithmic fallback.", exc)
        from agents.design_crew import algorithmic_basic_design
        basic_design_dict = algorithmic_basic_design(req)

    # Save to file
    design_path = _design_dir(design_id) / "basic_design.json"
    design_path.write_text(json.dumps(basic_design_dict, indent=2))

    return {
        "basic_design": basic_design_dict,
        "messages": [{"role": "architect", "content": "Basic design complete.", "stage": "basic_design"}],
        "current_stage": "basic_design_complete",
        "progress": 35,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 3: Generate 2D Layout
# ─────────────────────────────────────────────────────────────────────────────

async def generate_2d_layout_node(state: DesignState) -> dict:
    """Render 2D architectural floor plans per floor."""
    design_id = state["design_id"]
    basic_design = state["basic_design"]
    req = state["requirements"]
    design_dir = _design_dir(design_id)

    from tools.floor_plan_2d import render_all_floors
    floor_plan_outputs = await asyncio.get_event_loop().run_in_executor(
        None, render_all_floors, basic_design, design_dir, design_id
    )

    return {
        "floor_plans": floor_plan_outputs,
        "messages": [{"role": "drafter", "content": f"{len(floor_plan_outputs)} floor plan(s) rendered.", "stage": "2d_layout"}],
        "current_stage": "2d_layout_complete",
        "progress": 62,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 4: Generate 3D Model
# ─────────────────────────────────────────────────────────────────────────────

async def generate_3d_model_node(state: DesignState) -> dict:
    """Build interactive 3D Plotly visualization of the house."""
    design_id = state["design_id"]
    basic_design = state["basic_design"]
    design_dir = _design_dir(design_id)

    from tools.model_3d import build_3d_model
    model_output = await asyncio.get_event_loop().run_in_executor(
        None, build_3d_model, basic_design, design_dir, design_id
    )

    return {
        "model_3d": model_output,
        "messages": [{"role": "visualizer", "content": "3D model generated.", "stage": "3d_model"}],
        "current_stage": "3d_model_complete",
        "progress": 82,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Node 5: Compile Report
# ─────────────────────────────────────────────────────────────────────────────

async def compile_report_node(state: DesignState) -> dict:
    """Generate a comprehensive PDF + HTML design report."""
    design_id = state["design_id"]
    design_dir = _design_dir(design_id)
    req = state["requirements"]
    basic_design = state["basic_design"]
    floor_plans = state.get("floor_plans", [])
    model_3d = state.get("model_3d", {})

    # AI-generated executive summary
    prompt = f"""As a senior architect, write a professional 2-paragraph executive summary 
for this house design project:

Title: {basic_design.get('title', 'Custom Residence')}
Style: {req.get('style', 'modern').title()}
Area: {basic_design.get('total_area_sqft', 2000)} sq ft, {req.get('floors', 1)} floor(s)
Bedrooms/Bathrooms: {req.get('bedrooms', 3)}/{req.get('bathrooms', 2)}
Key features: {basic_design.get('energy_features', [])}

Write professionally, highlight design philosophy and value for the homeowner."""

    fallback_summary = (
        f"This {req.get('style','modern').title()} residence offers a thoughtfully designed "
        f"{basic_design.get('total_area_sqft',2000):.0f} sq ft living space across "
        f"{req.get('floors',1)} floor(s), featuring {req.get('bedrooms',3)} bedrooms and "
        f"{req.get('bathrooms',2)} bathrooms. The design balances functionality and aesthetics "
        f"to create a comfortable, efficient home tailored to modern living standards."
    )

    summary = await _call_llm(prompt, fallback_summary)

    from tools.report_gen import generate_report
    report_url = await asyncio.get_event_loop().run_in_executor(
        None, generate_report, {
            "design_id": design_id,
            "requirements": req,
            "basic_design": basic_design,
            "floor_plans": floor_plans,
            "model_3d": model_3d,
            "summary": summary,
        }, design_dir
    )

    return {
        "report_url": report_url,
        "messages": [{"role": "reporter", "content": summary, "stage": "report"}],
        "current_stage": "complete",
        "progress": 100,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Error Handler Node
# ─────────────────────────────────────────────────────────────────────────────

async def error_handler_node(state: DesignState) -> dict:
    """Catches and records pipeline errors."""
    errors = state.get("errors", [])
    logger.error("Design pipeline error: %s", errors)
    return {
        "current_stage": "error",
        "progress": state.get("progress", 0),
    }
