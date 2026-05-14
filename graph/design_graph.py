"""NeoArchAI - LangGraph Design Pipeline

Five-stage pipeline:
  analyze_requirements → generate_basic_design → generate_2d_layout
  → generate_3d_model → compile_report
"""
from __future__ import annotations
from langgraph.graph import StateGraph, END

from graph.state import DesignState
from graph.nodes import (
    analyze_requirements_node,
    generate_basic_design_node,
    generate_2d_layout_node,
    generate_3d_model_node,
    compile_report_node,
    error_handler_node,
)


def _should_abort(state: DesignState) -> str:
    """Route to error handler if errors accumulated, else continue."""
    return "error" if state.get("errors") else "continue"


def build_design_graph():
    """Build and compile the LangGraph design pipeline."""
    graph = StateGraph(DesignState)

    # ── Nodes ──────────────────────────────────────────────────────────────
    graph.add_node("analyze_requirements",  analyze_requirements_node)
    graph.add_node("generate_basic_design", generate_basic_design_node)
    graph.add_node("generate_2d_layout",    generate_2d_layout_node)
    graph.add_node("generate_3d_model",     generate_3d_model_node)
    graph.add_node("compile_report",        compile_report_node)
    graph.add_node("error_handler",         error_handler_node)

    # ── Entry point ────────────────────────────────────────────────────────
    graph.set_entry_point("analyze_requirements")

    # ── Edges with error-check routing ─────────────────────────────────────
    def route_after(next_node: str):
        def _route(state: DesignState) -> str:
            return "error_handler" if state.get("errors") else next_node
        return _route

    graph.add_conditional_edges(
        "analyze_requirements",
        route_after("generate_basic_design"),
        {"generate_basic_design": "generate_basic_design", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "generate_basic_design",
        route_after("generate_2d_layout"),
        {"generate_2d_layout": "generate_2d_layout", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "generate_2d_layout",
        route_after("generate_3d_model"),
        {"generate_3d_model": "generate_3d_model", "error_handler": "error_handler"},
    )
    graph.add_conditional_edges(
        "generate_3d_model",
        route_after("compile_report"),
        {"compile_report": "compile_report", "error_handler": "error_handler"},
    )

    graph.add_edge("compile_report", END)
    graph.add_edge("error_handler",  END)

    return graph.compile()


# Singleton compiled graph
design_graph = build_design_graph()
