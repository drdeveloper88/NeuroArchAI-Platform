"""NeoArchAI - 3D House Visualization

Builds a fully interactive Plotly 3D model of the house:
  - Exterior shell (walls + gable roof)
  - Interior cutaway showing color-coded rooms
  - Foundation slab
  - Interactive camera controls in browser
Output: self-contained HTML + scene JSON
"""
from __future__ import annotations
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ── Colour palette ────────────────────────────────────────────────────────────
ROOM_COLORS_3D: Dict[str, str] = {
    "living_room":    "#AED6F1",
    "dining_room":    "#F9E79F",
    "kitchen":        "#D7BDE2",
    "master_bedroom": "#A9DFBF",
    "bedroom":        "#AED6F1",
    "master_bathroom":"#76D7C4",
    "bathroom":       "#A3E4D7",
    "garage":         "#BFC9CA",
    "laundry_room":   "#FAD7A0",
    "home_office":    "#F1948A",
    "family_room":    "#F7DC6F",
    "hallway":        "#E5E7E9",
    "staircase":      "#D5D8DC",
    "foyer":          "#FDEBD0",
    "powder_room":    "#C5CAE9",
    "default":        "#ECF0F1",
}

WALL_COLOR_3D   = "#E8E8E0"    # off-white exterior
ROOF_COLOR_3D   = "#7D6608"    # dark golden-brown roof
FLOOR_COLOR_3D  = "#D5B07A"    # warm wood floor
FOUND_COLOR_3D  = "#95A5A6"    # concrete foundation
GRASS_COLOR_3D  = "#A9DFBF"    # garden green
WALL_HEIGHT     = 9.0           # standard ceiling height (ft)
ROOF_RISE       = 5.5           # gable roof peak above wall top
FOUNDATION_H    = 1.5           # foundation slab thickness


# ── Mesh helpers ─────────────────────────────────────────────────────────────

def _box_mesh(x: float, y: float, z: float,
              w: float, d: float, h: float,
              color: str, name: str,
              opacity: float = 1.0) -> go.Mesh3d:
    """Return a Mesh3d trace for an axis-aligned box."""
    x1, y1, z1 = x + w, y + d, z + h
    # 8 vertices
    vx = [x, x1, x1, x,  x,  x1, x1, x ]
    vy = [y, y,  y1, y1, y,  y,  y1, y1]
    vz = [z, z,  z,  z,  z1, z1, z1, z1]
    # 12 triangles (2 per face × 6 faces)
    i  = [0, 0, 1, 1, 2, 2, 3, 3, 0, 0, 4, 4]
    j  = [1, 2, 2, 5, 3, 6, 0, 7, 4, 5, 5, 6]
    k  = [2, 3, 5, 6, 6, 7, 7, 4, 5, 1, 6, 7]
    return go.Mesh3d(
        x=vx, y=vy, z=vz, i=i, j=j, k=k,
        color=color, opacity=opacity, name=name,
        showlegend=True, flatshading=True,
        lighting=dict(ambient=0.7, diffuse=0.8, specular=0.3),
    )


def _gable_roof(x: float, y: float, z_base: float,
                w: float, d: float, rise: float,
                color: str) -> go.Mesh3d:
    """Return a Mesh3d for a gable roof over box (x,y) width w, depth d."""
    ridge_z = z_base + rise
    # 6 vertices: 4 base corners + 2 ridge points
    vx = [x,     x + w,  x + w,  x,     x + w/2, x + w/2]
    vy = [y,     y,      y + d,  y + d, y,        y + d   ]
    vz = [z_base, z_base, z_base, z_base, ridge_z,  ridge_z ]
    # 6 triangular faces
    i  = [0, 3, 0, 0, 1, 1]
    j  = [1, 2, 3, 5, 4, 5]
    k  = [4, 5, 5, 4, 5, 2]
    return go.Mesh3d(
        x=vx, y=vy, z=vz, i=i, j=j, k=k,
        color=color, opacity=1.0, name="Roof",
        showlegend=True, flatshading=True,
        lighting=dict(ambient=0.6, diffuse=0.9),
    )


