import os
from dotenv import load_dotenv

load_dotenv()

# Models to use
AVAILABLE_MODELS = [
    "deepseek-coder:6.7b",
    "codellama:7b", 
    "qwen2.5-coder:7b"
]

DEFAULT_MODEL = "deepseek-coder:6.7b"

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# GitHub settings (will add later)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_webhook_secret")