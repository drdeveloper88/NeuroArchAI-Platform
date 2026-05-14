"""NeoArchAI - Pydantic Models & Schemas"""
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ─── Enums ─────────────────────────────────────────────────────────────────────

class HouseStyle(str, Enum):
    MODERN = "modern"
    TRADITIONAL = "traditional"
    CONTEMPORARY = "contemporary"
    MEDITERRANEAN = "mediterranean"
    CRAFTSMAN = "craftsman"
    COLONIAL = "colonial"
    RANCH = "ranch"
    VICTORIAN = "victorian"
    MINIMALIST = "minimalist"


class BudgetLevel(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    LUXURY = "luxury"


class Climate(str, Enum):
    TROPICAL = "tropical"
    TEMPERATE = "temperate"
    COLD = "cold"
    ARID = "arid"
    MEDITERRANEAN = "mediterranean"


class RoofType(str, Enum):
    GABLE = "gable"
    HIP = "hip"
    FLAT = "flat"
    SHED = "shed"
    MANSARD = "mansard"


class DesignStatus(str, Enum):
    PENDING = "pending"
    ANALYZING = "analyzing"
    DESIGNING = "designing"
    LAYOUT_2D = "layout_2d"
    MODEL_3D = "model_3d"
    REPORTING = "reporting"
    COMPLETE = "complete"
    ERROR = "error"


# ─── Input Models ──────────────────────────────────────────────────────────────

class HouseRequirements(BaseModel):
    style: HouseStyle = Field(HouseStyle.MODERN, description="Architectural style")
    total_area_sqft: float = Field(2000.0, ge=500, le=20000, description="Total floor area in sq ft")
    floors: int = Field(1, ge=1, le=4, description="Number of above-ground floors")
    bedrooms: int = Field(3, ge=1, le=10)
    bathrooms: int = Field(2, ge=1, le=10)
    has_garage: bool = Field(False, description="Include attached garage")
    garage_cars: int = Field(2, ge=1, le=4, description="Garage capacity in cars")
    has_garden: bool = Field(True, description="Include garden/yard area")
    has_basement: bool = Field(False, description="Include basement level")
    has_home_office: bool = Field(False, description="Dedicated home office")
    has_dining_room: bool = Field(True, description="Separate dining room")
    has_family_room: bool = Field(False, description="Family/media room")
    has_laundry_room: bool = Field(True, description="Dedicated laundry room")
    budget_level: BudgetLevel = Field(BudgetLevel.STANDARD)
    climate: Climate = Field(Climate.TEMPERATE)
    roof_type: RoofType = Field(RoofType.GABLE)
    special_features: List[str] = Field(default_factory=list, description="Extra features")
    custom_notes: Optional[str] = Field(None, description="Any additional design notes")


# ─── Design Output Models ──────────────────────────────────────────────────────

class RoomSpec(BaseModel):
    name: str
    room_type: str
    floor: int
    x: float          # left edge in feet from house origin
    y: float          # bottom edge in feet from house origin
    width: float      # in feet
    depth: float      # in feet
    area: float       # sq ft
    color: str        # hex fill color


class MaterialSpec(BaseModel):
    foundation: str = "Reinforced concrete slab"
    exterior_walls: str = "Brick veneer on wood frame"
    interior_walls: str = "Drywall on metal studs"
    flooring: str = "Hardwood / ceramic tile"
    roofing: str = "Architectural asphalt shingles"
    windows: str = "Double-pane vinyl-framed"
    insulation: str = "Spray foam + batt insulation"


class StructuralNote(BaseModel):
    category: str
    note: str


class CostEstimate(BaseModel):
    low: float
    high: float
    currency: str = "USD"
    note: str = ""


class BasicDesign(BaseModel):
    title: str
    style_description: str
    total_area_sqft: float
    house_width_ft: float
    house_depth_ft: float
    floors: int
    rooms: List[RoomSpec]
    materials: MaterialSpec
    structural_notes: List[str]
    energy_features: List[str]
    cost_estimate: CostEstimate
    ai_description: str
    design_rationale: str


class FloorPlanOutput(BaseModel):
    floor_number: int
    image_url: str        # /api/files/{design_id}/floor_{n}.png
    svg_url: str          # /api/files/{design_id}/floor_{n}.svg
    width_ft: float
    depth_ft: float
    rooms: List[str]


class Model3DOutput(BaseModel):
    html_url: str         # /api/files/{design_id}/model_3d.html
    json_url: str         # /api/files/{design_id}/model_3d.json
    scene_summary: str


class DesignResult(BaseModel):
    design_id: str
    status: DesignStatus
    stage: str
    progress: int = Field(0, ge=0, le=100)
    requirements: Optional[HouseRequirements] = None
    basic_design: Optional[BasicDesign] = None
    floor_plans: Optional[List[FloorPlanOutput]] = None
    model_3d: Optional[Model3DOutput] = None
    report_url: Optional[str] = None
    error: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    completed_at: Optional[str] = None


# ─── API Request/Response Models ───────────────────────────────────────────────

class DesignRequest(BaseModel):
    requirements: HouseRequirements


class DesignInitResponse(BaseModel):
    design_id: str
    message: str
    status_url: str
    websocket_url: str
