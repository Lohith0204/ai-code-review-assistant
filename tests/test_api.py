from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

import os
# Set dummy API key before importing app to prevent OpenAI client validation error
os.environ["OPENAI_API_KEY"] = "dummy"
# Skip Auth for general API tests
os.environ["SKIP_AUTH"] = "true"

from app.main import app
from app.core.models import ReviewResult

client = TestClient(app)
# Define common headers for authorized requests
auth_headers = {"Authorization": "Bearer dummy"}

def test_health_check():
    # Health check is public, no auth needed
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "version": "1.0.0"}

def test_get_me():
    response = client.get("/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "user_id" in data
    assert "email" in data
    assert data["plan"] == "open-source"

@patch("app.api.routes.orchestrator")
def test_review_endpoint(mock_orchestrator):
    # Mock the orchestrator response
    mock_result = ReviewResult(
        summary="Code looks good.",
        risks=["Low risk"],
        suggestions=["Add comments"],
        affected_files=["main.py"]
    )
    mock_orchestrator.run_review.return_value = mock_result

    # Define a valid request payload
    # We use a dummy path, it doesn't need to exist because we might mock os.path.exists too
    # BUT, the route checks os.path.exists.
    # So we should also mock os.path.exists or point to a real path.
    # Let's point to this file's parent directory
    real_path = str(Path(__file__).parent)

    payload = {
        "directory_path": real_path,
        "query": "Check for bugs"
    }

    response = client.post("/review", json=payload, headers=auth_headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["summary"] == "Code looks good."
    assert "Low risk" in data["risks"]
    assert "main.py" in data["affected_files"]

    # Verify orchestrator was called with correct args
    mock_orchestrator.run_review.assert_called_once_with(real_path, "Check for bugs")

def test_review_endpoint_invalid_path():
    payload = {
        "directory_path": "/non/existent/path/xyz",
        "query": "Check for bugs"
    }
    response = client.post("/review", json=payload, headers=auth_headers)
    assert response.status_code == 400
    assert "Directory not found" in response.json()["detail"]

if __name__ == "__main__":
    # Manually run tests if executed as script
    try:
        test_health_check()
        test_get_me()
        # We need to run the patched test carefully if running manually
        # Ideally we use pytest, but let's just use the client logic here for simple run
        print("✅ /health and /me tests passed.")
        print("Run `pytest tests/test_api.py` for full coverage including mocks.")
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
