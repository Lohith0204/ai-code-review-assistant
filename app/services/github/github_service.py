from github import Github, GithubException
from typing import List, Dict, Optional
import tempfile
import os
import shutil

class GitHubService:
    """Service for interacting with GitHub API."""
    
    def __init__(self, access_token: str):
        """Initialize with GitHub personal access token."""
        self.github = Github(access_token)
        
    def get_pr_info(self, repo_name: str, pr_number: int) -> Dict:
        """Get basic PR information."""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            return {
                "title": pr.title,
                "state": pr.state,
                "base_branch": pr.base.ref,
                "head_branch": pr.head.ref,
                "author": pr.user.login,
                "url": pr.html_url
            }
        except GithubException as e:
            raise Exception(f"Failed to fetch PR info: {e}")
    
    def get_changed_files(self, repo_name: str, pr_number: int) -> List[Dict[str, str]]:
        """Get list of files changed in the PR with their content."""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            
            changed_files = []
            for file in pr.get_files():
                if self._is_code_file(file.filename):
                    try:
                        content = repo.get_contents(file.filename, ref=pr.head.sha)
                        file_content = content.decoded_content.decode('utf-8')
                        
                        changed_files.append({
                            "filename": file.filename,
                            "status": file.status,
                            "additions": file.additions,
                            "deletions": file.deletions,
                            "patch": file.patch if hasattr(file, 'patch') else None,
                            "content": file_content
                        })
                    except Exception as e:
                        print(f"Warning: Could not fetch content for {file.filename}: {e}")
                        continue
            
            return changed_files
        except GithubException as e:
            raise Exception(f"Failed to fetch changed files: {e}")
    
    def download_pr_files(self, repo_name: str, pr_number: int) -> str:
        """Download changed files to a temporary directory."""
        temp_dir = tempfile.mkdtemp(prefix="pr_review_")
        
        try:
            changed_files = self.get_changed_files(repo_name, pr_number)
            
            for file_info in changed_files:
                if file_info["status"] != "removed":
                    file_path = os.path.join(temp_dir, file_info["filename"])
                    os.makedirs(os.path.dirname(file_path), exist_ok=True)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(file_info["content"])
            
            return temp_dir
        except Exception as e:
            shutil.rmtree(temp_dir, ignore_errors=True)
            raise e
    
    def post_review_comment(self, repo_name: str, pr_number: int, 
                           body: str, commit_id: str = None) -> str:
        """Post a general review comment on the PR."""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            comment = pr.create_issue_comment(body)
            return comment.html_url
        except GithubException as e:
            raise Exception(f"Failed to post comment: {e}")
    
    def post_review_comments(self, repo_name: str, pr_number: int, 
                            comments: List[Dict[str, any]]) -> List[str]:
        """Post multiple inline review comments."""
        try:
            repo = self.github.get_repo(repo_name)
            pr = repo.get_pull(pr_number)
            commits = list(pr.get_commits())
            latest_commit = commits[-1]
            
            posted_urls = []
            for comment in comments:
                try:
                    review_comment = pr.create_review_comment(
                        body=comment["body"],
                        commit=latest_commit,
                        path=comment["path"],
                        line=comment["line"]
                    )
                    posted_urls.append(review_comment.html_url)
                except GithubException as e:
                    print(f"Warning: Could not post comment on {comment['path']}:{comment['line']}: {e}")
                    continue
            
            return posted_urls
        except GithubException as e:
            raise Exception(f"Failed to post review comments: {e}")
    
    def _is_code_file(self, filename: str) -> bool:
        """Check if file is a code file (not binary/image)."""
        code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.cpp', '.c', '.h',
            '.go', '.rs', '.rb', '.php', '.cs', '.swift', '.kt', '.scala',
            '.sh', '.bash', '.yml', '.yaml', '.json', '.xml', '.html', '.css',
            '.sql', '.r', '.m', '.dart', '.lua', '.pl', '.vim'
        }
        _, ext = os.path.splitext(filename)
        return ext.lower() in code_extensions
