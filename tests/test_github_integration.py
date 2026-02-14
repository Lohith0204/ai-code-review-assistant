from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Set environment variables for testing
os.environ["SKIP_AUTH"] = "true"
os.environ["OPENAI_API_KEY"] = "dummy"

from app.main import app
from app.core.models import PRReviewResult

client = TestClient(app)
auth_headers = {"Authorization": "Bearer dummy"}

@patch("app.api.github_routes.GitHubService")
@patch("app.api.github_routes.RAGOrchestrator")
def test_pr_review_endpoint(mock_orchestrator_class, mock_github_service_class):
    # Mock GitHub service
    mock_github = MagicMock()
    mock_github_service_class.return_value = mock_github
    
    mock_github.get_pr_info.return_value = {
        "title": "Test PR",
        "state": "open",
        "base_branch": "main",
        "head_branch": "feature",
        "author": "testuser",
        "url": "https://github.com/owner/repo/pull/1"
    }
    
    mock_github.get_changed_files.return_value = [
        {
            "filename": "test.py",
            "status": "modified",
            "additions": 10,
            "deletions": 5,
            "content": "def test(): pass"
        }
    ]
    
    mock_github.download_pr_files.return_value = "/tmp/test"
    mock_github.post_review_comment.return_value = "https://github.com/owner/repo/pull/1#comment"
    
    # Mock RAG orchestrator
    mock_orch = MagicMock()
    mock_orchestrator_class.return_value = mock_orch
    
    from app.core.models import ReviewResult
    mock_orch.run_review.return_value = ReviewResult(
        summary="Code looks good",
        risks=["Minor issue"],
        suggestions=["Add tests"],
        affected_files=["test.py"]
    )
    
    # Make request
    payload = {
        "repo_url": "owner/repo",
        "pr_number": 1,
        "github_token": "fake_token",
        "query": "Review this PR"
    }
    
    response = client.post("/github/review/pr", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Code looks good"
    assert data["comments_posted"] == 1
    assert "test.py" in data["files_reviewed"]
    assert data["review_url"] is not None

@patch("app.api.github_routes.GitHubService")
def test_pr_review_closed_pr(mock_github_service_class):
    mock_github = MagicMock()
    mock_github_service_class.return_value = mock_github
    
    mock_github.get_pr_info.return_value = {
        "state": "closed",
        "url": "https://github.com/owner/repo/pull/1"
    }
    
    payload = {
        "repo_url": "owner/repo",
        "pr_number": 1,
        "github_token": "fake_token"
    }
    
    response = client.post("/github/review/pr", json=payload, headers=auth_headers)
    
    assert response.status_code == 400
    assert "closed" in response.json()["detail"]

if __name__ == "__main__":
    try:
        test_pr_review_endpoint()
        test_pr_review_closed_pr()
        print("✅ GitHub integration tests passed.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
