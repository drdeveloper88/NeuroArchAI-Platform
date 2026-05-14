# 🏛️ NeoArchAI

**Agentic House Architecture Design System**

Generate complete house architecture designs at three levels — Basic Design, 2D Floor Plans, and Interactive 3D Model — powered by LangGraph, CrewAI, FastAPI, and FastMCP.  
Everything is **free**: uses Groq (free tier LLM) or Ollama (local LLM) with a full algorithmic fallback requiring zero API keys.

---

## ✨ Features

| Level | Output | Technology |
|-------|--------|------------|
| **Basic Design** | Room schedule, materials, cost estimate, energy features | CrewAI 4-agent crew + algorithmic fallback |
| **2D Floor Plans** | Architectural drawings per floor (PNG + SVG, 180 DPI) | Matplotlib with door/window/stair symbols |
| **3D Model** | Interactive Plotly visualization with 4 camera presets | Plotly Mesh3d with colored rooms, roof shapes |
| **Report** | Self-contained HTML + PDF with all details | Jinja2 + fpdf2 |

**Pipeline stages** (LangGraph):
```
analyze_requirements → generate_basic_design → generate_2d_layout → generate_3d_model → compile_report
```

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/yourname/NeoArchAI.git
cd NeoArchAI
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set GROQ_API_KEY (free at console.groq.com)
```

No API key? Set `LLM_PROVIDER=none` in `.env` — the system uses the built-in algorithmic design engine.

### 3. Run

```bash
python main.py
```

Open **http://localhost:8000** in your browser.

---

## 🔑 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GROQ_API_KEY` | *(empty)* | Groq API key ([free tier](https://console.groq.com)) |
| `LLM_PROVIDER` | `groq` | `groq` / `ollama` / `none` |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Model name |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `APP_HOST` | `0.0.0.0` | FastAPI host |
| `APP_PORT` | `8000` | FastAPI port |
| `OUTPUT_DIR` | `output` | Directory for generated files |
| `DEBUG` | `false` | Enable hot reload |

---

## 🏗️ Architecture

```
NeoArchAI/
├── main.py                   # FastAPI app entry point
├── config.py                 # Configuration & LLM factory
├── mcp_server.py             # FastMCP tool server
├── requirements.txt
├── .env.example
│
├── models/
│   └── schemas.py            # Pydantic v2 models
│
├── graph/
│   ├── state.py              # LangGraph TypedDict state
│   ├── nodes.py              # 5 async pipeline nodes
│   └── design_graph.py       # Compiled StateGraph
│
├── agents/
│   └── design_crew.py        # CrewAI agents + algorithmic fallback
│
├── tools/
│   ├── floor_plan_2d.py      # Matplotlib floor plan renderer
│   ├── model_3d.py           # Plotly 3D model builder
│   └── report_gen.py         # HTML + PDF report generator
│
├── api/
│   └── routes.py             # FastAPI routes + SSE streaming
│
├── static/
│   └── index.html            # Single-page web UI
│
└── output/                   # Generated files per design_id
    └── {design_id}/
        ├── basic_design.json
        ├── floor_1.png / floor_1.svg
        ├── floor_2.png / floor_2.svg
        ├── model_3d.html
        ├── model_3d.json
        ├── report.html
        └── report.pdf
```

---

## 📡 API Reference

### Start a design
```http
POST /api/design
Content-Type: application/json

{
  "requirements": {
    "style": "modern",
    "total_area_sqft": 2500,
    "floors": 2,
    "bedrooms": 4,
    "bathrooms": 3,
    "has_garage": true,
    "has_garden": true,
    "budget_level": "standard",
    "climate": "temperate",
    "roof_type": "gable",
    "special_features": ["home office", "solar panels"]
  }
}
```
→ Returns `{ "design_id": "...", "status_url": "/api/design/{id}", ... }`

### Poll status
```http
GET /api/design/{design_id}
```

### SSE progress stream
```http
GET /api/design/{design_id}/stream
```
Emits `text/event-stream` events with `{ status, stage, progress }` until complete.

### Download files
```http
GET /api/files/{design_id}/floor_1.png
GET /api/files/{design_id}/model_3d.html
GET /api/files/{design_id}/report.html
GET /api/files/{design_id}/report.pdf
```

### Interactive docs
- Swagger UI: http://localhost:8000/docs
- ReDoc:       http://localhost:8000/redoc

---

## 🤖 MCP Server (for AI assistants)

NeoArchAI exposes its capabilities as MCP tools via FastMCP:

```bash
# Run standalone (stdio transport for Claude Desktop, Copilot, etc.)
python mcp_server.py
```

Available tools:
- `generate_house_design` – Start a design job
- `get_design_status` – Poll progress and results  
- `list_design_styles` – Available styles, budgets, climate zones
- `estimate_construction_cost` – Quick cost estimate

### Claude Desktop configuration

Add to `claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "neoarchai": {
      "command": "python",
      "args": ["path/to/NeoArchAI/mcp_server.py"]
    }
  }
}
```

---

## 🛠️ Tech Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Web Framework | FastAPI + Uvicorn | 0.115.5 |
| Agent Pipeline | LangGraph | 0.2.55 |
| Multi-agent Crew | CrewAI | 0.86.0 |
| LLM (free cloud) | Groq / llama-3.3-70b | - |
| LLM (local) | Ollama | any |
| 2D Drawings | Matplotlib | 3.9.3 |
| 3D Model | Plotly | 5.24.1 |
| Reports | fpdf2 + Jinja2 | 2.8.1 |
| MCP Server | FastMCP | 2.3.3 |

---

## 🆓 Completely Free

- **Groq** – Free tier: 14,400 requests/day, 6,000 tokens/min  
  Sign up at https://console.groq.com
- **Ollama** – Run LLMs locally for free  
  Install at https://ollama.ai
- **No paid APIs required** – the algorithmic fallback produces real designs without any LLM

---

## 📄 License

MIT License — see [LICENSE](LICENSE)
