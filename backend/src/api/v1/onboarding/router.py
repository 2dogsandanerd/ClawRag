from fastapi import APIRouter, HTTPException
from loguru import logger
from typing import List
from .models import WizardStep, WizardState, SystemCheckResponse, SystemCheckResult
import httpx
import os
from src.core.chroma_manager import get_chroma_manager
from src.core.system_check import SystemHealthCheck
from src.core.config import get_config

router = APIRouter()

# Static definition of steps for now
DEFAULT_STEPS = [
    WizardStep(id="system_check", title="System Check", description="Prüfe Verbindungen zu ChromaDB, Redis und Ollama", component="SystemCheck"),
    WizardStep(id="model_selection", title="Modell Auswahl", description="Wähle das LLM für die Antwort-Generierung", component="ModelSelector"),
    WizardStep(id="data_ingestion", title="Daten Import", description="Lade E-Mails und Dokumente in den RAG-Index", component="DataIngestion"),
    WizardStep(id="completion", title="Abschluss", description="Zusammenfassung und Start", component="Completion")
]

@router.get("/steps", response_model=List[WizardStep])
async def get_steps():
    """Returns the list of available onboarding/maintenance steps."""
    return DEFAULT_STEPS

@router.post("/run/system_check", response_model=SystemCheckResponse)
async def run_system_check():
    """Executes a system health check for critical components."""
    checks = []
    overall_status = "ok"

    # 1. Check ChromaDB
    try:
        manager = get_chroma_manager()
        # Use the proper method to get the client
        client = manager.get_client()
        if client:
            client.heartbeat()
            checks.append(SystemCheckResult(component="ChromaDB", status="ok", message="Connected successfully"))
        else:
            overall_status = "error"
            checks.append(SystemCheckResult(component="ChromaDB", status="error", message="Connection failed", details="Client not available"))
    except Exception as e:
        overall_status = "error"
        checks.append(SystemCheckResult(component="ChromaDB", status="error", message="Connection failed", details=str(e)))

    # 2. Check LLM Provider
    config = get_config()
    provider = config.provider
    
    if provider == "ollama":
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        res = await SystemHealthCheck.check_ollama(ollama_host)
        if res["status"] == "ok":
            checks.append(SystemCheckResult(component=f"LLM ({provider})", status="ok", message=f"Connected to {ollama_host}", details=f"Models: {', '.join(res['models'][:5])}"))
        else:
            overall_status = "error"
            checks.append(SystemCheckResult(component=f"LLM ({provider})", status="error", message=res["message"]))
    
    elif provider == "openai_compatible":
        base_url = config.base_url
        res = await SystemHealthCheck.check_openai_compatible(base_url, config.api_key)
        if res["status"] == "ok":
            checks.append(SystemCheckResult(component=f"LLM ({provider})", status="ok", message=f"Connected to {base_url}", details=f"Models: {', '.join(res['models'][:5])}"))
        else:
            overall_status = "error"
            checks.append(SystemCheckResult(component=f"LLM ({provider})", status="error", message=res["message"]))
    
    elif provider in ["openai", "gemini", "anthropic"]:
        # For cloud providers, we just check if API key is set
        if config.api_key:
            checks.append(SystemCheckResult(component=f"LLM ({provider})", status="ok", message=f"API Key configured for {provider}"))
        else:
            overall_status = "error"
            checks.append(SystemCheckResult(component=f"LLM ({provider})", status="error", message=f"API Key missing for {provider}"))
    
    else:
        checks.append(SystemCheckResult(component="LLM", status="warning", message=f"Unknown provider: {provider}"))

    return SystemCheckResponse(overall_status=overall_status, checks=checks)


