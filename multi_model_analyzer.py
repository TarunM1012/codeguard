from ollama_client import OllamaClient
from config import AVAILABLE_MODELS

class MultiModelAnalyzer:
    def __init__(self):
        self.client = OllamaClient()
    
    def analyze_with_model(self, model_name, code, filename):
        """Analyze code with a single model"""
        model = AVAILABLE_MODELS[model_name]
        
        prompt = f"""You are a code reviewer. Analyze this NEW code for bugs and security issues:

File: {filename}
```
{code}
```

List ONLY critical issues. Be concise. Format: "Issue: <description>". One issue per line."""
        
        return self.client.generate(model, prompt)
    
    def analyze_single(self, code, filename, model_name="deepseek"):
        """Analyze with single model"""
        result = self.analyze_with_model(model_name, code, filename)
        
        return {
            "mode": "single",
            "model": model_name,
            "analysis": result
        }
    
    def analyze_ensemble(self, code, filename, models=None):
        """Analyze with multiple models"""
        if models is None:
            models = ["deepseek", "codellama", "qwen"]
        
        results = {}
        
        for model_name in models:
            print(f"      Running {model_name}...")
            try:
                analysis = self.analyze_with_model(model_name, code, filename)
                results[model_name] = analysis
            except Exception as e:
                print(f"       {model_name} failed: {e}")
                results[model_name] = f"Error: {str(e)}"
        
        return {
            "mode": "ensemble",
            "models": models,
            "results": results
        }
    
    def extract_issues(self, analysis_text):
        """Extract individual issues from analysis text"""
        issues = []
        for line in analysis_text.split('\n'):
            line = line.strip()
            if line and ('issue' in line.lower() or 'bug' in line.lower() or 'error' in line.lower()):
                issues.append(line)
        return issues
    
    def find_consensus(self, ensemble_results, threshold=2):
        """Find consensus using semantic similarity (embeddings)"""
        from sentence_transformers import SentenceTransformer
        from sklearn.metrics.pairwise import cosine_similarity
        import numpy as np
        
        # Load lightweight embedding model
        model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Collect all issues with metadata
        all_issues = []
        for model_name, analysis in ensemble_results.items():
            if isinstance(analysis, str) and not analysis.startswith("Error:"):
                issues = self.extract_issues(analysis)
                for issue in issues:
                    all_issues.append({
                        "text": issue,
                        "model": model_name,
                        "embedding": None
                    })
        
        if not all_issues:
            return []
        
        # Generate embeddings
        texts = [item["text"] for item in all_issues]
        embeddings = model.encode(texts)
        
        # Add embeddings to issues
        for i, item in enumerate(all_issues):
            item["embedding"] = embeddings[i]
        
        # Group similar issues using clustering
        grouped = []
        used = set()
        
        for i, issue1 in enumerate(all_issues):
            if i in used:
                continue
                
            group = {
                "issues": [issue1],
                "models": {issue1["model"]},
                "representative": issue1["text"]
            }
            
            # Find similar issues
            for j, issue2 in enumerate(all_issues[i+1:], start=i+1):
                if j in used:
                    continue
                    
                # Calculate cosine similarity
                sim = cosine_similarity(
                    [issue1["embedding"]], 
                    [issue2["embedding"]]
                )[0][0]
                
                # If similarity > 0.7, same issue
                if sim > 0.7:
                    group["issues"].append(issue2)
                    group["models"].add(issue2["model"])
                    used.add(j)
            
            used.add(i)
            grouped.append(group)
        
        # Filter to consensus (2+ models)
        consensus = []
        for group in grouped:
            if len(group["models"]) >= threshold:
                # Extract core concept for category
                words = group["representative"].lower().split()
                key_words = [w for w in words if len(w) > 4][:3]
                category = " ".join(key_words).title()
                
                consensus.append({
                    "category": category,
                    "models": list(group["models"]),
                    "count": len(group["models"]),
                    "example": group["representative"]
                })
        
        return consensus

# Test it
if __name__ == "__main__":
    analyzer = MultiModelAnalyzer()
    
    test_code = """
def divide(a, b):
    return a / b

def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return query
"""
    
    print("=" * 60)
    print("TEST 1: Single Model Analysis")
    print("=" * 60)
    result = analyzer.analyze_single(test_code, "test.py", "deepseek")
    print(f"Model: {result['model']}")
    print(f"Analysis:\n{result['analysis']}\n")
    
    print("=" * 60)
    print("TEST 2: Ensemble Analysis")
    print("=" * 60)
    result = analyzer.analyze_ensemble(test_code, "test.py")
    print(f"Models: {result['models']}")
    for model, analysis in result['results'].items():
        print(f"\n{model.upper()}:")
        print(analysis[:200])
    
    print("\n" + "=" * 60)
    print("TEST 3: Consensus Detection")
    print("=" * 60)
    consensus = analyzer.find_consensus(result['results'], threshold=2)
    print(f"Issues {2}+ models agree on:")
    for issue in consensus:
        print(f"  • {issue}")