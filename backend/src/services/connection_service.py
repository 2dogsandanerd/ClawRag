
import time
import httpx
import asyncio
from typing import Dict, Any, List
from loguru import logger

# Assuming clients or connection logic will be available from other services
# This is a simplified adaptation of Project B's service.

class ConnectionService:
    """Provides methods to test connections to external services."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.logger = logger.bind(component="ConnectionService")

    async def test_ollama_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Tests connection to Ollama."""
        start_time = time.time()
        host = config.get("OLLAMA_HOST", "http://localhost:11434")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{host}/api/tags", timeout=self.timeout)
                response.raise_for_status()
                duration = time.time() - start_time
                return {
                    "success": True,
                    "message": f"Ollama connection to {host} successful.",
                    "duration": duration
                }
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Ollama connection test failed: {e}")
            return {"success": False, "message": str(e), "duration": duration}

    async def test_chroma_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Tests connection to ChromaDB via ChromaManager."""
        start_time = time.time()

        try:
            # Use the centralized ChromaManager for connection testing
            from src.core.chroma_manager import get_chroma_manager
            chroma_manager = get_chroma_manager()

            # Use async method for proper connection testing
            client = await chroma_manager.get_client_async()

            if client:
                # Test with heartbeat (wrap in asyncio.to_thread for sync operation)
                heartbeat = await asyncio.to_thread(client.heartbeat)
                duration = time.time() - start_time
                self.logger.info(f"ChromaDB heartbeat: {heartbeat}")
                return {
                    "success": True,
                    "message": f"ChromaDB connection via ChromaManager successful.",
                    "duration": duration
                }
            else:
                duration = time.time() - start_time
                self.logger.error("ChromaDB client not available via ChromaManager")
                return {
                    "success": False,
                    "message": "ChromaDB client not available via ChromaManager",
                    "duration": duration
                }
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"ChromaDB connection test failed: {e}")
            return {"success": False, "message": str(e), "duration": duration}

    async def test_openai_compatible_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Tests connection to an OpenAI-compatible server."""
        start_time = time.time()
        base_url = config.get("OPENAI_BASE_URL")
        if not base_url:
            return {"success": False, "message": "OPENAI_BASE_URL not configured.", "duration": 0}
            
        api_key = config.get("OPENAI_API_KEY", "not-required")
        
        try:
            from src.core.system_check import SystemHealthCheck
            res = await SystemHealthCheck.check_openai_compatible(base_url, api_key)
            duration = time.time() - start_time
            if res["status"] == "ok":
                return {
                    "success": True,
                    "message": f"OpenAI-compatible connection to {base_url} successful.",
                    "duration": duration,
                    "details": f"Found {res['count']} models."
                }
            else:
                return {
                    "success": False,
                    "message": res["message"],
                    "duration": duration
                }
        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"OpenAI-compatible connection test failed: {e}")
            return {"success": False, "message": str(e), "duration": duration}

    async def test_all_connections(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Tests all relevant connections concurrently."""
        self.logger.info("Testing all connections...")
        tasks = {
            "ollama": self.test_ollama_connection(config),
            "chroma": self.test_chroma_connection(config),
        }
        
        # Add optional provider tests
        provider = config.get("LLM_PROVIDER")
        if provider == "openai_compatible":
            tasks["openai_compatible"] = self.test_openai_compatible_connection(config)
        
        results = await asyncio.gather(*tasks.values())
        
        final_results = []
        for i, (component, _) in enumerate(tasks.items()):
            result = results[i]
            result["component"] = component
            final_results.append(result)
        
        return final_results

connection_service = ConnectionService()
