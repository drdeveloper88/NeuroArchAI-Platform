"""NeoArchAI - LangGraph State Definition"""
from __future__ import annotations
from typing import TypedDict, Annotated, Optional, List
import operator


class DesignState(TypedDict):
    """
    Immutable state passed through the LangGraph pipeline.
    Each node returns a partial dict; LangGraph merges it.
    """
    # Identity
    design_id: str

    # Input
    requirements: dict          # HouseRequirements as dict

    # Stage outputs (populated progressively)
    basic_design: dict          # BasicDesign as dict
    floor_plans: list           # List[FloorPlanOutput as dict]
    model_3d: dict              # Model3DOutput as dict
    report_url: str

    # Control
    current_stage: str
    progress: int               # 0-100
    errors: Annotated[list, operator.add]   # accumulates errors

    # LLM messages trace
    messages: Annotated[list, operator.add]
