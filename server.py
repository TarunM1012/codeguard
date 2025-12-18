from fastapi import FastAPI, Request
from ollama_client import OllamaClient
import json

app = FastAPI()
ollama = OllamaClient()

@app.get("/")
def home():
    """Health check"""
    is_connected = ollama.test_connection()
    return {
        "status": "running",
        "ollama_connected": is_connected
    }

@app.post("/analyze")
async def analyze_code(request: Request):
    """Analyze code snippet"""
    data = await request.json()
    
    code = data.get("code", "")
    model = data.get("model", "deepseek-coder:6.7b")
    
    if not code:
        return {"error": "No code provided"}
    
    prompt = f"""You are a code reviewer. Analyze this code for bugs, security issues, and bad practices:
```
{code}
```

List any issues found."""
    
    result = ollama.generate(model, prompt)
    
    return {
        "code": code,
        "model": model,
        "analysis": result
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)