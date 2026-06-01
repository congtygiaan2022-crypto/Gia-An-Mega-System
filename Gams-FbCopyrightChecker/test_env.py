from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("ANTHROPIC_API_KEY")
base_url = os.getenv("ANTHROPIC_BASE_URL")
model = os.getenv("ANTHROPIC_MODEL")

print(api_key)
print(base_url)
print(model)