from ollama_client import OllamaClient
from config import AVAILABLE_MODELS
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class MultiModelAnalyzer:
    def __init__(self):
        self.client = OllamaClient()
        # Load embedding model for semantic similarity
        print("Loading embedding model (all-MiniLM-L6-v2)...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        print("Embedding model loaded successfully")
    
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
    
    def find_consensus_string_matching(self, ensemble_results, threshold=2):
        """Find issues that multiple models agree on using string matching (legacy method)"""
        all_issues = {}
        
        # Collect all issues from all models
        for model_name, analysis in ensemble_results.items():
            if isinstance(analysis, str) and not analysis.startswith("Error:"):
                issues = self.extract_issues(analysis)
                for issue in issues:
                    # Normalize issue text (lowercase, basic cleaning)
                    normalized = issue.lower().strip()
                    
                    if normalized not in all_issues:
                        all_issues[normalized] = {
                            "original": issue,
                            "models": [],
                            "count": 0
                        }
                    
                    all_issues[normalized]["models"].append(model_name)
                    all_issues[normalized]["count"] += 1
        
        # Filter to only issues where threshold+ models agree
        consensus = [
            data["original"] 
            for data in all_issues.values() 
            if data["count"] >= threshold
        ]
        
        return consensus
    
    def find_consensus(self, ensemble_results, threshold=0.7, min_consensus=2):
        """
        Find issues using semantic similarity with embeddings.
        
        Args:
            ensemble_results: Dict of {model_name: analysis_text}
            threshold: Cosine similarity threshold (0.7 = 70% similarity)
            min_consensus: Minimum number of models that must agree (default 2/3)
        
        Returns:
            List of consensus issues with model agreement information
        """
        all_issues = []
        
        # Extract all issues with embeddings
        for model_name, analysis in ensemble_results.items():
            if isinstance(analysis, str) and not analysis.startswith("Error:"):
                issues = self.extract_issues(analysis)
                for issue in issues:
                    embedding = self.embedding_model.encode(issue)
                    all_issues.append({
                        'text': issue,
                        'model': model_name,
                        'embedding': embedding
                    })
        
        if not all_issues:
            return []
        
        # Build similarity matrix
        embeddings = np.array([issue['embedding'] for issue in all_issues])
        similarity_matrix = cosine_similarity(embeddings)
        
        # Find consensus clusters using semantic similarity
        consensus_issues = []
        processed = set()
        
        for i in range(len(all_issues)):
            if i in processed:
                continue
            
            # Find all semantically similar issues
            similar_indices = []
            for j in range(len(all_issues)):
                if similarity_matrix[i][j] >= threshold:
                    similar_indices.append(j)
            
            # Check if enough unique models agree
            unique_models = set(all_issues[idx]['model'] for idx in similar_indices)
            
            if len(unique_models) >= min_consensus:
                # Create consensus report
                consensus_issues.append({
                    'issue': all_issues[i]['text'],
                    'models': list(unique_models),
                    'count': len(unique_models),
                    'similarity_scores': [
                        similarity_matrix[i][j] for j in similar_indices if j != i
                    ]
                })
                processed.update(similar_indices)
        
        # Return just the issue text for backward compatibility
        return [item['issue'] for item in consensus_issues]
    
    def find_consensus_detailed(self, ensemble_results, threshold=0.7, min_consensus=2):
        """
        Same as find_consensus but returns detailed information about agreement.
        Useful for debugging and understanding how models agree.
        """
        all_issues = []
        
        # Extract all issues with embeddings
        for model_name, analysis in ensemble_results.items():
            if isinstance(analysis, str) and not analysis.startswith("Error:"):
                issues = self.extract_issues(analysis)
                for issue in issues:
                    embedding = self.embedding_model.encode(issue)
                    all_issues.append({
                        'text': issue,
                        'model': model_name,
                        'embedding': embedding
                    })
        
        if not all_issues:
            return []
        
        # Build similarity matrix
        embeddings = np.array([issue['embedding'] for issue in all_issues])
        similarity_matrix = cosine_similarity(embeddings)
        
        # Find consensus clusters
        consensus_issues = []
        processed = set()
        
        for i in range(len(all_issues)):
            if i in processed:
                continue
            
            # Find all semantically similar issues
            cluster = []
            for j in range(len(all_issues)):
                if similarity_matrix[i][j] >= threshold:
                    cluster.append({
                        'index': j,
                        'text': all_issues[j]['text'],
                        'model': all_issues[j]['model'],
                        'similarity': similarity_matrix[i][j]
                    })
            
            # Check if enough unique models agree
            unique_models = set(item['model'] for item in cluster)
            
            if len(unique_models) >= min_consensus:
                consensus_issues.append({
                    'primary_issue': all_issues[i]['text'],
                    'models_agreeing': list(unique_models),
                    'agreement_count': len(unique_models),
                    'cluster_details': cluster
                })
                processed.update(item['index'] for item in cluster)
        
        return consensus_issues

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
    print("TEST 3: String Matching Consensus (Legacy)")
    print("=" * 60)
    consensus = analyzer.find_consensus_string_matching(result['results'], threshold=2)
    print(f"Issues {2}+ models agree on (string matching):")
    for issue in consensus:
        print(f"  • {issue}")
    
    print("\n" + "=" * 60)
    print("TEST 4: Semantic Similarity Consensus (New)")
    print("=" * 60)
    consensus = analyzer.find_consensus(result['results'], threshold=0.7)
    print(f"Issues with semantic agreement (threshold=0.7):")
    for issue in consensus:
        print(f"  • {issue}")
    
    print("\n" + "=" * 60)
    print("TEST 5: Detailed Consensus Analysis")
    print("=" * 60)
    detailed = analyzer.find_consensus_detailed(result['results'], threshold=0.7)
    for i, cluster in enumerate(detailed, 1):
        print(f"\nConsensus Issue #{i}:")
        print(f"  Primary: {cluster['primary_issue']}")
        print(f"  Models: {', '.join(cluster['models_agreeing'])} ({cluster['agreement_count']}/3)")
        print(f"  Similar findings from other models:")
        for detail in cluster['cluster_details'][1:]:  # Skip primary
            print(f"    - {detail['model']}: {detail['text'][:60]}... (similarity: {detail['similarity']:.2f})")
