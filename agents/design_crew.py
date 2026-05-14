"""NeoArchAI - CrewAI Multi-Agent Design Crew

Four specialized agents collaborate to produce a complete BasicDesign:
  1. Requirements Analyst  – understands the brief
  2. Master Architect       – layout & spatial design
  3. Structural Engineer    – materials & structure
  4. Interior Designer      – finishes, flow, livability

Falls back to algorithmic generation if LLM is unavailable.
"""
from __future__ import annotations
import json
import math
import logging
import os
from typing import Any, Dict, List

from config import get_crewai_llm, GROQ_API_KEY, LLM_PROVIDER

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Room type catalogue
# ─────────────────────────────────────────────────────────────────────────────

ROOM_CATALOG: Dict[str, Dict[str, Any]] = {
    "living_room":       {"label": "Living Room",         "zone": "public",  "min_w": 14, "min_d": 16, "pref_w": 16, "pref_d": 20, "color": "#E3F2FD"},
    "dining_room":       {"label": "Dining Room",         "zone": "public",  "min_w": 10, "min_d": 12, "pref_w": 12, "pref_d": 14, "color": "#FFF3E0"},
    "kitchen":           {"label": "Kitchen",             "zone": "service", "min_w": 10, "min_d": 12, "pref_w": 12, "pref_d": 14, "color": "#F3E5F5"},
    "master_bedroom":    {"label": "Master Bedroom",      "zone": "private", "min_w": 13, "min_d": 15, "pref_w": 14, "pref_d": 16, "color": "#E8F5E9"},
    "bedroom":           {"label": "Bedroom",             "zone": "private", "min_w": 10, "min_d": 12, "pref_w": 12, "pref_d": 13, "color": "#E1F5FE"},
    "master_bathroom":   {"label": "Master Bathroom",     "zone": "private", "min_w": 8,  "min_d": 10, "pref_w": 10, "pref_d": 12, "color": "#E0F2F1"},
    "bathroom":          {"label": "Bathroom",            "zone": "private", "min_w": 6,  "min_d": 8,  "pref_w": 8,  "pref_d": 10, "color": "#B2EBF2"},
    "garage":            {"label": "Garage",              "zone": "service", "min_w": 20, "min_d": 20, "pref_w": 22, "pref_d": 22, "color": "#ECEFF1"},
    "laundry_room":      {"label": "Laundry Room",        "zone": "service", "min_w": 6,  "min_d": 8,  "pref_w": 8,  "pref_d": 10, "color": "#FFF8E1"},
    "home_office":       {"label": "Home Office",         "zone": "private", "min_w": 10, "min_d": 11, "pref_w": 11, "pref_d": 12, "color": "#FCE4EC"},
    "family_room":       {"label": "Family Room",         "zone": "public",  "min_w": 13, "min_d": 16, "pref_w": 14, "pref_d": 18, "color": "#FFF9C4"},
    "hallway":           {"label": "Hallway",             "zone": "circulation", "min_w": 4, "min_d": 4, "pref_w": 4, "pref_d": 4, "color": "#F5F5F5"},
    "staircase":         {"label": "Staircase",           "zone": "circulation", "min_w": 4, "min_d": 10,"pref_w": 4, "pref_d": 10,"color": "#FAFAFA"},
    "foyer":             {"label": "Foyer / Entry",       "zone": "public",  "min_w": 6,  "min_d": 8,  "pref_w": 8,  "pref_d": 10, "color": "#FBE9E7"},
    "powder_room":       {"label": "Powder Room",         "zone": "service", "min_w": 4,  "min_d": 6,  "pref_w": 5,  "pref_d": 7,  "color": "#E8EAF6"},
}

MATERIAL_PRESETS = {
    "basic": {
        "foundation": "Reinforced concrete slab-on-grade",
        "exterior_walls": "Vinyl siding on wood frame",
        "interior_walls": "Drywall on wood studs",
        "flooring": "Laminate / vinyl plank",
        "roofing": "3-tab asphalt shingles",
        "windows": "Single-pane vinyl-framed",
        "insulation": "Fiberglass batt insulation",
    },
    "standard": {
        "foundation": "Reinforced concrete slab with perimeter footings",
        "exterior_walls": "Brick veneer on wood frame",
        "interior_walls": "Drywall on metal studs",
        "flooring": "Hardwood / ceramic tile",
        "roofing": "Architectural asphalt shingles",
        "windows": "Double-pane low-E vinyl-framed",
        "insulation": "Spray foam + batt insulation",
    },
    "luxury": {
        "foundation": "Reinforced concrete with waterproofed basement",
        "exterior_walls": "Stone / stucco on ICF blocks",
        "interior_walls": "Drywall on metal studs with sound insulation",
        "flooring": "Solid hardwood / imported marble",
        "roofing": "Metal standing-seam / clay tiles",
        "windows": "Triple-pane aluminum-clad with UV coating",
        "insulation": "Spray foam with thermal break",
    },
}

