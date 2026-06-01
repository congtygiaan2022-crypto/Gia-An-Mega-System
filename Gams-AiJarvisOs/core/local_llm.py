"""
core/local_llm.py — Local LLM via Ollama (no API key needed)
Run: ollama serve  +  ollama pull llama3
"""
import requests
import os


OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
DEFAULT_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3")
TIMEOUT = int(os.getenv("LOCAL_LLM_TIMEOUT", "120"))


class LocalLLM:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.url = OLLAMA_URL
        self.model = model

    def is_available(self) -> bool:
        """Ping Ollama health endpoint."""
        try:
            r = requests.get("http://localhost:11434/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def ask(self, prompt: str, model: str = None) -> str:
        """Send prompt, return response string. Returns None if unavailable."""
        try:
            r = requests.post(
                self.url,
                json={
                    "model": model or self.model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=TIMEOUT,
            )
            r.raise_for_status()
            return r.json().get("response", "").strip()
        except requests.exceptions.ConnectionError:
            return None  # Ollama not running — caller falls back to cloud
        except Exception as e:
            return f"LLM ERROR: {e}"


# Global singleton
local_llm = LocalLLM()
