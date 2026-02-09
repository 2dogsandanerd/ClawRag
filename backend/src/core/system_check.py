import shutil
import os
import aiohttp
from typing import Dict, Any, List
from loguru import logger
from pathlib import Path

class SystemHealthCheck:
    """
    Comprehensive system health check for the Onboarding Wizard.
    Checks disk space, permissions, and AI service availability.
    """

    @staticmethod
    def check_disk_space(path: str = ".", min_gb: int = 2) -> Dict[str, Any]:
        """Check if there is enough free disk space."""
        try:
            total, used, free = shutil.disk_usage(path)
            free_gb = free / (2**30)
            
            status = "ok" if free_gb >= min_gb else "warning"
            if free_gb < 0.5: # Critical if less than 500MB
                status = "critical"
                
            return {
                "status": status,
                "free_gb": round(free_gb, 2),
                "required_gb": min_gb,
                "message": f"Free space: {round(free_gb, 2)} GB"
            }
        except Exception as e:
            logger.error(f"Disk check failed: {e}")
            return {"status": "error", "message": str(e)}

    @staticmethod
    def check_permissions(paths: List[str]) -> Dict[str, Any]:
        """Check read/write permissions for critical directories."""
        results = {}
        all_ok = True
        
        for path_str in paths:
            path = Path(path_str)
            # Create if not exists to test creation
            try:
                if not path.exists():
                    path.mkdir(parents=True, exist_ok=True)
                
                # Test write
                test_file = path / ".perm_test"
                test_file.touch()
                test_file.unlink()
                
                results[path_str] = "ok"
            except Exception as e:
                logger.error(f"Permission check failed for {path_str}: {e}")
                results[path_str] = "error"
                all_ok = False
                
        return {
            "status": "ok" if all_ok else "error",
            "details": results
        }

    @staticmethod
    async def check_ollama(base_url: str = "http://localhost:11434") -> Dict[str, Any]:
        """Check if Ollama is running and list models."""
        try:
            async with aiohttp.ClientSession() as session:
                # Check version/status
                async with session.get(f"{base_url}/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [m['name'] for m in data.get('models', [])]
                        return {
                            "status": "ok",
                            "available": True,
                            "models": models,
                            "count": len(models)
                        }
                    else:
                        return {
                            "status": "error",
                            "available": False,
                            "message": f"Ollama returned status {response.status}"
                        }
        except aiohttp.ClientConnectorError:
            return {
                "status": "critical",
                "available": False,
                "message": "Connection refused. Is Ollama running?"
            }
        except Exception as e:
            return {
                "status": "error",
                "available": False,
                "message": str(e)
            }

    @staticmethod
    async def check_openai_compatible(base_url: str, api_key: str = "not-required") -> Dict[str, Any]:
        """Check if an OpenAI-compatible server is running."""
        if not base_url:
            return {
                "status": "error",
                "available": False,
                "message": "No base_url provided for OpenAI-compatible server"
            }
            
        try:
            # Clean up base_url - ensure it doesn't end with /v1 if we're adding it
            check_url = base_url.rstrip('/')
            if not check_url.endswith('/v1'):
                check_url = f"{check_url}/v1"
            
            headers = {}
            if api_key and api_key != "not-required":
                headers["Authorization"] = f"Bearer {api_key}"
                
            async with aiohttp.ClientSession() as session:
                logger.info(f"Checking OpenAI-compatible endpoint: {check_url}/models")
                async with session.get(f"{check_url}/models", headers=headers, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Some servers return a list of models directly, others wrap it in a 'data' field
                        models_data = data.get('data', data) if isinstance(data, dict) else data
                        models = []
                        if isinstance(models_data, list):
                            models = [m.get('id', str(m)) for m in models_data]
                            
                        return {
                            "status": "ok",
                            "available": True,
                            "models": models,
                            "count": len(models)
                        }
                    elif response.status == 401:
                        return {
                            "status": "error",
                            "available": False,
                            "message": "Unauthorized: API key may be invalid or required"
                        }
                    else:
                        text = await response.text()
                        return {
                            "status": "error",
                            "available": False,
                            "message": f"Server returned status {response.status}: {text[:100]}"
                        }
        except aiohttp.ClientConnectorError:
            return {
                "status": "critical",
                "available": False,
                "message": f"Connection refused at {base_url}. Is the server running?"
            }
        except Exception as e:
            logger.error(f"OpenAI-compatible check failed: {e}")
            return {
                "status": "error",
                "available": False,
                "message": str(e)
            }
