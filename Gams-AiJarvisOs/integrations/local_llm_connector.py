"""
Local LLM Connector — Ollama HTTP client
Supports: llama3, mistral, phi3, gemma, etc.

Priority chain in base_agent.py:
  Local LLM (Ollama) → Gemini → OpenAI

To use: run `ollama serve` and ensure the model is pulled.
  ollama pull llama3
"""

import requests
import os
import json
from core.logger import get_module_logger

logger = get_module_logger("LocalLLM")

OLLAMA_BASE_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
DEFAULT_LOCAL_MODEL = os.getenv("LOCAL_LLM_MODEL", "llama3")
TIMEOUT_SECONDS = int(os.getenv("LOCAL_LLM_TIMEOUT", "120"))


class LocalLLMConnector:
    """
    Wraps the Ollama API for local, offline LLM inference.
    Falls back gracefully if Ollama is not running.
    """

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = DEFAULT_LOCAL_MODEL):
        self.base_url = base_url.rstrip("/")
        self.model = model

    def is_available(self) -> bool:
        """Ping Ollama to check if it is running."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=3)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list:
        """Return list of locally available models."""
        try:
            r = requests.get(f"{self.base_url}/api/tags", timeout=5)
            data = r.json()
            return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"[LocalLLM] Failed to list models: {e}")
            return []

    def generate(self, prompt: str, model: str = None, stream: bool = False) -> str:
        """
        Send a prompt to local Ollama model and return the response.

        Args:
            prompt: The full prompt string (system + context + task already merged).
            model: Override the default model.
            stream: If True, consume streamed NDJSON response.

        Returns:
            The LLM response string, or error message.
        """
        model = model or self.model
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
        }

        try:
            logger.info(f"[LocalLLM] Sending prompt to Ollama model '{model}' at {self.base_url}")
            r = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=TIMEOUT_SECONDS,
                stream=stream,
            )
            r.raise_for_status()

            if stream:
                # Aggregate streamed NDJSON lines
                output = []
                for line in r.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        output.append(chunk.get("response", ""))
                        if chunk.get("done", False):
                            break
                result = "".join(output)
            else:
                result = r.json().get("response", "").strip()

            logger.info(f"[LocalLLM] Response received ({len(result)} chars).")
            return result

        except requests.exceptions.ConnectionError:
            logger.warning("[LocalLLM] Ollama not running — connection refused.")
            return None
        except requests.exceptions.Timeout:
            logger.warning(f"[LocalLLM] Ollama timed out after {TIMEOUT_SECONDS}s.")
            return None
        except Exception as e:
            logger.error(f"[LocalLLM] Unexpected error: {e}")
            return None

    def chat(self, system: str, user_message: str, model: str = None) -> str:
        """
        Convenience wrapper: merge system + user into a single prompt.
        Ollama /api/generate does not support chat format natively for all models,
        so we format it manually.
        """
        prompt = f"[SYSTEM]\n{system}\n\n[USER]\n{user_message}\n\n[ASSISTANT]\n"
        return self.generate(prompt, model=model)


# Global singleton
local_llm = LocalLLMConnector()
