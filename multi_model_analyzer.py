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
                print(f"      {model_name} failed: {e}")
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
    
    def extract_keywords(self, issue_text):
        """Extract key technical terms from issue description"""
        import re
        
        text = issue_text.lower()
        
        # Remove common filler words that don't indicate bug type
        stopwords = {"issue", "bug", "error", "problem", "found", "the", "a", "an", 
                     "in", "on", "at", "to", "for", "of", "with", "by", "is", "are",
                     "this", "that", "it", "can", "may", "could", "should", "description",
                     "file", "function", "code", "line", "using", "used", "allows"}
        
        # Extract words (alphanumeric plus underscores)
        words = re.findall(r'\b\w+\b', text)
        
        # Filter out stopwords and very short words
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        
        # Extract important bigrams (two-word technical phrases)
        bigrams = []
        for i in range(len(keywords) - 1):
            bigram = f"{keywords[i]} {keywords[i+1]}"
            bigrams.append(bigram)
        
        return set(keywords + bigrams)
    
    def find_consensus(self, ensemble_results, threshold=2):
        """Find issues using dynamic keyword extraction and similarity matching"""
        keyword_tracker = {}
        
        # Process each model's analysis
        for model_name, analysis in ensemble_results.items():
            if isinstance(analysis, str) and not analysis.startswith("Error:"):
                issues = self.extract_issues(analysis)
                
                for issue in issues:
                    keywords = self.extract_keywords(issue)
                    
                    # Try to match with existing issue signatures
                    matched = False
                    for existing_sig, data in keyword_tracker.items():
                        # Calculate keyword overlap using Jaccard similarity
                        # Jaccard = (intersection) / (union)
                        overlap = len(keywords & existing_sig) / len(keywords | existing_sig) if (keywords | existing_sig) else 0
                        
                        # Consider issues the same if they share 40%+ keywords
                        if overlap > 0.4:
                            if model_name not in data["models"]:
                                data["models"].add(model_name)
                                data["examples"].append(issue)
                            matched = True
                            break
                    
                    if not matched:
                        # No match found - this is a new unique issue
                        keyword_tracker[frozenset(keywords)] = {
                            "keywords": keywords,
                            "models": {model_name},
                            "examples": [issue]
                        }
        
        # Build consensus results from issues found by multiple models
        consensus = []
        for sig, data in keyword_tracker.items():
            if len(data["models"]) >= threshold:
                # Create readable category name from most significant keywords
                key_terms = sorted(data["keywords"], key=len, reverse=True)[:3]
                category = " ".join(key_terms).title()
                
                consensus.append({
                    "category": category,
                    "models": list(data["models"]),
                    "count": len(data["models"]),
                    "example": data["examples"][0]
                })
        
        return consensus

# Test suite
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
    print(f"Issues {threshold}+ models agree on:")
    for item in consensus:
        print(f"  Category: {item['category']}")
        print(f"  Models: {', '.join(item['models'])}")
        print(f"  Example: {item['example']}\n")