def _hip_roof(x: float, y: float, z_base: float,
              w: float, d: float, rise: float,
              color: str) -> go.Mesh3d:
    """Return a Mesh3d for a hip roof."""
    inset = min(w, d) * 0.25
    # Ridge is a shorter line at the top
    vx = [x, x+w, x+w,  x,    x+inset, x+w-inset, x+w-inset, x+inset]
    vy = [y, y,   y+d,  y+d,  y+inset, y+inset,   y+d-inset, y+d-inset]
    vz = [z_base]*4 + [z_base+rise]*4
    i  = [0,1,1,2,2,3,3,0, 4,5,6,7]
    j  = [1,5,2,6,3,7,0,4, 5,6,7,4]
    k  = [5,2,6,3,7,0,4,1, 4,4,4,4]
    # Build proper triangles
    triangles_i = [0,1,1,2,2,3,3,0,4,5,5,6,6,7,7,4]
    triangles_j = [4,4,5,5,6,6,7,7,5,4,6,5,7,6,4,7]
    triangles_k = [1,5,2,6,3,7,0,4,4,5,5,6,6,7,7,4]
    return go.Mesh3d(
        x=vx, y=vy, z=vz,
        i=triangles_i, j=triangles_j, k=triangles_k,
        color=color, opacity=1.0, name="Hip Roof",
        showlegend=True, flatshading=True,
    )


def _flat_roof(x: float, y: float, z_base: float,
               w: float, d: float, color: str) -> go.Mesh3d:
    """Flat roof slab with parapet."""
    return _box_mesh(x, y, z_base, w, d, 0.4, color, "Flat Roof")


# ── Main builder ─────────────────────────────────────────────────────────────

