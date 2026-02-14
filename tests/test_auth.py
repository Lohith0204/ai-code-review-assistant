from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
import sys
import os
from pathlib import Path

# Add project root to sys.path
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

# Verify Auth using SKIP_AUTH env var for testing
os.environ["SKIP_AUTH"] = "true"
os.environ["OPENAI_API_KEY"] = "dummy"

from app.main import app
from app.core.models import ReviewResult

client = TestClient(app)

def test_auth_protection():
    # If we disable SKIP_AUTH, we should get 401
    os.environ.pop("SKIP_AUTH", None)
    
    # Reload app dependencies might be tricky with client, 
    # but the dependency function reads env var at runtime.
    
    # However, verify_token uses Security(security).
    # TestClient doesn't send auth header by default.
    
    # We need to mock verify_id_token to throw error if we want to test 401
    # But wait, our verify_token implementation checks env var FIRST.
    # So if we unset it, it tries firebase verify.
    # Since we typically don't have properly failing credentials in test env without mocking,
    # it might raise "Invalid authentication credentials".
    
    with patch("app.core.security.auth.verify_id_token") as mock_verify:
        mock_verify.side_effect = Exception("No valid token")
        
        response = client.get("/me")
        # Should be 401 or 403
        assert response.status_code == 401 or response.status_code == 403
        
def test_authenticated_access():
    # Re-enable Mock Auth
    os.environ["SKIP_AUTH"] = "true"
    
    # HTTPBearer requires header presence even if logic skips validation
    headers = {"Authorization": "Bearer dummy_token"}
    response = client.get("/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "test_user"

@patch("app.api.routes.orchestrator")
def test_rate_limiting(mock_orchestrator):
    os.environ["SKIP_AUTH"] = "true"
    
    # Mock review result
    mock_result = ReviewResult(
        summary="Safe", risks=[], suggestions=[], affected_files=[]
    )
    mock_orchestrator.run_review.return_value = mock_result
    
    # We set rate limit to 10 in routes.py
    # Let's hit it 11 times.
    
    payload = {"directory_path": ".", "query": "test"}
    headers = {"Authorization": "Bearer mock_token"}
    
    # We need to ensure we are identified as same user. 
    # verify_token returns "test_user" when SKIP_AUTH is true.
    # RateLimiter uses user_id from request.state.
    
    # Note: verify_token sets request.state.user_id = decoded_token.get("uid") 
    # ONLY if it does not take the SKIP_AUTH path?
    # Wait, looking at security.py:
    # if SKIP_AUTH: return {...} -> checking dependency.
    # It does NOT set request.state.user_id in SKIP_AUTH block.
    # RateLimiter falls back to IP if user_id not set?
    # RateLimiter code: user_id = getattr(request.state, "user_id", request.client.host)
    # So it should work based on IP (TestClient host).
    
    for _ in range(12):
        response = client.post("/review", json=payload, headers=headers)
        if response.status_code == 429:
            break
            
    assert response.status_code == 429, "Rate limit should be triggered"

if __name__ == "__main__":
    try:
        test_auth_protection()
        test_authenticated_access()
        test_rate_limiting()
        print("✅ Auth & Safety tests passed.")
    except Exception as e:
        print(f"❌ Test failed: {e}")
