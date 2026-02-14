# Security Design

## Secret Management

The system adheres to strict secret isolation policies to prevent credential leakage.

1.  **Zero Hardcoded Secrets**: All configuration is injected via environment variables or secure file mounts.
2.  **Secret File Mounting**: Highly sensitive credentials, like the Firebase Service Account, are never stored as environment strings. They are mounted as read-only files in `/etc/secrets/`.
3.  **Environment Isolation**: Development credentials (`SKIP_AUTH=true`) are explicitly disabled in the production environment variables.

## Authentication Flow

### User Authentication (Frontend)
The system uses Firebase Authentication for secure user sessions.
-   **Provider**: Google OAuth.
-   **Verification**: The backend verifies the Firebase ID Token (JWT) on every request using the `firebase-admin` SDK.
-   **Middleware**: A FastAPI dependency ensures that no review can be initiated without a valid user context.

### Webhook Authentication (GitHub)
To prevent unauthorized API usage and DoS attacks on the LLM, the `/github/webhook` endpoint utilizes HMAC-SHA256 signature verification.
-   **Secret**: A shared `GITHUB_WEBHOOK_SECRET`.
-   **Process**: GitHub signs the payload with the secret. The backend re-calculates the hash and compares it using `hmac.compare_digest` to prevent timing attacks.

## API Security

-   **Rate Limiting**: Implemented at the route level using a custom `RateLimiter`. To prevent abuse in a free-tier environment, limits are pinned to the **Firebase User ID**, falling back to IP address only for unauthenticated or webhook events.
-   **Resource Quotas**: Strict limits are enforced at the ingestion layer to prevent credit exhaustion:
    -   `MAX_FILES`: Limits total files in a PR (Default: 50).
    -   `MAX_FILE_SIZE_KB`: Skips files larger than a specific size (Default: 500KB).
    -   `MAX_TOTAL_SIZE_MB`: Rejects repositories exceeding total size (Default: 2MB).
-   **CORS**: Restricted via `CORSMiddleware`. In production, `ALLOWED_ORIGINS` must be set to the explicit frontend domain to prevent Cross-Site Request Forgery.
-   **Payload Validation**: All incoming data is strictly validated against Pydantic models to prevent injection or malformed data processing.

## Infrastructure Hardening

### Docker Security
-   **Non-Root Execution**: The container runs under a dedicated `appuser` with UID 1000. It does not have sudo privileges.
-   **Multi-Stage Build**: Reduces the image size and removes build-time dependencies (like compilers) from the final runtime environment.
-   **Minimal Base Image**: Uses `python:3.11-slim` to reduce the vulnerability surface area.

## Production Checklist

- [ ] `SKIP_AUTH` is set to `false`.
- [ ] `ALLOWED_ORIGINS` is set to the production domain.
- [ ] `GITHUB_WEBHOOK_SECRET` is a high-entropy random string.
- [ ] Firebase service account JSON is mounted in `/etc/secrets/`.
- [ ] Render "Auto-Deploy" is enabled for security patches.
- [ ] Fine-grained GitHub PAT is used with minimal required permissions (Read-only contents, Read/Write Pull Requests).
