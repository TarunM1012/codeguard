import requests
import json

class OllamaClient:
    def __init__(self, base_url='http://localhost:11434'):
        self.base_url = base_url

    def generate(self, model, prompt):
        """Send prompt to Ollama, get response."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False
        }

        try:
            response = requests.post(url, json=payload, timeout=120)
            response.raise_for_status()
            return response.json()["response"]
        except requests.exceptions.RequestException as e:
            return f"Error: {str(e)}"
        
    def test_connection(self):
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.base_url}/api/tags")
            return response.status_code == 200
        except:
            return False
        
#Testing
        
if __name__ == "__main__":
    from config import AVAILABLE_MODELS
    
    client = OllamaClient()
    
    # Check connection
    if not client.test_connection():
        print("Ollama not running! Start it with: ollama serve")
        exit(1)
    
    print("Ollama connected!\n")
    
    # Test all models
    test_code = """
def divide(a, b):
    return a / b
"""
    
    prompt = f"""You are a code reviewer. Find bugs in this code:

{test_code}

List issues in one line."""
    
    for name, model in AVAILABLE_MODELS.items():
        print(f"Testing {name} ({model})...")
        try:
            response = client.generate(model, prompt)
            print(f"   Response: {response[:100]}...")
            print(f"   {name} works!\n")
        except Exception as e:
            print(f"   {name} failed: {e}\n")