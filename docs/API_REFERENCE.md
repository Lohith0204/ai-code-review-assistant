# API Reference

## Authentication

All standard API endpoints (except `/health` and `/github/webhook`) require a Firebase ID Token passed in the Authorization header.

**Header**: `Authorization: Bearer <FIREBASE_ID_TOKEN>`

---

## Endpoints

### 1. Review Local Repository
`POST /review`

Initiates a code review for a directory on the local filesystem (Development use).

**Request Body**:
```json
{
  "directory_path": "string",
  "query": "string (optional)"
}
```

**Response (200 OK)**:
```json
{
  "summary": "string",
  "risks": ["string"],
  "suggestions": ["string"],
  "affected_files": ["string"]
}
```

---

### 2. Review GitHub Pull Request
`POST /github/review/pr`

Manually triggers a review for a specific GitHub Pull Request.

**Request Body**:
```json
{
  "repo_url": "string (e.g., owner/repo)",
  "pr_number": 123,
  "github_token": "string (User PAT)",
  "query": "string (optional)"
}
```

**Response (200 OK)**:
```json
{
  "summary": "string",
  "comments_posted": 1,
  "files_reviewed": ["string"],
  "risks": ["string"],
  "suggestions": ["string"],
  "review_url": "string"
}
```

---

### 3. GitHub Webhook Handler
`POST /github/webhook`

Receiver for GitHub `pull_request` events. Requires HMAC signature.

**Headers**:
- `X-GitHub-Event`: `pull_request`
- `X-Hub-Signature-256`: `sha256=<signature>`
- `X-GitHub-Delivery`: `<guid>`

---

### 4. System Health
`GET /health`

Public endpoint for monitoring and load balancer health checks.

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

---

## Status Codes

| Code | Meaning | Description |
| :--- | :--- | :--- |
| `200` | OK | Success. |
| `401` | Unauthorized | Missing or invalid Token / Webhook Signature. |
| `413` | Payload Too Large | Repository exceeds File Count or Size quotas. |
| `422` | Unprocessable Entity | Invalid request schema. |
| `429` | Too Many Requests | User-pinned or IP-based rate limit exceeded. |
| `500` | Internal Server Error | AI processing or GitHub API failure. |

## Error Responses

```json
{
  "detail": "Descriptive error message"
}
```
