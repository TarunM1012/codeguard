import requests
from config import GITHUB_TOKEN
from config import TEST_REPO, TEST_PR

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
    
    def post_review_comment(self, repo, pr_number, body, commit_id, filepath, line):
            """Post a review comment on a specific line of a PR"""
            url = f"{self.base_url}/repos/{repo}/pulls/{pr_number}/comments"
            
            data = {
                "body": body,
                "commit_id": commit_id,
                "path": filepath,
                "line": line,
                "side": "RIGHT"  # RIGHT = new code, LEFT = old code
            }
            
            response = requests.post(url, headers=self.headers, json=data)
            response.raise_for_status()
            return response.json()
    
    def post_pr_comment(self, repo, pr_number, body):
        """Post a general comment on the PR (not tied to specific line)"""
        url = f"{self.base_url}/repos/{repo}/issues/{pr_number}/comments"
        
        data = {"body": body}
        
        response = requests.post(url, headers=self.headers, json=data)
        response.raise_for_status()
        return response.json()
    
#Testing
if __name__ == "__main__": 
    client = GitHubClient()

    repo = TEST_REPO
    pr_number = TEST_PR

    # TEST 1: Fetch PR files (original test)
    print("=" * 50)
    print("TEST 1: Fetching PR files")
    print("=" * 50)
    try:
        print(f"Fetching PR #{pr_number} from {repo}...")
        files = client.get_pr_files(repo, pr_number)
        print(f"\nFound {len(files)} files:")
        for file in files:
            print(f"  - {file['filename']}")
            print(f"    Status: {file['status']}")
            print(f"    Changes: +{file['additions']} -{file['deletions']}")
            if file.get("patch"):
                print(f"    Patch preview: {file['patch'][:100]}...")
            print()
    except Exception as e:
        print(f"Error: {e}")
    
    # TEST 2: Post comment (new test)
    print("\n" + "=" * 50)
    print("TEST 2: Posting comment to PR")
    print("=" * 50)
    try:
        print("Posting test comment to PR...")
        result = client.post_pr_comment(
            repo, 
            pr_number, 
            "**CodeGuard Test**: This is an automated test comment!"
        )
        print(f"✅ Comment posted! View at: {result['html_url']}")
    except Exception as e:
        print(f"Error: {e}")