ENERGY_FEATURES = {
    "basic": ["LED lighting throughout", "Programmable thermostat", "Low-flow plumbing fixtures"],
    "standard": [
        "High-efficiency HVAC (SEER 16+)", "LED lighting", "Smart thermostat",
        "Low-flow plumbing", "Insulated garage door", "Solar-ready roof orientation",
    ],
    "luxury": [
        "Solar panel system (10 kW)", "Geothermal HVAC", "Triple-pane windows",
        "Smart home automation", "Rainwater harvesting", "EV charging station",
        "Heat recovery ventilation", "Green roof option",
    ],
}

COST_PER_SQFT = {
    ("basic",    "cold"):          (120, 160),
    ("basic",    "temperate"):     (110, 150),
    ("basic",    "tropical"):      (105, 145),
    ("basic",    "arid"):          (108, 148),
    ("standard", "cold"):          (175, 250),
    ("standard", "temperate"):     (160, 235),
    ("standard", "tropical"):      (155, 225),
    ("standard", "arid"):          (158, 228),
    ("luxury",   "cold"):          (320, 520),
    ("luxury",   "temperate"):     (300, 500),
    ("luxury",   "tropical"):      (290, 480),
    ("luxury",   "arid"):          (295, 490),
}


# ─────────────────────────────────────────────────────────────────────────────
# Room list builder
# ─────────────────────────────────────────────────────────────────────────────

def _build_room_list(req: dict) -> List[dict]:
    """Return ordered list of rooms needed for this house."""
    rooms: List[dict] = []
    floors = req.get("floors", 1)
    bedrooms = req.get("bedrooms", 3)
    bathrooms = req.get("bathrooms", 2)

    if floors == 1:
        # ── Ground floor only ──────────────────────────────────────────────
        rooms.append({**ROOM_CATALOG["foyer"],        "room_type": "foyer",        "floor": 1})
        rooms.append({**ROOM_CATALOG["living_room"],  "room_type": "living_room",  "floor": 1})
        if req.get("has_dining_room", True):
            rooms.append({**ROOM_CATALOG["dining_room"], "room_type": "dining_room", "floor": 1})
        rooms.append({**ROOM_CATALOG["kitchen"],       "room_type": "kitchen",       "floor": 1})
        if req.get("has_family_room", False):
            rooms.append({**ROOM_CATALOG["family_room"], "room_type": "family_room", "floor": 1})

        # Garage / laundry
        if req.get("has_garage", False):
            rooms.append({**ROOM_CATALOG["garage"],     "room_type": "garage",       "floor": 1})
        if req.get("has_laundry_room", True):
            rooms.append({**ROOM_CATALOG["laundry_room"],"room_type": "laundry_room","floor": 1})
        if req.get("has_home_office", False):
            rooms.append({**ROOM_CATALOG["home_office"], "room_type": "home_office", "floor": 1})

        # Master suite
        rooms.append({**ROOM_CATALOG["master_bedroom"],  "room_type": "master_bedroom",  "floor": 1})
        rooms.append({**ROOM_CATALOG["master_bathroom"], "room_type": "master_bathroom", "floor": 1})

        # Additional bedrooms
        for i in range(2, bedrooms + 1):
            rooms.append({**ROOM_CATALOG["bedroom"], "room_type": "bedroom",
                          "label": f"Bedroom {i}", "floor": 1})
        # Additional bathrooms (beyond master)
        for _ in range(1, bathrooms):
            rooms.append({**ROOM_CATALOG["bathroom"], "room_type": "bathroom", "floor": 1})

    else:
        # ── Ground floor: public + service ────────────────────────────────
        rooms.append({**ROOM_CATALOG["foyer"],        "room_type": "foyer",        "floor": 1})
        rooms.append({**ROOM_CATALOG["living_room"],  "room_type": "living_room",  "floor": 1})
        if req.get("has_dining_room", True):
            rooms.append({**ROOM_CATALOG["dining_room"], "room_type": "dining_room", "floor": 1})
        rooms.append({**ROOM_CATALOG["kitchen"],       "room_type": "kitchen",       "floor": 1})
        rooms.append({**ROOM_CATALOG["powder_room"],   "room_type": "powder_room",   "floor": 1})
        if req.get("has_family_room", False):
            rooms.append({**ROOM_CATALOG["family_room"], "room_type": "family_room", "floor": 1})
        if req.get("has_garage", False):
            rooms.append({**ROOM_CATALOG["garage"],     "room_type": "garage",       "floor": 1})
        if req.get("has_laundry_room", True):
            rooms.append({**ROOM_CATALOG["laundry_room"],"room_type": "laundry_room","floor": 1})
        if req.get("has_home_office", False):
            rooms.append({**ROOM_CATALOG["home_office"], "room_type": "home_office", "floor": 1})
        rooms.append({**ROOM_CATALOG["staircase"],     "room_type": "staircase",    "floor": 1})

        # ── Upper floor(s): private ───────────────────────────────────────
        for floor_num in range(2, floors + 1):
            rooms.append({**ROOM_CATALOG["staircase"],      "room_type": "staircase",     "floor": floor_num})
            rooms.append({**ROOM_CATALOG["master_bedroom"],  "room_type": "master_bedroom", "floor": floor_num})
            rooms.append({**ROOM_CATALOG["master_bathroom"], "room_type": "master_bathroom","floor": floor_num})
            for i in range(2, bedrooms + 1):
                rooms.append({**ROOM_CATALOG["bedroom"], "room_type": "bedroom",
                              "label": f"Bedroom {i}", "floor": floor_num})
            for _ in range(1, bathrooms):
                rooms.append({**ROOM_CATALOG["bathroom"], "room_type": "bathroom", "floor": floor_num})

    return rooms


