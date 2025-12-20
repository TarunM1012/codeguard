#TEST FILE TO CHECK SERVER.PY
import requests
import json

# Simulate GitHub webhook
payload = {
    "action": "opened",
    "pull_request": {
        "number": 1,  # Your PR number
    },
    "repository": {
        "full_name": "TarunM1012/AI-stock-report-generator"  # Your repo
    }
}

print("Sending webhook to server...")
response = requests.post(
    "http://localhost:8000/webhook",
    json=payload,
    headers={"X-GitHub-Event": "pull_request"}
)

print("\nResponse:")
print(json.dumps(response.json(), indent=2))