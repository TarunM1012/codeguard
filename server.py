from fastapi import FastAPI, Request
from ollama_client import OllamaClient
from github_client import GitHubClient
from diff_parser import extract_added_code

import json

app = FastAPI()
ollama = OllamaClient()
github = GitHubClient()

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

@app.post("/webhook")
async def github_webhook(request: Request):
    """Handle GitHub webhook for PR events"""
    
    # Get event type
    event = request.headers.get("X-GitHub-Event")
    
    # Parse payload
    payload = await request.json()
    
    # Only handle PR events
    if event != "pull_request":
        return {"status": "ignored", "reason": f"Not a PR event: {event}"}
    
    action = payload.get("action")
    
    # Only analyze when PR is opened or updated
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"Action not relevant: {action}"}
    
    # Extract PR info
    pr_number = payload["pull_request"]["number"]
    repo = payload["repository"]["full_name"]
    
    print(f"\n New PR event: {repo} #{pr_number}")
    
    # Get changed files
    try:
        files = github.get_pr_files(repo, pr_number)
        
        analyses = []
        
        for file in files:
            # Only analyze code files
            if not file['filename'].endswith(('.py', '.js', '.java', '.cpp', '.c', '.ts', '.jsx', '.tsx')):
                continue
            
            # Get the patch (diff)
            patch = file.get('patch')
            if not patch:
                continue
            
            # Extract just the new code
            new_code = extract_added_code(patch)
            if not new_code.strip():
                continue
            
            print(f"  Analyzing {file['filename']}...")
            
            # Analyze with Ollama
            prompt = f"""You are a code reviewer. Analyze this NEW code for bugs and security issues:

File: {file['filename']}
```
{new_code}
```

List ONLY critical issues. Be concise."""
            
            analysis = ollama.generate("deepseek-coder:6.7b", prompt)
            
            analyses.append({
                "file": file['filename'],
                "additions": file['additions'],
                "deletions": file['deletions'],
                "analysis": analysis
            })
        
        return {
            "status": "analyzed",
            "repo": repo,
            "pr": pr_number,
            "files_analyzed": len(analyses),
            "results": analyses
        }
    
    except Exception as e:
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)