# ─────────────────────────────────────────────────────────────────────────────
# Room layout algorithm
# ─────────────────────────────────────────────────────────────────────────────

def _layout_floor(rooms: List[dict], floor_num: int,
                  house_w: float, house_d: float) -> List[dict]:
    """
    Place rooms for a single floor using a zone-strip packing approach.
    Returns rooms augmented with x, y, width, depth, area fields.
    """
    WALL_T = 0.5   # wall thickness
    HALL_D = 4.0   # central hallway depth

    floor_rooms = [r for r in rooms if r["floor"] == floor_num]
    if not floor_rooms:
        return []

    # Zone allocation
    front_d = (house_d - HALL_D) * 0.42    # public zone
    back_d  = house_d - HALL_D - front_d   # private/service zone
    hall_y  = front_d

    # Separate rooms by zone
    public   = [r for r in floor_rooms if r["zone"] == "public"]
    private  = [r for r in floor_rooms if r["zone"] == "private"]
    service  = [r for r in floor_rooms if r["zone"] == "service"]
    circ     = [r for r in floor_rooms if r["zone"] == "circulation"]

    placed: List[dict] = []

    def strip_pack(room_list: List[dict], origin_x: float, origin_y: float,
                   avail_w: float, avail_d: float) -> None:
        """Pack rooms side-by-side, scaling to fill avail_w × avail_d."""
        if not room_list:
            return
        total_pref_w = sum(r["pref_w"] for r in room_list)
        scale = avail_w / max(total_pref_w, avail_w)
        cx = origin_x
        for room in room_list:
            rw = room["pref_w"] * scale
            rd = avail_d
            placed.append({
                **room,
                "x": round(cx + WALL_T, 2),
                "y": round(origin_y + WALL_T, 2),
                "width": round(rw - WALL_T, 2),
                "depth": round(rd - WALL_T, 2),
                "area": round((rw - WALL_T) * (rd - WALL_T), 1),
            })
            cx += rw

    # Front zone: public rooms
    strip_pack(public, 0, 0, house_w, front_d)

    # Back zone: private then service, side by side
    back_rooms = private + service + circ
    strip_pack(back_rooms, 0, hall_y + HALL_D, house_w, back_d)

    return placed


