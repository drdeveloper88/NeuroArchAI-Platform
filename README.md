# 🏛️ NeuroArchAI Platform

> **AI-Powered Autonomous Architecture Design System**  
> Generate complete residential house designs with 2D floor plans and interactive 3D models using multi-agent AI orchestration, LangGraph pipelines, and advanced visualization technologies.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111%2B-00a36d)](https://fastapi.tiangolo.com/)
[![Made with LangGraph](https://img.shields.io/badge/Orchestration-LangGraph-621a4a)](https://langchain-ai.github.io/langgraph/)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture](#system-architecture)
- [Project Structure](#project-structure)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [MCP Server Integration](#mcp-server-integration)
- [Development Guide](#development-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**NeuroArchAI Platform** is an intelligent architectural design system that automates residential house design generation across three progressive levels:

1. **Basic Design** – Conceptual room layouts, material specifications, cost estimates, and energy efficiency features
2. **2D Floor Plans** – Professional architectural drawings with precise dimensions, symbols, and renderings (PNG + SVG)
3. **3D Interactive Model** – Fully interactive 3D visualization with multiple camera presets and room-level detail

The platform is built with:
- **Completely free** – Uses Groq (free tier) or Ollama (local LLM) with intelligent fallback
- **Async-first** – FastAPI with Server-Sent Events for real-time progress streaming
- **AI-native** – Multi-agent CrewAI orchestrated by LangGraph state machine
- **Production-ready** – Type-safe Pydantic models, comprehensive error handling, scalable architecture

---

## ✨ Key Features

| Feature | Details |
|---------|---------|
| **Multi-Level Design** | Basic → 2D Plans → 3D Model with progressive complexity |
| **LLM Agnostic** | Groq (free), Ollama (local), or algorithmic fallback (no API needed) |
| **Async Processing** | Real-time SSE streaming, non-blocking design generation |
| **Report Generation** | Self-contained HTML + PDF reports with all design specifications |
| **MCP Integration** | Expose capabilities to Claude Desktop, Copilot, and other AI assistants |
| **Professional Output** | High-DPI renderings (180 DPI), SVG exports, interactive 3D visualization |
| **Type-Safe** | Full Pydantic v2 validation and static typing throughout |
| **RESTful API** | Complete Swagger/OpenAPI documentation, easy integration |

---

## 🛠️ Technology Stack

### Core Framework & Web
| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | 0.115.5+ | Modern async web framework |
| **Uvicorn** | 0.29.0+ | ASGI application server |
| **Python** | 3.10+ | Core language |
| **Pydantic** | 2.7.0+ | Data validation & serialization |

### AI & Orchestration
| Technology | Version | Purpose |
|-----------|---------|---------|
| **LangGraph** | 0.2.55+ | Agentic workflow orchestration & state management |
| **LangChain** | 0.3.0+ | LLM abstraction and tool integration |
| **CrewAI** | 0.86.0+ | Multi-agent framework for specialized tasks |
| **FastMCP** | 2.3.3+ | Model Context Protocol server |

### LLM Providers
| Provider | Type | Setup |
|----------|------|-------|
| **Groq** | Cloud (Free) | Free tier: 14,400 requests/day, 6,000 tokens/min |
| **Ollama** | Local | Run LLMs entirely on your machine |
| **Algorithmic Fallback** | Built-in | Zero dependencies, no API keys required |

### Visualization & Rendering
| Technology | Version | Purpose |
|-----------|---------|---------|
| **Matplotlib** | 3.9.3+ | 2D floor plan rendering with custom symbols |
| **Plotly** | 5.24.1+ | Interactive 3D model visualization |
| **NumPy** | 1.26.0+ | Numerical computations |
| **Shapely** | 2.0.0+ | Geometric operations |
| **SVGwrite** | 1.4.3+ | Scalable vector graphics generation |

### Document Generation
| Technology | Version | Purpose |
|-----------|---------|---------|
| **fpdf2** | 2.8.1+ | PDF report generation |
| **Jinja2** | 3.1.0+ | HTML templating |

### Utilities
| Technology | Version | Purpose |
|-----------|---------|---------|
| **python-dotenv** | 1.0.0+ | Environment configuration |
| **httpx** | 0.27.0+ | Async HTTP client |
| **sse-starlette** | 1.8.0+ | Server-Sent Events |

---

## 🏗️ System Architecture

### High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     Client Layer                                │
│  ┌─────────────────┐  ┌──────────────┐  ┌─────────────────┐    │
│  │  Web UI (HTML)  │  │  REST API    │  │  MCP Clients    │    │
│  │  (SPA)          │  │  (Swagger)   │  │  (Claude, etc)  │    │
│  └────────┬────────┘  └──────┬───────┘  └────────┬────────┘    │
│           │                  │                   │              │
└───────────┼──────────────────┼───────────────────┼──────────────┘
            │                  │                   │
┌───────────┼──────────────────┼───────────────────┼──────────────┐
│           ▼                  ▼                   ▼              │
│  ┌──────────────────────────────────────────────────┐           │
│  │      FastAPI Application Server (Uvicorn)       │           │
│  │  • Route handlers with SSE streaming            │           │
│  │  • Request validation & error handling          │           │
│  │  • CORS & security middleware                   │           │
│  └──────────────────┬───────────────────────────────┘           │
│                    │                                           │
│  ┌─────────────────┴────────────────────────────────────┐      │
│  │   LangGraph State Machine (design_graph.py)         │      │
│  │   ┌──────────────────────────────────────────────┐   │      │
│  │   │  Pipeline Stages (TypedDict State):          │   │      │
│  │   │  1. analyze_requirements                    │   │      │
│  │   │  2. generate_basic_design                   │   │      │
│  │   │  3. generate_2d_layout                      │   │      │
│  │   │  4. generate_3d_model                       │   │      │
│  │   │  5. compile_report                          │   │      │
│  │   └──────────────────────────────────────────────┘   │      │
│  └──────────────────┬─────────────────────────────────┘       │
│                    │                                           │
│  ┌─────────────────┴────────────────────────────────────┐      │
│  │   Agent Execution Layer (agents/design_crew.py)     │      │
│  │   ┌──────────────────────────────────────────────┐   │      │
│  │   │  CrewAI Multi-Agent Framework:              │   │      │
│  │   │  • Architect Agent → Room planning          │   │      │
│  │   │  • Layout Engineer → 2D optimization        │   │      │
│  │   │  • Materials Specialist → Specs & costs     │   │      │
│  │   │  • Energy Analyst → Efficiency features     │   │      │
│  │   │  • Fallback: Algorithmic engine (no API)   │   │      │
│  │   └──────────────────────────────────────────────┘   │      │
│  └──────────────────┬─────────────────────────────────┘       │
│                    │                                           │
│  ┌─────────────────┴────────────────────────────────────┐      │
│  │   LLM Abstraction & Routing Layer                    │      │
│  │   ┌────────────────┐  ┌─────────────────────────┐    │      │
│  │   │  LangChain     │  │  LangChain-Groq or      │    │      │
│  │   │  LLM Router    │  │  LangChain-Ollama       │    │      │
│  │   └────────────────┘  └─────────────────────────┘    │      │
│  └──────────────────┬─────────────────────────────────┘       │
│                    │                                           │
└────────────────────┼───────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
    ┌───▼───┐   ┌───▼───┐   ┌───▼─────┐
    │ Groq  │   │Ollama │   │Algorithm│
    │Cloud  │   │Local  │   │Fallback │
    │(Free) │   │(Free) │   │(No API) │
    └───────┘   └───────┘   └─────────┘
        
┌─────────────────────────────────────────────────────────────────┐
│                   Tool & Output Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ 2D Floor Plans  │  │ 3D Models       │  │ Report          │ │
│  │ (Matplotlib)    │  │ (Plotly)        │  │ (fpdf2+Jinja2)  │ │
│  │ PNG + SVG       │  │ HTML (180 DPI)  │  │ HTML + PDF      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │          File Storage (output/{design_id}/)                 ││
│  │  ├── basic_design.json                                      ││
│  │  ├── floor_1.png / floor_1.svg                              ││
│  │  ├── floor_2.png / floor_2.svg                              ││
│  │  ├── model_3d.html                                          ││
│  │  ├── model_3d.json                                          ││
│  │  ├── report.html                                            ││
│  │  └── report.pdf                                             ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. Client Request (POST /api/design)
   ↓
2. FastAPI validates & creates design_id
   ↓
3. SSE stream starts (GET /api/design/{id}/stream)
   ↓
4. LangGraph invokes state machine:
   
   Input: Requirements (TypedDict)
   ├─ analyze_requirements (node)
   │  ├─ Call CrewAI Architect Agent
   │  └─ Emit: "Analyzing requirements..." → 20%
   │
   ├─ generate_basic_design (node)
   │  ├─ Call CrewAI Design Crew
   │  └─ Emit: "Generating basic design..." → 40%
   │
   ├─ generate_2d_layout (node)
   │  ├─ Call floor_plan_2d tool (Matplotlib)
   │  └─ Emit: "Rendering 2D plans..." → 60%
   │
   ├─ generate_3d_model (node)
   │  ├─ Call model_3d tool (Plotly)
   │  └─ Emit: "Building 3D model..." → 80%
   │
   └─ compile_report (node)
      ├─ Call report_gen tool (Jinja2 + fpdf2)
      └─ Emit: "Generating report..." → 100%
   
   Output: Complete design (TypedDict with all results)
   ↓
5. Results written to output/{design_id}/
   ↓
6. JSON response sent to client
   ↓
7. Client downloads files via /api/files/{id}/{filename}
```

---

## 📁 Project Structure

```
NeuroArchAI-Platform/
│
├── 📄 README.md                          # This file
├── 📄 LICENSE                            # MIT License
├── 📄 requirements.txt                   # Python dependencies
├── 📄 .env.example                       # Environment template
│
├── 🐍 main.py                            # FastAPI application entry point
│                                        # • Starts Uvicorn server
│                                        # • Initializes middleware
│
├── 🐍 config.py                          # Configuration management
│                                        # • Environment loading
│                                        # • LLM factory pattern
│                                        # • Settings validation
│
├── 🐍 mcp_server.py                      # Model Context Protocol server
│                                        # • Exposes design tools to AI assistants
│                                        # • Stdio transport for Claude Desktop
│
├── 📁 models/                            # Data models
│   ├── __init__.py
│   └── schemas.py                        # Pydantic v2 models
│                                        # • DesignRequirements
│                                        # • BasicDesignOutput
│                                        # • Floor3DData
│                                        # • DesignState (TypedDict)
│
├── 📁 graph/                             # LangGraph orchestration
│   ├── __init__.py
│   ├── state.py                          # TypedDict state definition
│                                        # • Input: requirements, design_id, metadata
│                                        # • Output: all_designs, all_plans, all_3d
│                                        # • Metadata: current_stage, progress %
│   │
│   ├── nodes.py                          # Async node implementations
│                                        # • analyze_requirements() → CrewAI
│                                        # • generate_basic_design() → CrewAI
│                                        # • generate_2d_layout() → Matplotlib
│                                        # • generate_3d_model() → Plotly
│                                        # • compile_report() → fpdf2+Jinja2
│   │
│   └── design_graph.py                   # Compiled StateGraph
│                                        # • Graph construction & routing
│                                        # • Error edge handling
│
├── 📁 agents/                            # CrewAI agent definitions
│   ├── __init__.py
│   └── design_crew.py                    # Multi-agent orchestration
│                                        # • Architect Agent
│                                        # • Layout Engineer Agent
│                                        # • Materials Specialist Agent
│                                        # • Energy Analyst Agent
│                                        # • Algorithmic fallback engine
│
├── 📁 tools/                             # Tool implementations
│   ├── __init__.py
│   │
│   ├── floor_plan_2d.py                  # 2D floor plan generation
│                                        # • Matplotlib rendering
│                                        # • Door/window symbols
│                                        # • Dimension annotations
│                                        # • PNG & SVG export (180 DPI)
│   │
│   ├── model_3d.py                       # 3D model generation
│                                        # • Plotly Mesh3d visualization
│                                        # • Room coloring
│                                        # • Roof shapes & camera presets
│                                        # • Interactive HTML output
│   │
│   └── report_gen.py                     # Report generation
│                                        # • Jinja2 templating
│                                        # • HTML with embedded styles
│                                        # • PDF export via fpdf2
│                                        # • Design summary & specifications
│
├── 📁 api/                               # API routes & endpoints
│   ├── __init__.py
│   └── routes.py                         # FastAPI endpoints
│                                        # • POST /api/design
│                                        # • GET /api/design/{id}
│                                        # • GET /api/design/{id}/stream (SSE)
│                                        # • GET /api/files/{id}/{filename}
│                                        # • GET /api/styles
│
├── 📁 static/                            # Frontend assets
│   ├── index.html                        # Single-page web application
│                                        # • React/Vue or vanilla JS
│                                        # • Design form
│                                        # • SSE progress display
│                                        # • File downloads
│   │
│   ├── css/                              # Stylesheets
│   │   └── style.css
│   │
│   └── js/                               # Frontend logic
│       └── app.js
│
├── 📁 output/                            # Generated design outputs
│   └── {design_id}/                      # Organized per design
│       ├── basic_design.json             # Design specifications
│       ├── floor_1.png                   # Floor plan PNG
│       ├── floor_1.svg                   # Floor plan SVG
│       ├── floor_2.png
│       ├── floor_2.svg
│       ├── model_3d.html                 # Interactive 3D model
│       ├── model_3d.json                 # 3D data (for archival)
│       ├── report.html                   # HTML report
│       └── report.pdf                    # PDF report
│
└── 📁 tests/                             # Test suite (optional)
    ├── __init__.py
    ├── test_graph.py                     # LangGraph pipeline tests
    ├── test_agents.py                    # CrewAI agent tests
    ├── test_tools.py                     # Tool unit tests
    └── test_api.py                       # API integration tests
```

---

## 🚀 Installation & Setup

### Prerequisites

- **Python 3.10+** ([Download](https://www.python.org/downloads/))
- **Git** ([Download](https://git-scm.com/))
- **pip** (comes with Python)
- **(Optional) Ollama** for local LLM ([Download](https://ollama.ai))

### Step 1: Clone Repository

```bash
git clone https://github.com/drdeveloper88/NeuroArchAI-Platform.git
cd NeuroArchAI-Platform
```

### Step 2: Create Virtual Environment

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows:**
```bash
python -m venv .venv
.venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

**Optional: For development with testing:**
```bash
pip install -r requirements.txt pytest pytest-asyncio httpx
```

### Step 4: Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings (see [Configuration](#configuration) section).

### Step 5: Verify Installation

```bash
python -c "import fastapi, langgraph, crewai, plotly; print('✅ All dependencies installed!')"
```

---

## ⚙️ Configuration

### Environment Variables (.env)

```bash
# ============================================
# LLM CONFIGURATION
# ============================================

# Groq API Key (free tier at https://console.groq.com)
# Leave empty to disable Groq
GROQ_API_KEY=your_groq_api_key_here

# LLM Provider: groq, ollama, or none (algorithmic fallback)
LLM_PROVIDER=groq

# Model name for Groq (default: llama-3.3-70b-versatile)
LLM_MODEL=llama-3.3-70b-versatile

# Ollama configuration (if LLM_PROVIDER=ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# ============================================
# APPLICATION SERVER
# ============================================

# FastAPI host binding
APP_HOST=0.0.0.0

# FastAPI port
APP_PORT=8000

# Enable hot reload in development
DEBUG=false

# ============================================
# OUTPUT & STORAGE
# ============================================

# Directory for generated design files
OUTPUT_DIR=output

# Max file size for uploads (in MB)
MAX_UPLOAD_SIZE=50

# ============================================
# LOGGING & MONITORING
# ============================================

# Log level: DEBUG, INFO, WARNING, ERROR
LOG_LEVEL=INFO

# Enable detailed request logging
LOG_REQUESTS=false
```

### Provider Selection

**Option 1: Use Groq (Recommended for Quick Start)**
```bash
LLM_PROVIDER=groq
GROQ_API_KEY=your_key_from_console.groq.com
```

**Option 2: Use Ollama (Local & Private)**
```bash
LLM_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
```
Then run: `ollama run llama2` in another terminal.

**Option 3: Use Algorithmic Fallback (No API)**
```bash
LLM_PROVIDER=none
```

---

## 🏃 Quick Start

### Start the Application

```bash
python main.py
```

You'll see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Press CTRL+C to quit
```

### Access the Web UI

Open your browser: **http://localhost:8000**

Fill the design form:
- **Style:** Modern, Traditional, Contemporary, etc.
- **Total Area:** 2500 sqft
- **Floors:** 2
- **Bedrooms:** 4
- **Bathrooms:** 3
- **Special Features:** Home office, Solar panels, etc.

Click **Generate Design** and watch real-time progress via SSE streaming.

### Download Results

Once complete, download:
- `floor_1.png` / `floor_1.svg` – 2D floor plans
- `model_3d.html` – Interactive 3D visualization
- `report.html` / `report.pdf` – Complete design report

### View API Documentation

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 📡 API Reference

### 1. Create a Design

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

**Response (202 Accepted):**
```json
{
  "design_id": "design_1726234561",
  "status": "processing",
  "created_at": "2026-05-14T19:09:54Z",
  "status_url": "/api/design/design_1726234561",
  "stream_url": "/api/design/design_1726234561/stream"
}
```

### 2. Get Design Status

```http
GET /api/design/{design_id}
```

**Response (200 OK):**
```json
{
  "design_id": "design_1726234561",
  "status": "completed",
  "progress": 100,
  "current_stage": "compile_report",
  "results": {
    "basic_design": { ... },
    "floor_plans": [...],
    "model_3d": { ... },
    "report": { ... }
  },
  "files": {
    "basic_design_json": "/api/files/design_1726234561/basic_design.json",
    "floor_1_png": "/api/files/design_1726234561/floor_1.png",
    "model_3d_html": "/api/files/design_1726234561/model_3d.html",
    "report_pdf": "/api/files/design_1726234561/report.pdf"
  }
}
```

### 3. Stream Progress (SSE)

```http
GET /api/design/{design_id}/stream
Accept: text/event-stream
```

**Response Stream:**
```
event: progress
data: {"status": "processing", "stage": "analyze_requirements", "progress": 20}

event: progress
data: {"status": "processing", "stage": "generate_basic_design", "progress": 40}

event: progress
data: {"status": "processing", "stage": "generate_2d_layout", "progress": 60}

event: progress
data: {"status": "processing", "stage": "generate_3d_model", "progress": 80}

event: progress
data: {"status": "processing", "stage": "compile_report", "progress": 100}

event: complete
data: {"status": "completed", "design_id": "design_1726234561"}
```

### 4. Download Generated Files

```http
GET /api/files/{design_id}/{filename}
```

**Available files:**
- `basic_design.json` – Design specifications
- `floor_1.png`, `floor_1.svg` – Floor plans
- `model_3d.html` – Interactive 3D
- `report.html`, `report.pdf` – Reports

### 5. List Available Styles

```http
GET /api/styles
```

**Response:**
```json
{
  "styles": ["modern", "traditional", "contemporary", "rustic"],
  "budgets": ["economy", "standard", "premium"],
  "climates": ["tropical", "temperate", "arid", "cold"],
  "roof_types": ["gable", "hip", "flat", "gambrel"]
}
```

---

## 🤖 MCP Server Integration

### What is MCP?

The **Model Context Protocol (MCP)** enables AI assistants (Claude, Copilot, etc.) to use your tools directly.

### Run MCP Server

```bash
python mcp_server.py
```

Output:
```
Stdio transport initialized. Ready for Claude Desktop...
```

### Configure Claude Desktop

Edit `~/.config/Claude/claude_desktop_config.json` (macOS/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "neoarchai": {
      "command": "python",
      "args": ["/path/to/NeuroArchAI-Platform/mcp_server.py"]
    }
  }
}
```

Restart Claude Desktop. You'll see "NeuroArchAI" in the available tools panel.

### Available MCP Tools

1. **generate_house_design**
   - Start an async design job
   - Returns: `design_id`, status URL

2. **get_design_status**
   - Poll progress and retrieve results
   - Returns: Current stage, progress %, results when done

3. **list_design_styles**
   - View available design options
   - Returns: Styles, budgets, climates, roof types

4. **estimate_construction_cost**
   - Quick cost estimate based on specifications
   - Returns: Total cost, cost per sqft, breakdown

### Example Claude Conversation

```
You: "Generate a modern 3000 sqft 3-bedroom house design with solar panels"

Claude (using MCP): 
Calling: generate_house_design({
  "style": "modern",
  "total_area_sqft": 3000,
  "bedrooms": 3,
  "special_features": ["solar panels"]
})

Result: Design ID: design_1726234561
Status: https://localhost:8000/api/design/design_1726234561

[Claude polls for completion every 5 seconds...]

"Your design is ready! Here's what was generated:
- 3-floor layout with open concept
- 3 bedrooms, 2.5 bathrooms
- Solar panel array on south-facing roof
- Modern minimalist aesthetic
- Estimated cost: $450,000

You can download the 3D model and floor plans at:"
```

---

## 💻 Development Guide

### Project Setup for Contributors

```bash
# Clone & setup
git clone https://github.com/drdeveloper88/NeuroArchAI-Platform.git
cd NeuroArchAI-Platform
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
pip install -r requirements.txt pytest pytest-asyncio
```

### Running Tests

```bash
# Run all tests
pytest

# With coverage
pytest --cov=.

# Specific test file
pytest tests/test_graph.py -v

# Watch mode (requires pytest-watch)
ptw
```

### Adding a New Design Feature

1. **Define Pydantic model** in `models/schemas.py`
2. **Create agent** in `agents/design_crew.py` if using CrewAI
3. **Create tool** in `tools/` (e.g., `tools/new_feature.py`)
4. **Add node** in `graph/nodes.py` calling the tool
5. **Update StateGraph** in `graph/design_graph.py` with new edge
6. **Add API endpoint** in `api/routes.py` if needed
7. **Write tests** in `tests/`

### Code Style & Best Practices

```bash
# Format code
pip install black isort
black .
isort .

# Lint
pip install flake8 pylint
flake8 . --max-line-length=120
pylint graph/ agents/ tools/ api/

# Type checking
pip install mypy
mypy . --strict
```

### Debugging LangGraph Pipeline

```python
# In nodes.py, add:
from langchain_core.runnables import RunnableConfig

async def your_node(state: DesignState, config: RunnableConfig) -> dict:
    print(f"🔍 Debug: Current state = {state}")
    print(f"🔍 Debug: Config metadata = {config.metadata if config else 'None'}")
    # ... rest of implementation
```

### Async Patterns

All I/O operations must be async:

```python
# ✅ Correct
async def my_node(state: DesignState) -> dict:
    result = await some_async_function()
    return {"key": result}

# ❌ Wrong
def my_node(state: DesignState) -> dict:
    result = blocking_call()  # Will hang!
    return {"key": result}
```

---

## 🐛 Troubleshooting

### Issue: "GROQ_API_KEY not found"

**Solution:**
```bash
# Verify .env file exists
ls -la .env

# Check key format
cat .env | grep GROQ_API_KEY

# Get free key at https://console.groq.com
```

### Issue: Ollama connection refused

**Solution:**
```bash
# Start Ollama in another terminal
ollama serve

# Verify connection
curl http://localhost:11434/api/tags

# Or use Groq instead by changing LLM_PROVIDER=groq
```

### Issue: "Port 8000 already in use"

**Solution:**
```bash
# Use different port
APP_PORT=8001 python main.py

# Or kill existing process
# macOS/Linux
lsof -ti:8000 | xargs kill -9

# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Issue: Out of memory on 3D model generation

**Solution:**
```bash
# Reduce model complexity in config.py
3D_MESH_RESOLUTION = 1000  # Default 2000
3D_VERTEX_LIMIT = 50000    # Default 100000
```

### Issue: Slow PDF generation

**Solution:**
```bash
# Use HTML report instead of PDF for development
# PDF generation scales with report complexity
```

### Enable Debug Logging

```bash
DEBUG=true LOG_LEVEL=DEBUG python main.py
```

---

## 🤝 Contributing

We welcome contributions! Here's how:

1. **Fork** the repository
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Write tests** for your changes
4. **Format code**: `black . && isort .`
5. **Commit**: `git commit -m 'Add amazing feature'`
6. **Push**: `git push origin feature/amazing-feature`
7. **Open Pull Request** with description

### Contribution Areas

- 🐛 **Bug fixes** – Report issues, submit fixes
- ✨ **Features** – New design options, agents, tools
- 📚 **Documentation** – Examples, guides, comments
- 🧪 **Tests** – Increase coverage
- 🚀 **Performance** – Optimization suggestions

---

## 📄 License

MIT License – See [LICENSE](LICENSE) file

**Summary:** Free for personal & commercial use. No attribution required (but appreciated!).

---

## 🔗 Resources & Links

### Documentation
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [CrewAI Documentation](https://docs.crewai.com/)
- [Groq Console](https://console.groq.com)
- [Ollama Docs](https://ollama.ai)

### Related Projects
- [LangChain](https://github.com/langchain-ai/langchain)
- [CrewAI](https://github.com/joaomdmoura/crewai)
- [Plotly](https://plotly.com/)
- [FastAPI](https://github.com/tiangolo/fastapi)

### Getting Help
- 📖 Check [Troubleshooting](#troubleshooting) section
- 💬 Open an [GitHub Issue](https://github.com/drdeveloper88/NeuroArchAI-Platform/issues)
- 🐛 Report bugs with full error logs
- 💡 Request features with use cases

---

## 👨‍💻 Author

**Dr. Developer** (@drdeveloper88)
- GitHub: [@drdeveloper88](https://github.com/drdeveloper88)
- Email: [your-email@example.com]

---

<div align="center">

**[⬆ Back to Top](#-neuroarchai-platform)**

Made with ❤️ using LangGraph, FastAPI, and AI agents.

</div>
