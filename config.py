"""NeoArchAI - Configuration Module"""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ─── LLM Settings ──────────────────────────────────────────────────────────────
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
TOGETHER_API_KEY: str = os.getenv("TOGETHER_API_KEY", "")
COHERE_API_KEY: str = os.getenv("COHERE_API_KEY", "")
# Generic OpenAI-compatible endpoint (LM Studio, vLLM, Anyscale, etc.)
OPENAI_COMPAT_BASE_URL: str = os.getenv("OPENAI_COMPAT_BASE_URL", "")
OPENAI_COMPAT_API_KEY: str = os.getenv("OPENAI_COMPAT_API_KEY", "none")
LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "groq")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

# ─── App Settings ──────────────────────────────────────────────────────────────
APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT: int = int(os.getenv("APP_PORT", "8080"))
OUTPUT_DIR: Path = Path(os.getenv("OUTPUT_DIR", "output"))
MCP_PORT: int = int(os.getenv("MCP_PORT", "8001"))
DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

# Ensure output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def get_llm():
    """Return configured LangChain LLM instance, or None if unavailable."""

    # ── Groq (free tier: console.groq.com) ───────────────────────────────────
    if LLM_PROVIDER == "groq" and GROQ_API_KEY:
        try:
            from langchain_groq import ChatGroq
            return ChatGroq(
                api_key=GROQ_API_KEY,
                model=LLM_MODEL,
                temperature=0.7,
                max_tokens=4096,
            )
        except ImportError:
            print("Warning: langchain-groq not installed.")

    # ── Google Gemini (free tier: aistudio.google.com) ───────────────────────
    elif LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(
                google_api_key=GEMINI_API_KEY,
                model=LLM_MODEL or "gemini-1.5-flash",
                temperature=0.7,
                max_output_tokens=4096,
            )
        except ImportError:
            print("Warning: langchain-google-genai not installed. Run: pip install langchain-google-genai")

    # ── OpenAI ────────────────────────────────────────────────────────────────
    elif LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=OPENAI_API_KEY,
                model=LLM_MODEL or "gpt-4o-mini",
                temperature=0.7,
                max_tokens=4096,
            )
        except ImportError:
            print("Warning: langchain-openai not installed. Run: pip install langchain-openai")

    # ── Together AI (free credits: api.together.xyz) ─────────────────────────
    elif LLM_PROVIDER == "together" and TOGETHER_API_KEY:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=TOGETHER_API_KEY,
                base_url="https://api.together.xyz/v1",
                model=LLM_MODEL or "meta-llama/Llama-3-70b-chat-hf",
                temperature=0.7,
                max_tokens=4096,
            )
        except ImportError:
            print("Warning: langchain-openai not installed. Run: pip install langchain-openai")

    # ── Cohere (free tier: dashboard.cohere.com) ──────────────────────────────
    elif LLM_PROVIDER == "cohere" and COHERE_API_KEY:
        try:
            from langchain_cohere import ChatCohere
            return ChatCohere(
                cohere_api_key=COHERE_API_KEY,
                model=LLM_MODEL or "command-r-plus",
                temperature=0.7,
            )
        except ImportError:
            print("Warning: langchain-cohere not installed. Run: pip install langchain-cohere")

    # ── Ollama (fully local: ollama.ai) ───────────────────────────────────────
    elif LLM_PROVIDER == "ollama":
        try:
            from langchain_ollama import ChatOllama
            return ChatOllama(
                base_url=OLLAMA_BASE_URL,
                model=LLM_MODEL or "llama3.2",
                temperature=0.7,
            )
        except ImportError:
            print("Warning: langchain-ollama not installed. Run: pip install langchain-ollama")

    # ── Generic OpenAI-compatible (LM Studio, vLLM, Anyscale, etc.) ──────────
    elif LLM_PROVIDER == "openai-compat" and OPENAI_COMPAT_BASE_URL:
        try:
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(
                api_key=OPENAI_COMPAT_API_KEY,
                base_url=OPENAI_COMPAT_BASE_URL,
                model=LLM_MODEL or "local-model",
                temperature=0.7,
                max_tokens=4096,
            )
        except ImportError:
            print("Warning: langchain-openai not installed. Run: pip install langchain-openai")

    return None  # Algorithmic fallback


def get_crewai_llm():
    """Return CrewAI-compatible LLM config string."""
    if LLM_PROVIDER == "groq" and GROQ_API_KEY:
        return f"groq/{LLM_MODEL}"
    if LLM_PROVIDER == "gemini" and GEMINI_API_KEY:
        return f"gemini/{LLM_MODEL or 'gemini-1.5-flash'}"
    if LLM_PROVIDER == "openai" and OPENAI_API_KEY:
        return f"openai/{LLM_MODEL or 'gpt-4o-mini'}"
    if LLM_PROVIDER == "together" and TOGETHER_API_KEY:
        return f"together_ai/{LLM_MODEL or 'meta-llama/Llama-3-70b-chat-hf'}"
    if LLM_PROVIDER == "cohere" and COHERE_API_KEY:
        return f"cohere/{LLM_MODEL or 'command-r-plus'}"
    if LLM_PROVIDER == "ollama":
        return f"ollama/{LLM_MODEL or 'llama3.2'}"
    return None
