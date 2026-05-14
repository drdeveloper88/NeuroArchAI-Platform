"""NeoArchAI - 2D Architectural Floor Plan Renderer

Generates professional-quality floor plans using matplotlib.
Output: PNG (high-res) + SVG (vector) per floor.
"""
from __future__ import annotations
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

import matplotlib
matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Arc, FancyArrowPatch
import matplotlib.patheffects as pe
import numpy as np

# ── Visual constants ──────────────────────────────────────────────────────────
WALL_COLOR        = "#2C2C2C"
WALL_THICKNESS    = 3        # outer wall line width
INNER_WALL_WIDTH  = 1.5      # inner wall line width
DIMENSION_COLOR   = "#555555"
TITLE_FONT_SIZE   = 12
ROOM_LABEL_SIZE   = 7.5
DIM_FONT_SIZE     = 6.5
DPI               = 180      # export resolution

ROOM_COLORS: Dict[str, str] = {
    "living_room":    "#D6EAF8",
    "dining_room":    "#FDEBD0",
    "kitchen":        "#E8DAEF",
    "master_bedroom": "#D5F5E3",
    "bedroom":        "#D6EAF8",
    "master_bathroom":"#D1F2EB",
    "bathroom":       "#ABEBC6",
    "garage":         "#D5D8DC",
    "laundry_room":   "#FEF9E7",
    "home_office":    "#FADBD8",
    "family_room":    "#FEF3CD",
    "hallway":        "#F2F3F4",
    "staircase":      "#EAECEE",
    "foyer":          "#FBE8E7",
    "powder_room":    "#E8EAF6",
    "default":        "#FDFEFE",
}


# ── Helper drawing functions ──────────────────────────────────────────────────

def _room_color(room_type: str) -> str:
    return ROOM_COLORS.get(room_type, ROOM_COLORS["default"])


def _draw_door(ax: plt.Axes, x: float, y: float, width: float,
               wall_side: str = "bottom", open_angle: float = 90.0) -> None:
    """Draw a standard door symbol: swing arc + door leaf line."""
    door_w = min(width * 0.6, 3.0)
    if wall_side == "bottom":
        # Door leaf goes up from wall
        ax.plot([x, x], [y, y + door_w], color=WALL_COLOR, lw=1.2, zorder=5)
        arc = Arc((x, y), 2 * door_w, 2 * door_w,
                  angle=0, theta1=0, theta2=open_angle,
                  color=WALL_COLOR, lw=0.8, zorder=5)
    elif wall_side == "top":
        ax.plot([x, x], [y, y - door_w], color=WALL_COLOR, lw=1.2, zorder=5)
        arc = Arc((x, y), 2 * door_w, 2 * door_w,
                  angle=0, theta1=180, theta2=180 + open_angle,
                  color=WALL_COLOR, lw=0.8, zorder=5)
    elif wall_side == "left":
        ax.plot([x, x + door_w], [y, y], color=WALL_COLOR, lw=1.2, zorder=5)
        arc = Arc((x, y), 2 * door_w, 2 * door_w,
                  angle=0, theta1=270, theta2=270 + open_angle,
                  color=WALL_COLOR, lw=0.8, zorder=5)
    else:  # right
        ax.plot([x - door_w, x], [y, y], color=WALL_COLOR, lw=1.2, zorder=5)
        arc = Arc((x, y), 2 * door_w, 2 * door_w,
                  angle=0, theta1=90, theta2=90 + open_angle,
                  color=WALL_COLOR, lw=0.8, zorder=5)
    ax.add_patch(arc)


def _draw_window(ax: plt.Axes, x: float, y: float, length: float,
                 orientation: str = "horizontal") -> None:
    """Draw window symbol: double parallel lines on wall."""
    gap = 0.3
    if orientation == "horizontal":
        ax.plot([x, x + length], [y - gap, y - gap], "b-", lw=1.0, zorder=6)
        ax.plot([x, x + length], [y + gap, y + gap], "b-", lw=1.0, zorder=6)
        ax.plot([x, x + length], [y, y], color="#AED6F1", lw=2.5, zorder=5, alpha=0.6)
    else:
        ax.plot([x - gap, x - gap], [y, y + length], "b-", lw=1.0, zorder=6)
        ax.plot([x + gap, x + gap], [y, y + length], "b-", lw=1.0, zorder=6)
        ax.plot([x, x], [y, y + length], color="#AED6F1", lw=2.5, zorder=5, alpha=0.6)


