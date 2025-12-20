import requests
import json

# More complete webhook payload
payload = {
    "action": "opened",
    "pull_request": {
        "number": 2,
        "head": {
            "sha": "abc123def456"  # Added this!
        }
    },
    "repository": {
        "full_name": "TarunM1012/AI-stock-report-generator"
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