def build_3d_model(basic_design: dict, design_dir: Path, design_id: str) -> dict:
    """
    Construct the full Plotly 3D figure and export to HTML + JSON.
    Returns a Model3DOutput-compatible dict.
    """
    rooms     = basic_design.get("rooms", [])
    house_w   = float(basic_design.get("house_width_ft",  40))
    house_d   = float(basic_design.get("house_depth_ft",  50))
    floors    = int(basic_design.get("floors", 1))
    roof_type = "gable"   # default; could read from requirements
    title     = basic_design.get("title", "House 3D Model")

    traces: List[Any] = []

    # ── Foundation slab ───────────────────────────────────────────────────
    traces.append(_box_mesh(
        -1, -1, -FOUNDATION_H, house_w + 2, house_d + 2, FOUNDATION_H,
        FOUND_COLOR_3D, "Foundation", opacity=0.9
    ))

    # ── Garden base ───────────────────────────────────────────────────────
    traces.append(_box_mesh(
        -4, -4, -FOUNDATION_H - 0.1,
        house_w + 8, house_d + 8, 0.1,
        GRASS_COLOR_3D, "Garden", opacity=0.6
    ))

    # ── Per-floor structure ───────────────────────────────────────────────
    for fl in range(1, floors + 1):
        z_floor = (fl - 1) * (WALL_HEIGHT + 0.5)   # 0.5 ft floor slab
        z_wall  = z_floor + 0.5

        # Floor slab
        traces.append(_box_mesh(
            0, 0, z_floor, house_w, house_d, 0.5,
            FLOOR_COLOR_3D, f"Floor {fl} Slab", opacity=1.0
        ))

        # ── Rooms (interior cutaway view - colored floor pads) ────────────
        floor_rooms = [r for r in rooms if r.get("floor") == fl]
        for room in floor_rooms:
            rx, ry = float(room.get("x", 0)), float(room.get("y", 0))
            rw, rd = float(room.get("width", 10)), float(room.get("depth", 12))
            rt     = room.get("room_type", "default")
            rname  = room.get("name", rt.replace("_", " ").title())
            rcolor = ROOM_COLORS_3D.get(rt, ROOM_COLORS_3D["default"])

            # Thin colored slab at floor level
            traces.append(_box_mesh(
                rx, ry, z_floor + 0.5,
                rw, rd, 0.15,
                rcolor, rname, opacity=0.85
            ))

            # Short room boundary walls (2 ft visible for interior view)
            for wall_x, wall_y, wall_w, wall_d in [
                (rx,      ry,      rw,   0.2),   # south
                (rx,      ry + rd - 0.2, rw, 0.2),  # north
                (rx,      ry,      0.2,  rd),    # west
                (rx + rw - 0.2, ry, 0.2, rd),   # east
            ]:
                traces.append(_box_mesh(
                    wall_x, wall_y, z_wall,
                    wall_w, wall_d, 2.0,
                    "#D5D8DC", f"{rname} wall", opacity=0.4
                ))

        # ── Outer shell walls ─────────────────────────────────────────────
        wt = 0.5   # wall thickness
        outer_walls = [
            # (x, y, w, d, label)
            (0,             0,             house_w, wt,      "South Wall"),
            (0,             house_d - wt,  house_w, wt,      "North Wall"),
            (0,             0,             wt,      house_d, "West Wall"),
            (house_w - wt,  0,             wt,      house_d, "East Wall"),
        ]
        for wx, wy, ww, wd, wlabel in outer_walls:
            traces.append(_box_mesh(
                wx, wy, z_wall, ww, wd, WALL_HEIGHT,
                WALL_COLOR_3D, wlabel if fl == 1 else f"L{fl} {wlabel}",
                opacity=0.88
            ))

    # ── Roof ──────────────────────────────────────────────────────────────
    z_roof_base = floors * (WALL_HEIGHT + 0.5)
    if roof_type == "gable":
        traces.append(_gable_roof(0, 0, z_roof_base, house_w, house_d, ROOF_RISE, ROOF_COLOR_3D))
    elif roof_type == "hip":
        traces.append(_hip_roof(0, 0, z_roof_base, house_w, house_d, ROOF_RISE, ROOF_COLOR_3D))
    else:
        traces.append(_flat_roof(0, 0, z_roof_base, house_w, house_d, ROOF_COLOR_3D))

    # ── Layout & scene ────────────────────────────────────────────────────
    max_dim = max(house_w, house_d)
    layout = go.Layout(
        title=dict(text=f"<b>{title}</b> – 3D Visualization",
                   font=dict(size=16, color="#2C3E50"), x=0.5),
        paper_bgcolor="#FAFAFA",
        scene=dict(
            xaxis=dict(title="Width (ft)", showbackground=True,
                       backgroundcolor="#F0F3F4", gridcolor="#BDC3C7"),
            yaxis=dict(title="Depth (ft)", showbackground=True,
                       backgroundcolor="#F0F3F4", gridcolor="#BDC3C7"),
            zaxis=dict(title="Height (ft)", showbackground=True,
                       backgroundcolor="#EBF5FB", gridcolor="#BDC3C7"),
            camera=dict(
                eye=dict(x=1.6, y=-1.6, z=1.2),
                center=dict(x=0, y=0, z=0),
            ),
            aspectmode="data",
        ),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.8)",
                    bordercolor="#BDC3C7", borderwidth=1),
        margin=dict(l=0, r=0, t=40, b=0),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                y=1.05, x=0.1,
                buttons=[
                    dict(label="Exterior View",
                         method="relayout",
                         args=[{"scene.camera": {
                             "eye": {"x": 1.6, "y": -1.6, "z": 1.2},
                             "center": {"x": 0, "y": 0, "z": 0},
                         }}]),
                    dict(label="Top-Down (Floor Plan)",
                         method="relayout",
                         args=[{"scene.camera": {
                             "eye": {"x": 0, "y": 0, "z": 3.0},
                             "center": {"x": 0, "y": 0, "z": 0},
                         }}]),
                    dict(label="Front Elevation",
                         method="relayout",
                         args=[{"scene.camera": {
                             "eye": {"x": 0, "y": -2.5, "z": 0.8},
                             "center": {"x": 0, "y": 0, "z": 0},
                         }}]),
                    dict(label="Interior Cutaway",
                         method="relayout",
                         args=[{"scene.camera": {
                             "eye": {"x": 0.5, "y": 0.2, "z": 2.5},
                             "center": {"x": 0, "y": 0, "z": 0},
                         }}]),
                ],
            )
        ],
    )

    fig = go.Figure(data=traces, layout=layout)

    # ── Export ────────────────────────────────────────────────────────────
    html_path = design_dir / "model_3d.html"
    json_path = design_dir / "model_3d.json"

    fig.write_html(
        str(html_path),
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": True, "scrollZoom": True},
    )

    # Write compact scene JSON (for API consumers / Three.js adapters)
    scene_summary = {
        "house_width_ft": house_w,
        "house_depth_ft": house_d,
        "floors": floors,
        "total_height_ft": round(floors * (WALL_HEIGHT + 0.5) + ROOF_RISE, 1),
        "room_count": len(rooms),
        "roof_type": roof_type,
    }
    json_path.write_text(json.dumps(scene_summary, indent=2))

    return {
        "html_url":      f"/api/files/{design_id}/model_3d.html",
        "json_url":      f"/api/files/{design_id}/model_3d.json",
        "scene_summary": (
            f"{floors}-story {title} | "
            f"{house_w:.0f}' × {house_d:.0f}' footprint | "
            f"{len(rooms)} rooms | {roof_type.title()} roof"
        ),
    }