def _draw_staircase(ax: plt.Axes, x: float, y: float, w: float, d: float) -> None:
    """Draw staircase symbol with steps."""
    steps = 10
    step_h = d / steps
    for i in range(steps):
        ax.plot([x, x + w], [y + i * step_h, y + i * step_h],
                color=WALL_COLOR, lw=0.6, alpha=0.7, zorder=5)
    # Arrow indicating direction
    ax.annotate("", xy=(x + w / 2, y + d - 0.5), xytext=(x + w / 2, y + 0.5),
                arrowprops=dict(arrowstyle="->", color="#555555", lw=1))


def _draw_dimension(ax: plt.Axes, x1: float, y1: float,
                    x2: float, y2: float, value: str,
                    offset: float = 1.5, orientation: str = "h") -> None:
    """Draw a dimension line with text."""
    if orientation == "h":
        oy = y1 - offset
        ax.annotate("", xy=(x2, oy), xytext=(x1, oy),
                    arrowprops=dict(arrowstyle="<->", color=DIMENSION_COLOR, lw=0.8))
        ax.text((x1 + x2) / 2, oy - 0.35, value,
                ha="center", va="top", fontsize=DIM_FONT_SIZE, color=DIMENSION_COLOR)
    else:
        ox = x1 - offset
        ax.annotate("", xy=(ox, y2), xytext=(ox, y1),
                    arrowprops=dict(arrowstyle="<->", color=DIMENSION_COLOR, lw=0.8))
        ax.text(ox - 0.35, (y1 + y2) / 2, value,
                ha="right", va="center", fontsize=DIM_FONT_SIZE,
                color=DIMENSION_COLOR, rotation=90)


def _north_arrow(ax: plt.Axes, x: float, y: float, size: float = 1.5) -> None:
    """Draw a north arrow indicator."""
    ax.annotate("", xy=(x, y + size), xytext=(x, y),
                arrowprops=dict(arrowstyle="-|>", color="black", lw=1.5,
                                mutation_scale=12))
    ax.text(x, y + size + 0.3, "N", ha="center", va="bottom",
            fontsize=8, fontweight="bold")


# ── Main floor rendering function ─────────────────────────────────────────────

