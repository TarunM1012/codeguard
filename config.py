import os
from dotenv import load_dotenv

load_dotenv()

# Models to use
AVAILABLE_MODELS = [
    "deepseek-coder:6.7b",
    "codellama:7b", 
    "qwen2.5-coder:7b"
]

DEFAULT_CONFIG = {
    "models": ["deepseek"],  # Can be ["deepseek"], ["codellama"], ["qwen"], or ["deepseek", "codellama", "qwen"]
    "consensus_threshold": 2,  # For ensemble: how many models must agree
    "mode": "single"  # "single" or "ensemble"
}

# Ollama settings
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")

# GitHub settings (will add later)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "your_webhook_secret")