"""NeoArchAI - HTML & PDF Report Generator

Produces a comprehensive architectural design report:
  - Cover page
  - Executive summary
  - Room schedule table
  - Materials specification
  - Cost estimate
  - Embedded 2D floor plan images
  - Link to interactive 3D model
"""
from __future__ import annotations
import base64
import json
from pathlib import Path
from typing import Any, Dict, List

from jinja2 import Template
from fpdf import FPDF

# ── HTML Report Template ──────────────────────────────────────────────────────
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{{ title }} – Architectural Design Report</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', sans-serif; background: #f5f5f5; color: #2c2c2c; }
  .container { max-width: 1100px; margin: 0 auto; padding: 24px; }
  .cover {
    background: linear-gradient(135deg, #1a252f 0%, #2c3e50 60%, #34495e 100%);
    color: white; padding: 60px 40px; border-radius: 12px; margin-bottom: 32px; text-align: center;
  }
  .cover h1 { font-size: 2.4rem; letter-spacing: 1px; margin-bottom: 8px; }
  .cover h2 { font-size: 1.1rem; font-weight: 300; opacity: 0.8; margin-bottom: 24px; }
  .cover .meta { display: flex; justify-content: center; gap: 32px; flex-wrap: wrap; }
  .cover .meta span { background: rgba(255,255,255,0.15); padding: 8px 16px;
    border-radius: 20px; font-size: 0.85rem; }
  .section { background: white; border-radius: 10px; padding: 28px; margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06); }
  .section h2 { font-size: 1.25rem; color: #2c3e50; border-bottom: 2px solid #3498db;
    padding-bottom: 8px; margin-bottom: 16px; }
  .summary p { line-height: 1.8; color: #444; }
  table { width: 100%; border-collapse: collapse; font-size: 0.88rem; }
  th { background: #2c3e50; color: white; padding: 10px 12px; text-align: left; }
  td { padding: 9px 12px; border-bottom: 1px solid #eee; }
  tr:hover td { background: #f8f9fa; }
  .color-dot { width: 14px; height: 14px; border-radius: 3px; display: inline-block; margin-right: 6px; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .card { background: #f8f9fa; border-radius: 8px; padding: 16px; }
  .card h3 { font-size: 0.95rem; color: #555; margin-bottom: 10px; }
  .card p, .card li { font-size: 0.88rem; color: #444; line-height: 1.7; }
  .card ul { padding-left: 18px; }
  .floor-plan-img { width: 100%; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.1);
    margin-bottom: 12px; }
  .cost-bar { height: 24px; border-radius: 4px; background: linear-gradient(90deg, #27ae60, #3498db);
    margin: 8px 0; display: flex; align-items: center; padding: 0 10px; color: white;
    font-size: 0.85rem; font-weight: 600; }
  .badge { display: inline-block; padding: 3px 10px; border-radius: 12px; font-size: 0.8rem;
    font-weight: 600; margin: 3px; }
  .badge-blue { background: #d6eaf8; color: #1a5276; }
  .badge-green { background: #d5f5e3; color: #1e8449; }
  .btn-3d { display: inline-block; background: linear-gradient(135deg, #3498db, #2980b9);
    color: white; padding: 12px 28px; border-radius: 6px; text-decoration: none;
    font-weight: 600; font-size: 0.95rem; margin-top: 12px; }
  .footer { text-align: center; color: #aaa; font-size: 0.8rem; margin-top: 32px; padding: 16px; }
  @media (max-width: 700px) { .grid-2 { grid-template-columns: 1fr; } }
</style>
</head>
<body>
<div class="container">

  <!-- Cover -->
  <div class="cover">
    <h1>{{ title }}</h1>
    <h2>Architectural Design Report  &bull;  NeoArchAI</h2>
    <div class="meta">
      <span>{{ style }}</span>
      <span>{{ area }} sq ft</span>
      <span>{{ floors }} Floor(s)</span>
      <span>{{ bedrooms }} Bed / {{ bathrooms }} Bath</span>
      <span>{{ budget }} Build</span>
    </div>
  </div>

  <!-- Executive Summary -->
  <div class="section summary">
    <h2>Executive Summary</h2>
    <p>{{ summary }}</p>
  </div>

  <!-- Room Schedule -->
  <div class="section">
    <h2>Room Schedule</h2>
    <table>
      <thead>
        <tr>
          <th>Room</th><th>Floor</th><th>Width (ft)</th>
          <th>Depth (ft)</th><th>Area (sq ft)</th>
        </tr>
      </thead>
      <tbody>
        {% for room in rooms %}
        <tr>
          <td>
            <span class="color-dot" style="background:{{ room.color }};"></span>
            {{ room.name }}
          </td>
          <td>{{ room.floor }}</td>
          <td>{{ "%.1f"|format(room.width) }}</td>
          <td>{{ "%.1f"|format(room.depth) }}</td>
          <td><strong>{{ "%.0f"|format(room.area) }}</strong></td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <!-- 2D Floor Plans -->
  <div class="section">
    <h2>2D Architectural Floor Plans</h2>
    {% for fp in floor_plans %}
    <h3 style="margin-bottom:8px; color:#34495e;">Floor {{ fp.floor_number }}</h3>
    {% if fp.image_b64 %}
    <img class="floor-plan-img" src="data:image/png;base64,{{ fp.image_b64 }}" alt="Floor {{ fp.floor_number }} Plan"/>
    {% endif %}
    <p style="font-size:0.82rem;color:#777;margin-bottom:20px;">
      Dimensions: {{ "%.1f"|format(fp.width_ft) }}' × {{ "%.1f"|format(fp.depth_ft) }}'
      &nbsp;|&nbsp; Rooms: {{ fp.rooms|join(', ') }}
    </p>
    {% endfor %}
  </div>

  <!-- 3D Model -->
  <div class="section" style="text-align:center;">
    <h2>3D Visualization Model</h2>
    <p style="color:#555; margin-bottom:12px;">{{ scene_summary }}</p>
    <a class="btn-3d" href="{{ model_3d_url }}" target="_blank">🏠 Open Interactive 3D Model</a>
  </div>

  <!-- Materials & Structure -->
  <div class="section">
    <h2>Materials & Structural Specification</h2>
    <div class="grid-2">
      <div class="card">
        <h3>Construction Materials</h3>
        <ul>
          {% for k, v in materials.items() %}
          <li><strong>{{ k.replace('_',' ').title() }}:</strong> {{ v }}</li>
          {% endfor %}
        </ul>
      </div>
      <div class="card">
        <h3>Structural Notes</h3>
        <ul>
          {% for note in structural_notes %}
          <li>{{ note }}</li>
          {% endfor %}
        </ul>
      </div>
    </div>
  </div>

  <!-- Energy Features -->
  <div class="section">
    <h2>Energy & Sustainability Features</h2>
    {% for feat in energy_features %}
    <span class="badge badge-green">✓ {{ feat }}</span>
    {% endfor %}
  </div>

  <!-- Cost Estimate -->
  <div class="section">
    <h2>Estimated Construction Cost</h2>
    <div class="cost-bar" style="width:100%;">
      ${{ "{:,.0f}".format(cost_low) }} – ${{ "{:,.0f}".format(cost_high) }} {{ cost_currency }}
    </div>
    <p style="font-size:0.85rem;color:#666;margin-top:8px;">{{ cost_note }}</p>
  </div>

  <!-- Design Rationale -->
  <div class="section">
    <h2>Design Rationale</h2>
    <p style="line-height:1.8;color:#444;">{{ design_rationale }}</p>
  </div>

  <div class="footer">
    Generated by <strong>NeoArchAI</strong> – Agentic House Architecture Design System<br>
    Design ID: {{ design_id }}
  </div>
</div>
</body>
</html>"""


# ── PDF Generator ─────────────────────────────────────────────────────────────

class DesignPDF(FPDF):
    def __init__(self, title: str):
        super().__init__()
        self._doc_title = title

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(44, 62, 80)
        self.cell(0, 8, self._doc_title, align="L")
        self.set_font("Helvetica", "", 9)
        self.set_text_color(120, 120, 120)
        self.cell(0, 8, "NeoArchAI Design Report", align="R", ln=True)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _generate_pdf(data: dict, design_dir: Path) -> Path:
    """Generate a multi-page PDF report."""
    pdf = DesignPDF(data["title"])
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # Cover
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_text_color(44, 62, 80)
    pdf.ln(10)
    pdf.multi_cell(0, 12, data["title"], align="C")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.multi_cell(0, 8,
        f"Style: {data['style']}  |  {data['area']} sq ft  |  "
        f"{data['floors']} floor(s)  |  {data['bedrooms']}BD/{data['bathrooms']}BA",
        align="C")
    pdf.ln(8)

    # Summary
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Executive Summary", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    pdf.multi_cell(0, 6, data["summary"])
    pdf.ln(6)

    # Room schedule
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Room Schedule", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(44, 62, 80)
    pdf.set_text_color(255, 255, 255)
    for col, w in [("Room", 60), ("Floor", 20), ("Width", 30), ("Depth", 30), ("Area", 30)]:
        pdf.cell(w, 8, col, border=0, fill=True, align="C")
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(40, 40, 40)
    for i, room in enumerate(data["rooms"]):
        fill = i % 2 == 0
        pdf.set_fill_color(248, 249, 250)
        pdf.cell(60, 7, room.get("name", ""), border=0, fill=fill)
        pdf.cell(20, 7, str(room.get("floor", 1)), border=0, fill=fill, align="C")
        pdf.cell(30, 7, f"{room.get('width',0):.1f}", border=0, fill=fill, align="C")
        pdf.cell(30, 7, f"{room.get('depth',0):.1f}", border=0, fill=fill, align="C")
        pdf.cell(30, 7, f"{room.get('area',0):.0f} sqft", border=0, fill=fill, align="C")
        pdf.ln()
    pdf.ln(6)

    # Materials
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Materials Specification", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(60, 60, 60)
    for k, v in data["materials"].items():
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(45, 6, k.replace("_", " ").title() + ":", border=0)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(0, 6, str(v))
    pdf.ln(4)

    # Cost
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(44, 62, 80)
    pdf.cell(0, 8, "Cost Estimate", ln=True)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 12)
    pdf.set_text_color(39, 174, 96)
    pdf.cell(0, 8,
        f"${data['cost_low']:,.0f} – ${data['cost_high']:,.0f} {data['cost_currency']}",
        ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(0, 6, data["cost_note"])

    pdf_path = design_dir / "report.pdf"
    pdf.output(str(pdf_path))
    return pdf_path


# ── Public API ────────────────────────────────────────────────────────────────

def generate_report(data: dict, design_dir: Path) -> str:
    """
    Generate HTML + PDF reports.  Returns the HTML file URL string.
    """
    design_id   = data["design_id"]
    req         = data["requirements"]
    bd          = data["basic_design"]
    floor_plans = data.get("floor_plans", [])
    model_3d    = data.get("model_3d", {})
    summary     = data.get("summary", "")

    # Embed floor plan images as base64 for self-contained HTML
    fp_with_b64 = []
    for fp in floor_plans:
        fp_copy = dict(fp)
        png_path = design_dir / f"floor_{fp['floor_number']}.png"
        if png_path.exists():
            b64 = base64.b64encode(png_path.read_bytes()).decode()
            fp_copy["image_b64"] = b64
        else:
            fp_copy["image_b64"] = ""
        fp_with_b64.append(fp_copy)

    materials       = bd.get("materials", {})
    structural_notes= bd.get("structural_notes", [])
    energy_features = bd.get("energy_features", [])
    cost            = bd.get("cost_estimate", {})

    # Render HTML
    tmpl = Template(HTML_TEMPLATE)
    html = tmpl.render(
        title           = bd.get("title", "Custom Residence"),
        style           = req.get("style", "modern").title(),
        area            = f"{bd.get('total_area_sqft', 2000):.0f}",
        floors          = req.get("floors", 1),
        bedrooms        = req.get("bedrooms", 3),
        bathrooms       = req.get("bathrooms", 2),
        budget          = req.get("budget_level", "standard").title(),
        summary         = summary,
        rooms           = bd.get("rooms", []),
        floor_plans     = fp_with_b64,
        scene_summary   = model_3d.get("scene_summary", ""),
        model_3d_url    = f"/api/files/{design_id}/model_3d.html",
        materials       = materials,
        structural_notes= structural_notes,
        energy_features = energy_features,
        cost_low        = cost.get("low", 0),
        cost_high       = cost.get("high", 0),
        cost_currency   = cost.get("currency", "USD"),
        cost_note       = cost.get("note", ""),
        design_rationale= bd.get("design_rationale", ""),
        design_id       = design_id,
    )

    html_path = design_dir / "report.html"
    html_path.write_text(html, encoding="utf-8")

    # Generate PDF
    pdf_data = {
        "title":         bd.get("title", "Residence"),
        "style":         req.get("style", "modern").title(),
        "area":          bd.get("total_area_sqft", 2000),
        "floors":        req.get("floors", 1),
        "bedrooms":      req.get("bedrooms", 3),
        "bathrooms":     req.get("bathrooms", 2),
        "summary":       summary,
        "rooms":         bd.get("rooms", []),
        "materials":     materials,
        "structural_notes": structural_notes,
        "energy_features":  energy_features,
        "cost_low":      cost.get("low", 0),
        "cost_high":     cost.get("high", 0),
        "cost_currency": cost.get("currency", "USD"),
        "cost_note":     cost.get("note", ""),
    }
    try:
        _generate_pdf(pdf_data, design_dir)
    except Exception as e:
        # PDF generation is best-effort
        import logging
        logging.getLogger(__name__).warning("PDF generation failed: %s", e)

    return f"/api/files/{design_id}/report.html"
