import hmac
import hashlib
import json
import os
import shutil
from fastapi import APIRouter, HTTPException, Depends, Request, Header
from app.core.models import PRReviewRequest, PRReviewResult
from app.services.github.github_service import GitHubService
from app.services.rag_orchestrator import RAGOrchestrator
from app.core.security import verify_token
from app.core.rate_limit import RateLimiter

from app.core.usage_logging import logger

router = APIRouter(prefix="/github", tags=["GitHub Integration"])
rate_limiter = RateLimiter(requests_per_minute=5)

WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "change-me-in-production")

async def verify_signature(request: Request, x_hub_signature_256: str = Header(None)):
    """Verify GitHub webhook signature."""
    if not x_hub_signature_256:
        raise HTTPException(status_code=401, detail="X-Hub-Signature-256 missing")
    
    body = await request.body()
    signature = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    expected_signature = f"sha256={signature}"
    if not hmac.compare_digest(expected_signature, x_hub_signature_256):
        raise HTTPException(status_code=401, detail="Invalid signature")

@router.post("/webhook", summary="GitHub Webhook handler")
async def github_webhook(
    request: Request,
    verify=Depends(verify_signature)
):
    """Handle incoming GitHub webhooks for automated reviews."""
    payload = await request.json()
    event = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery", "N/A")
    request_id = getattr(request.state, "request_id", "N/A")
    
    logger.info(f"GITHUB-WEBHOOK: received event={event}, delivery_id={delivery_id}, request_id={request_id}")
    
    if event != "pull_request":
        return {"status": "ignored", "reason": f"Event {event} not handled"}
    
    action = payload.get("action")
    if action not in ["opened", "synchronize"]:
        return {"status": "ignored", "reason": f"Action {action} not handled"}
    
    pr_data = payload.get("pull_request")
    repo_url = payload.get("repository", {}).get("full_name")
    pr_number = pr_data.get("number")
    
    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN not configured for automated reviews")
    
    temp_dir = None
    try:
        github_service = GitHubService(github_token)
        temp_dir = github_service.download_pr_files(repo_url, pr_number)
        
        orchestrator = RAGOrchestrator()
        review_result = orchestrator.run_review(temp_dir, "Perform an automated code review for security and quality.")
        
        comment_body = f"""## 🤖 Automated AI Code Review
        
**Summary:** {review_result.summary}

### 🚨 Risks Identified
{chr(10).join(f'- {risk}' for risk in review_result.risks) if review_result.risks else '- No major risks identified'}

### 💡 Suggestions
{chr(10).join(f'- {suggestion}' for suggestion in review_result.suggestions) if review_result.suggestions else '- No suggestions at this time'}

---
*Powered by AI Code Review Assistant*
"""
        github_service.post_review_comment(repo_url, pr_number, comment_body)
        
        return {"status": "success", "action": "review_posted"}
        
    except Exception as e:
        logger.error(f"GITHUB-WEBHOOK-ERROR: delivery_id={delivery_id}, error={e}", exc_info=True)
        return {"status": "error", "detail": str(e)}
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)

@router.post("/review/pr", response_model=PRReviewResult, summary="Review a GitHub Pull Request")
async def review_pull_request(
    request: PRReviewRequest,
    user=Depends(verify_token),
    allowed=Depends(rate_limiter)
):
    """Automatically review a GitHub PR and post feedback as a comment."""
    temp_dir = None
    
    try:
        github_service = GitHubService(request.github_token)
        pr_info = github_service.get_pr_info(request.repo_url, request.pr_number)
        
        if pr_info["state"] != "open":
            raise HTTPException(
                status_code=400, 
                detail=f"PR #{request.pr_number} is {pr_info['state']}, not open"
            )
        
        changed_files = github_service.get_changed_files(request.repo_url, request.pr_number)
        
        if not changed_files:
            return PRReviewResult(
                summary="No code files to review in this PR.",
                comments_posted=0,
                files_reviewed=[],
                review_url=pr_info["url"]
            )
        
        temp_dir = github_service.download_pr_files(request.repo_url, request.pr_number)
        orchestrator = RAGOrchestrator()
        review_result = orchestrator.run_review(temp_dir, request.query)
        
        comment_body = f"""## 🤖 AI Code Review
        
**Summary:** {review_result.summary}

### 🚨 Risks Identified
{chr(10).join(f'- {risk}' for risk in review_result.risks) if review_result.risks else '- No major risks identified'}

### 💡 Suggestions
{chr(10).join(f'- {suggestion}' for suggestion in review_result.suggestions) if review_result.suggestions else '- No suggestions at this time'}

### 📁 Files Reviewed
{chr(10).join(f'- `{file["filename"]}`' for file in changed_files)}

---
*Powered by AI Code Review Assistant*
"""
        
        comment_url = github_service.post_review_comment(
            request.repo_url,
            request.pr_number,
            comment_body
        )
        
        return PRReviewResult(
            summary=review_result.summary,
            comments_posted=1,
            files_reviewed=[f["filename"] for f in changed_files],
            risks=review_result.risks,
            suggestions=review_result.suggestions,
            review_url=comment_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR review failed: {str(e)}")
    
    finally:
        if temp_dir:
            shutil.rmtree(temp_dir, ignore_errors=True)
