from fastapi import FastAPI, Request
from ollama_client import OllamaClient
from github_client import GitHubClient
from diff_parser import extract_added_code
from multi_model_analyzer import MultiModelAnalyzer
import json

app = FastAPI()
ollama = OllamaClient()
github = GitHubClient()
analyzer = MultiModelAnalyzer()

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
    
    try:
        commit_id = payload["pull_request"]["head"]["sha"]
    except KeyError:
        commit_id = "unknown"
    
    print(f"\n New PR event: {repo} #{pr_number} (commit: {commit_id[:7]})")
    
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
            
            # Choose analysis mode based on config
            mode = "single"  # TODO: Make this configurable later
            
            if mode == "single":
                result = analyzer.analyze_single(new_code, file['filename'], "deepseek")
                analysis = result['analysis']
                model_info = f"Model: {result['model']}"
            else:
                # Ensemble mode
                result = analyzer.analyze_ensemble(new_code, file['filename'])
                
                # Get consensus issues
                consensus = analyzer.find_consensus(result['results'], threshold=2)
                
                if consensus:
                    analysis = "**Consensus Issues (2+ models agree):**\n\n" + "\n".join(f"• {issue}" for issue in consensus)
                else:
                    analysis = "No consensus issues found. Individual model results varied."
                
                model_info = f"Models: {', '.join(result['models'])}"
            
            # Post comment to GitHub
            comment_body = f"""##  CodeGuard Analysis

**File:** `{file['filename']}`  
**{model_info}**

{analysis}

---
*Powered by CodeGuard Multi-Model System*"""
            
            try:
                github.post_pr_comment(repo, pr_number, comment_body)
                print(f"     Posted comment for {file['filename']}")
                
                analyses.append({
                    "file": file['filename'],
                    "comment_posted": True
                })
            except Exception as e:
                print(f"     Failed to post comment: {e}")
                analyses.append({
                    "file": file['filename'],
                    "comment_posted": False,
                    "error": str(e)
                })
        
        return {
            "status": "analyzed",
            "repo": repo,
            "pr": pr_number,
            "files_analyzed": len(analyses),
            "results": analyses
        }
    
    except Exception as e:
        print(f" Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)