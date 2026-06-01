import os
import sys
import warnings
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv
from integrations.local_llm_connector import local_llm

# Suppress deprecated SDK warning — still functional, upgrade later
warnings.filterwarnings("ignore", category=FutureWarning, module="google")

# Force UTF-8 on Windows stdout
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')

load_dotenv()


class BaseAgent:
    def __init__(self, name: str, instructions: str):
        self.name = name
        self.instructions = instructions

    def run(self, task: str, context: str = "", model: str = None) -> str:
        # Reload env to catch runtime changes
        load_dotenv(override=True)

        if not model:
            model = os.getenv("DEFAULT_MODEL", "local")

        prompt = f"{self.instructions}\n\nContext:\n{context}\n\nTask:\n{task}"
        system = f"You are {self.name}, a specialized AI agent."

        print(f"[{self.name}] Using model: {model}")

        # -----------------------------------------------------------------
        # 1. Local LLM via Ollama (offline, no API cost)
        # -----------------------------------------------------------------
        if model == "local" or model.startswith("ollama:"):
            ollama_model = model.replace("ollama:", "") if ":" in model else None
            if local_llm.is_available():
                response = local_llm.chat(system=system, user_message=prompt, model=ollama_model)
                if response:
                    print(f"[{self.name}] Local LLM responded.")
                    return response
                print(f"[{self.name}] Local LLM returned empty. Falling back to cloud...")
            else:
                print(f"[{self.name}] Ollama not running. Falling back to cloud API...")

        # -----------------------------------------------------------------
        # 2. Gemini
        # -----------------------------------------------------------------
        if "gemini" in model.lower() or model == "local":
            gemini_key = os.getenv("GEMINI_API_KEY")
            if gemini_key:
                try:
                    api_model = "gemini-2.5-flash" if "flash" in model.lower() else "gemini-2.5-pro"
                    if model == "local":
                        api_model = "gemini-2.5-flash"
                    genai.configure(api_key=gemini_key)
                    print(f"[{self.name}] Calling Gemini ({api_model})...")
                    gemini_model = genai.GenerativeModel(
                        model_name=api_model,
                        system_instruction=system,
                    )
                    response = gemini_model.generate_content(prompt)
                    print(f"[{self.name}] Gemini responded.")
                    return response.text
                except Exception as e:
                    print(f"[{self.name}] Gemini error: {e}. Trying OpenAI...")

        # -----------------------------------------------------------------
        # 3. OpenAI / GPT
        # -----------------------------------------------------------------
        if "gpt" in model.lower() or model == "local":
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                try:
                    api_model = "gpt-4o"
                    if "3.5" in model:
                        api_model = "gpt-3.5-turbo"
                    elif "turbo" in model:
                        api_model = "gpt-4-turbo"
                    client = OpenAI(api_key=openai_key)
                    print(f"[{self.name}] Calling OpenAI ({api_model})...")
                    response = client.chat.completions.create(
                        model=api_model,
                        messages=[
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        timeout=30.0,
                    )
                    print(f"[{self.name}] OpenAI responded.")
                    return response.choices[0].message.content
                except Exception as e:
                    print(f"[{self.name}] OpenAI error: {e}")

        raise RuntimeError(
            f"[{self.name}] All LLM backends failed (model='{model}'). "
            "Check Ollama is running or set GEMINI_API_KEY / OPENAI_API_KEY in .env"
        )
