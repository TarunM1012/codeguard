import requests
import json
from config import TEST_REPO, TEST_PR

# More complete webhook payload
payload = {
    "action": "opened",
    "pull_request": {
        "number": TEST_PR,
        "head": {
            "sha": "abc123def456"  # Added this!
        }
    },
    "repository": {
        "full_name": TEST_REPO
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