from fastapi import APIRouter, HTTPException, Depends
from app.core.models import ReviewRequest, ReviewResult
from app.services.rag_orchestrator import RAGOrchestrator
from app.core.security import verify_token
from app.core.rate_limit import RateLimiter
import os

router = APIRouter()
orchestrator = RAGOrchestrator()
rate_limiter = RateLimiter(requests_per_minute=10)

@router.post("/review", response_model=ReviewResult, summary="Review a local repository")
async def review_repo(
    request: ReviewRequest, 
    user=Depends(verify_token),
    allowed=Depends(rate_limiter)
):
    """Analyzes a local repository and returns a structured code review."""
    if not os.path.exists(request.directory_path):
        raise HTTPException(status_code=400, detail=f"Directory not found: {request.directory_path}")
    
    try:
        result = orchestrator.run_review(request.directory_path, request.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", summary="Health Check")
async def health_check():
    """Returns service health status."""
    return {"status": "healthy", "version": "1.0.0"}

@router.get("/me", summary="Get User Profile")
async def get_me(user=Depends(verify_token)):
    """Returns the authenticated user's profile."""
    return {
        "user_id": user.get("uid"),
        "email": user.get("email"),
        "plan": "open-source",
        "requests_remaining": "unlimited"
    }
