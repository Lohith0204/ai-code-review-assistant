# Deployment Guide

This document provides instructions for deploying the AI Code Review Assistant to production using Docker. The recommended platform is Render, but the configuration is compatible with any OCI-compliant orchestrator (Kubernetes, AWS ECS).

## Docker Configuration

The project utilizes a multi-stage Docker build to minimize the attack surface and image size.

-   **Stage 1 (Builder)**: Installs dependencies and prepares the environment.
-   **Stage 2 (Final)**: Copies only necessary artifacts and runs as a non-root `appuser`.

**Build Command**:
```bash
docker build -t ai-code-review-assistant .
```

## Render Deployment (Recommended)

### 1. Create Web Service
1.  Connect your GitHub repository to Render.
2.  Select **Docker** as the Runtime.
3.  Select a **Starter** plan or higher (recommended for model performance).

### 2. Secret Mounting (Firebase)
The application expects the Firebase service account key at a fixed file path for security.
1.  In Render, go to the **Secrets** tab.
2.  Create a secret file named `firebase-service-account.json`.
3.  Paste the raw contents of your Firebase JSON key.
4.  Render will automatically mount this at `/etc/secrets/firebase-service-account.json`.

### 3. Environment Variables

| Key | Value |
| :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI API Key |
| `GITHUB_TOKEN` | Fine-grained PAT with repo write access |
| `GITHUB_WEBHOOK_SECRET` | A unique string for HMAC verification |
| `ALLOWED_ORIGINS` | Your production URL (e.g., `https://app.onrender.com`) |
| `SKIP_AUTH` | `false` |
| `MAX_FILES` | Max files per review (Abuse prevention) |
| `MAX_FILE_SIZE_KB` | Max size per individual file in KB |
| `MAX_TOTAL_SIZE_MB` | Max total repo size allowed in MB |
| `RATE_LIMIT_RPM` | Requests per minute per user/IP |

## GitHub Webhook Integration

To enable automated reviews, configure the webhook in your GitHub repository:

1.  **URL**: `https://<your-render-url>/github/webhook`
2.  **Content type**: `application/json`
3.  **Secret**: The value you set for `GITHUB_WEBHOOK_SECRET`.
4.  **Events**: Select "Let me select individual events" -> **Pull requests**.

## Monitoring

-   **Logs**: Render provides real-time stdout/stderr capture. All critical review operations are logged with `X-GitHub-Delivery` and `X-Request-ID` for correlation.
-   **Health Checks**: The service provides a `/health` endpoint. The Dockerfile includes a built-in healthcheck:
    `CMD python -c "import requests; requests.get('http://localhost:8000/health').raise_for_status()"`

## Troubleshooting

### Container Crashes on Startup
-   **Cause**: Missing `OPENAI_API_KEY` or invalid Firebase secret path.
-   **Fix**: Check Render logs and verify the secret mount path `/etc/secrets/firebase-service-account.json`.

### Webhook 401 Unauthorized
-   **Cause**: HMAC signature mismatch.
-   **Fix**: Ensure `GITHUB_WEBHOOK_SECRET` is identical in both GitHub and Render settings.

### Slow First Review
-   **Cause**: The system lazy-loads the 500MB embedding model during the first request after startup.
-   **Fix**: This is expected behavior. Subsequent reviews will be significantly faster.
