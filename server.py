from fastapi import FastAPI, Request
from ollama_client import OllamaClient
from github_client import GitHubClient
from diff_parser import extract_added_code
from multi_model_analyzer import MultiModelAnalyzer
from config import ANALYSIS_MODE
import json

app = FastAPI()
ollama = OllamaClient()
github = GitHubClient()
analyzer = MultiModelAnalyzer()

@app.get("/")
def home():
    """Health check endpoint"""
    is_connected = ollama.test_connection()
    return {
        "status": "running",
        "ollama_connected": is_connected
    }

@app.post("/analyze")
async def analyze_code(request: Request):
    """Direct code analysis endpoint for testing"""
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
    """Process GitHub webhook events for pull requests"""
    
    # Extract event metadata from headers
    event = request.headers.get("X-GitHub-Event")
    payload = await request.json()
    
    # Filter: only process pull request events
    if event != "pull_request":
        return {"status": "ignored", "reason": f"Not a PR event: {event}"}
    
    action = payload.get("action")
    
    # Filter: only analyze new PRs or updates to existing PRs
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"Action not relevant: {action}"}
    
    # Extract pull request metadata
    pr_number = payload["pull_request"]["number"]
    repo = payload["repository"]["full_name"]
    
    try:
        commit_id = payload["pull_request"]["head"]["sha"]
    except KeyError:
        commit_id = "unknown"
    
    print(f"\nNew PR event: {repo} #{pr_number} (commit: {commit_id[:7]})")
    
    # Begin analysis process
    try:
        files = github.get_pr_files(repo, pr_number)
        analyses = []
        
        for file in files:
            # Skip non-code files
            if not file['filename'].endswith(('.py', '.js', '.java', '.cpp', '.c', '.ts', '.jsx', '.tsx')):
                continue
            
            # Skip files with no diff data
            patch = file.get('patch')
            if not patch:
                continue
            
            # Extract only newly added code from the diff
            new_code = extract_added_code(patch)
            if not new_code.strip():
                continue
            
            print(f"  Analyzing {file['filename']}...")
            
            # Select single-model or ensemble analysis based on config
            mode = ANALYSIS_MODE
            
            if mode == "single":
                # Fast path: single model analysis
                result = analyzer.analyze_single(new_code, file['filename'], "deepseek")
                analysis = result['analysis']
                model_info = f"Model: {result['model']}"
            else:
                # Ensemble path: multi-model consensus
                result = analyzer.analyze_ensemble(new_code, file['filename'])
                
                # Debug output: show individual model responses
                print("\n  === ENSEMBLE RESULTS ===")
                for model, model_analysis in result['results'].items():
                    print(f"\n  {model.upper()}:")
                    print(f"  {model_analysis[:300]}...")
                print("\n  === END RESULTS ===\n")
                
                # Apply consensus algorithm to find agreement between models
                consensus = analyzer.find_consensus(result['results'], threshold=2)
                
                if consensus:
                    # Format consensus results for display
                    analysis = "**Consensus Issues (2+ models agree):**\n\n"
                    for item in consensus:
                        models_str = ", ".join(item["models"])
                        analysis += f"• **{item['category']}** ({item['count']}/3 models: {models_str})\n"
                        analysis += f"  _{item['example']}_\n\n"
                else:
                    analysis = "No consensus issues found. Individual model results varied."
                
                model_info = f"Models: {', '.join(result['models'])}"
            
            # Format comment for GitHub
            comment_body = f"""## CodeGuard Analysis

**File:** `{file['filename']}`  
**{model_info}**

{analysis}

---
*Powered by CodeGuard Multi-Model System*"""
            
            # Post analysis as PR comment
            try:
                github.post_pr_comment(repo, pr_number, comment_body)
                print(f"    Posted comment for {file['filename']}")
                
                analyses.append({
                    "file": file['filename'],
                    "comment_posted": True
                })
            except Exception as e:
                print(f"    Failed to post comment: {e}")
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
        print(f"Error: {e}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)