def _render_floor(rooms_on_floor: List[dict], floor_num: int,
                  house_w: float, house_d: float,
                  design_title: str, style: str) -> plt.Figure:
    """Render a single floor plan and return the matplotlib Figure."""
    MARGIN = 4.0
    fig_w  = (house_w + 2 * MARGIN) / 8   # scale to inches
    fig_h  = (house_d + 2 * MARGIN) / 8

    fig, ax = plt.subplots(1, 1, figsize=(max(fig_w, 10), max(fig_h, 8)))
    ax.set_facecolor("#F8F8F8")
    fig.patch.set_facecolor("#FFFFFF")

    # ── Outer boundary (thick wall) ───────────────────────────────────────
    outer = patches.Rectangle(
        (0, 0), house_w, house_d,
        linewidth=WALL_THICKNESS, edgecolor=WALL_COLOR,
        facecolor="#FFFFFF", zorder=1
    )
    ax.add_patch(outer)

    # ── Draw each room ────────────────────────────────────────────────────
    for room in rooms_on_floor:
        rx, ry = room["x"], room["y"]
        rw, rd = room["width"], room["depth"]
        rt     = room.get("room_type", "default")
        rname  = room.get("name", rt.replace("_", " ").title())
        rarea  = room.get("area", rw * rd)
        color  = _room_color(rt)

        # Room fill
        rect = patches.Rectangle(
            (rx, ry), rw, rd,
            linewidth=INNER_WALL_WIDTH, edgecolor=WALL_COLOR,
            facecolor=color, zorder=2, alpha=0.92
        )
        ax.add_patch(rect)

        # Staircase special drawing
        if rt == "staircase":
            _draw_staircase(ax, rx, ry, rw, rd)

        # Room label (name + area)
        mid_x, mid_y = rx + rw / 2, ry + rd / 2
        ax.text(mid_x, mid_y + 0.4, rname,
                ha="center", va="center", fontsize=ROOM_LABEL_SIZE,
                fontweight="bold", color="#1A1A1A", zorder=7,
                wrap=True)
        ax.text(mid_x, mid_y - 0.6, f"{rarea:.0f} sq ft",
                ha="center", va="center", fontsize=DIM_FONT_SIZE - 0.5,
                color="#555555", zorder=7)

        # Add door symbol on bottom wall
        if rt not in ("staircase", "hallway", "garage"):
            door_x = rx + rw * 0.25
            _draw_door(ax, door_x, ry, rw, wall_side="bottom")

        # Add window on outer walls
        if ry < 1.0 and rw > 4:           # south-facing room
            _draw_window(ax, rx + 1, 0, min(rw - 2, 4), "horizontal")
        if ry + rd > house_d - 1 and rw > 4:  # north-facing room
            _draw_window(ax, rx + 1, house_d, min(rw - 2, 4), "horizontal")

    # ── Overall dimension lines ───────────────────────────────────────────
    _draw_dimension(ax, 0, 0, house_w, 0, f"{house_w:.1f}'",
                    offset=2.5, orientation="h")
    _draw_dimension(ax, 0, 0, 0, house_d, f"{house_d:.1f}'",
                    offset=2.5, orientation="v")

    # ── North arrow ───────────────────────────────────────────────────────
    _north_arrow(ax, house_w + 1.5, house_d * 0.7)

    # ── Title block ───────────────────────────────────────────────────────
    ax.text(house_w / 2, -3.2,
            f"{design_title}  |  Floor {floor_num}  |  {style.title()} Style",
            ha="center", va="top", fontsize=TITLE_FONT_SIZE,
            fontweight="bold", color="#1A1A1A")
    ax.text(house_w / 2, -4.0,
            f"Scale: 1/8\" = 1'  |  Total floor area: {house_w * house_d:.0f} sq ft",
            ha="center", va="top", fontsize=7, color="#666666")

    # ── Axis formatting ───────────────────────────────────────────────────
    ax.set_xlim(-MARGIN, house_w + MARGIN)
    ax.set_ylim(-MARGIN * 1.4, house_d + MARGIN * 0.8)
    ax.set_aspect("equal")
    ax.axis("off")

    return fig


# ── Public API ────────────────────────────────────────────────────────────────

def render_all_floors(basic_design: dict, design_dir: Path, design_id: str) -> List[dict]:
    """
    Render floor plans for all floors.
    Returns list of FloorPlanOutput-compatible dicts.
    """
    rooms_all = basic_design.get("rooms", [])
    house_w   = float(basic_design.get("house_width_ft",  40))
    house_d   = float(basic_design.get("house_depth_ft",  50))
    floors    = int(basic_design.get("floors", 1))
    title     = basic_design.get("title", "Residence")
    style     = basic_design.get("style_description", "modern").split()[0]

    outputs: List[dict] = []

    for floor_num in range(1, floors + 1):
        floor_rooms = [r for r in rooms_all if r.get("floor") == floor_num]
        if not floor_rooms:
            continue

        fig = _render_floor(floor_rooms, floor_num, house_w, house_d, title, style)

        png_path = design_dir / f"floor_{floor_num}.png"
        svg_path = design_dir / f"floor_{floor_num}.svg"

        fig.savefig(str(png_path), dpi=DPI, bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        fig.savefig(str(svg_path), format="svg", bbox_inches="tight",
                    facecolor="white", edgecolor="none")
        plt.close(fig)

        outputs.append({
            "floor_number": floor_num,
            "image_url":    f"/api/files/{design_id}/floor_{floor_num}.png",
            "svg_url":      f"/api/files/{design_id}/floor_{floor_num}.svg",
            "width_ft":     house_w,
            "depth_ft":     house_d,
            "rooms":        [r.get("name", r.get("room_type", "")) for r in floor_rooms],
        })

    return outputs
