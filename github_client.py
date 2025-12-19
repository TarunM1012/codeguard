import requests
from config import GITHUB_TOKEN

#Creating a "client" object to interact with the GitHub API
class GitHubClient:
    def __init__(self):
        self.token = GITHUB_TOKEN
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {self.token}", 
            "Accept": "application/vnd.github.v3+json"
        }

#Get PR files and file content
    def get_pr_files(self, repo, pr_number):
        """Get all files changed in a PR"""
        url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/files"

        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
#Step 1: Build URL for specific file - Step 2: Add ref parameter - Step 3: Decode the content
    
    def get_file_content(self, repo, filepath, ref):
        """Get the content of a specific file"""
        url = f"{self.base_url}/repos/{repo}/contents/{filepath}"
        params = {"ref": ref}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()

        import base64
        content = response.json()["content"]
        return base64.b64decode(content).decode('utf-8')
    
#Testing
if __name__ == "__main__": 
    client = GitHubClient()

    # tests with my repo
    repo = "TarunM1012/AI-stock-report-generator"
    pr_number = 1

    try:
        print(f"Fetching PR #{pr_number} from {repo}...")
        files = client.get_pr_files(repo, pr_number)
        for file in files:
            print(f"- {file['filename']}")
            print(f" Status: {file['status']}")
            print(f" Changes: +{file['additions']} -{file['deletions']}")

            if file.get("patch"):
                print(f" Patch preview: {file['patch'][:100]}...")
            print()

    except Exception as e:
        print(f"Error: {e}")