# ─────────────────────────────────────────────────────────────────────────────
# Algorithmic fallback (no LLM)
# ─────────────────────────────────────────────────────────────────────────────

def algorithmic_basic_design(req: dict) -> dict:
    """Pure-Python design generation (no LLM required)."""
    style        = req.get("style", "modern")
    area         = float(req.get("total_area_sqft", 2000))
    floors       = int(req.get("floors", 1))
    budget       = req.get("budget_level", "standard")
    climate      = req.get("climate", "temperate")
    bedrooms     = req.get("bedrooms", 3)
    bathrooms    = req.get("bathrooms", 2)

    area_per_floor = area / floors
    # Aspect ratio 1 : 1.4 (width : depth)
    house_w = round(math.sqrt(area_per_floor / 1.4), 1)
    house_d = round(area_per_floor / house_w, 1)

    # Rooms
    room_list = _build_room_list(req)
    all_rooms: List[dict] = []
    for fl in range(1, floors + 1):
        placed = _layout_floor(room_list, fl, house_w, house_d)
        all_rooms.extend(placed)

    # Convert to RoomSpec-compatible dicts
    room_specs = []
    for i, r in enumerate(all_rooms):
        room_specs.append({
            "name":      r.get("label", r.get("room_type", "Room").replace("_", " ").title()),
            "room_type": r["room_type"],
            "floor":     r["floor"],
            "x":         r.get("x", 0),
            "y":         r.get("y", 0),
            "width":     r.get("width", r.get("pref_w", 10)),
            "depth":     r.get("depth", r.get("pref_d", 12)),
            "area":      r.get("area", r.get("pref_w", 10) * r.get("pref_d", 12)),
            "color":     r.get("color", "#FFFFFF"),
        })

    # Materials & energy
    materials = MATERIAL_PRESETS.get(budget, MATERIAL_PRESETS["standard"])
    energy    = ENERGY_FEATURES.get(budget, ENERGY_FEATURES["standard"])

    # Cost estimate
    key   = (budget, climate)
    cpf   = COST_PER_SQFT.get(key, COST_PER_SQFT[("standard", "temperate")])
    low   = round(area * cpf[0])
    high  = round(area * cpf[1])

    structural_notes = [
        f"Foundation: {materials['foundation']}",
        f"Exterior wall system: {materials['exterior_walls']}",
        f"Roof: {req.get('roof_type', 'gable').title()} style – {materials['roofing']}",
        "Load-bearing walls per structural engineer's drawings",
        f"Insulation R-values per {climate.title()} climate zone requirements",
        "All openings (doors/windows) with appropriate lintels",
    ]
    if req.get("has_basement", False):
        structural_notes.append("Basement: waterproofed concrete with sump pump")

    description = (
        f"A {style.title()} {floors}-story residence designed for {climate} climate. "
        f"The {area:.0f} sq ft floor plan features {bedrooms} bedrooms and {bathrooms} bathrooms "
        f"with an emphasis on natural light, efficient circulation, and {budget.lower()} finishes. "
        f"Public living spaces occupy the front zone while private areas are positioned "
        f"toward the back for optimal privacy."
    )

    return {
        "title":            f"{style.title()} {area:.0f} sqft Residence",
        "style_description": f"{style.title()} architecture with {budget} finishes",
        "total_area_sqft":  area,
        "house_width_ft":   house_w,
        "house_depth_ft":   house_d,
        "floors":           floors,
        "rooms":            room_specs,
        "materials":        materials,
        "structural_notes": structural_notes,
        "energy_features":  energy,
        "cost_estimate":    {"low": low, "high": high, "currency": "USD",
                             "note": f"Estimate based on ${cpf[0]}-${cpf[1]}/sqft for {budget} build"},
        "ai_description":   description,
        "design_rationale": (
            f"Zone-based layout separates public and private areas for optimal living. "
            f"Rooms sized to {budget} standards with climate-appropriate materials for {climate} zone."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# CrewAI Crew runner
# ─────────────────────────────────────────────────────────────────────────────

def run_design_crew(req: dict) -> dict:
    """
    Run a CrewAI crew of 4 agents to produce an enriched BasicDesign dict.
    Falls back to algorithmic_basic_design on any error.
    """
    crewai_llm = get_crewai_llm()
    if not crewai_llm:
        logger.info("No LLM configured – using algorithmic design.")
        return algorithmic_basic_design(req)

    try:
        from crewai import Agent, Task, Crew, Process, LLM

        llm = LLM(model=crewai_llm, temperature=0.7)

        # ── Agents ────────────────────────────────────────────────────────
        analyst = Agent(
            role="Senior Requirements Analyst",
            goal="Extract precise spatial and functional requirements from client brief",
            backstory=(
                "15 years analyzing residential projects. Expert at translating "
                "client wishes into measurable architectural requirements."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )

        architect = Agent(
            role="Master Architect",
            goal="Create a complete, buildable house design with optimal room layout",
            backstory=(
                "Award-winning residential architect with expertise in "
                f"{req.get('style','modern')} design and space optimization."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )

        engineer = Agent(
            role="Structural Engineer",
            goal="Specify structurally sound materials and construction methods",
            backstory=(
                "Licensed PE with 20 years in residential construction. "
                "Expert in cost-effective structural systems."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )

        interior = Agent(
            role="Interior Design Specialist",
            goal="Optimize interior flow, finishes, and energy efficiency",
            backstory=(
                "NCIDQ-certified designer specializing in functional, beautiful interiors "
                "that maximize homeowner comfort and resale value."
            ),
            llm=llm,
            verbose=False,
            allow_delegation=False,
        )

        # ── Context string ────────────────────────────────────────────────
        req_str = json.dumps(req, indent=2)

        # ── Tasks ─────────────────────────────────────────────────────────
        analysis_task = Task(
            description=f"""Analyze this house brief and identify the 5 most important design priorities:
{req_str}
Output a numbered list of priorities with brief justifications.""",
            expected_output="Numbered list of 5 design priorities with justifications",
            agent=analyst,
        )

        design_task = Task(
            description=f"""Using the analysis above, design a complete {req.get('style','modern')} house:
- {req.get('floors',1)} floor(s), {req.get('total_area_sqft',2000)} sq ft total
- {req.get('bedrooms',3)} bedrooms, {req.get('bathrooms',2)} bathrooms
- Style: {req.get('style','modern')}, Climate: {req.get('climate','temperate')}

Write a 3-sentence architectural description capturing the design philosophy and key features.
Then list the top 5 unique design decisions you made for this specific brief.""",
            expected_output="3-sentence description + 5 design decisions",
            agent=architect,
            context=[analysis_task],
        )

        structural_task = Task(
            description=f"""Specify materials and structural notes for a {req.get('budget_level','standard')} budget {req.get('style','modern')} house.
Climate: {req.get('climate','temperate')}. Floors: {req.get('floors',1)}.
Provide: foundation, walls, roof, windows, insulation, and 3 critical structural notes.""",
            expected_output="Material specifications + 3 structural notes",
            agent=engineer,
            context=[design_task],
        )

        interior_task = Task(
            description=f"""Recommend interior finishes and energy features for a {req.get('budget_level','standard')} {req.get('style','modern')} home.
Write a 2-sentence design rationale on spatial flow and lifestyle.""",
            expected_output="Interior finishes + energy features list + 2-sentence rationale",
            agent=interior,
            context=[design_task],
        )

        # ── Run crew ──────────────────────────────────────────────────────
        crew = Crew(
            agents=[analyst, architect, engineer, interior],
            tasks=[analysis_task, design_task, structural_task, interior_task],
            process=Process.sequential,
            verbose=False,
        )

        result = crew.kickoff()

        # ── Merge LLM outputs into algorithmic base ────────────────────────
        base = algorithmic_basic_design(req)

        # Extract text outputs
        task_outputs = result.tasks_output if hasattr(result, "tasks_output") else []
        design_text   = task_outputs[1].raw if len(task_outputs) > 1 else ""
        interior_text = task_outputs[3].raw if len(task_outputs) > 3 else ""

        # Enrich description and rationale with LLM content
        if design_text:
            sentences = [s.strip() for s in design_text.split(".") if s.strip()]
            base["ai_description"]   = ". ".join(sentences[:3]) + "." if sentences else base["ai_description"]
        if interior_text:
            sentences = [s.strip() for s in interior_text.split(".") if s.strip()]
            base["design_rationale"] = ". ".join(sentences[:2]) + "." if sentences else base["design_rationale"]

        return base

    except Exception as exc:
        logger.warning("CrewAI run failed (%s), using algorithmic fallback.", exc)
        return algorithmic_basic_design(req)
