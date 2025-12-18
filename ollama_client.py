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
    client = OllamaClient()

    #Check connection
    if not client.test_connection():
        print("Ollama server is not running. Start with : ollama serve")
        exit(1)

    print("Ollama server is running.")

    #Test prompt
    test_code = """
def devide(a,b):
    return a / b"""

    prompt = f"""You are a expert code reviewerFind the bug in the following code:\n{test_code}\n List any issues."""
    print("Testing DeepSeek Coder...")
    response = client.generate("deepseek-coder:6.7b", prompt)
    print(response)