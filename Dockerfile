# Stage 1: Builder
FROM python:3.11-slim as builder

WORKDIR /app

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download the AI model into a specific directory for sharing
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Stage 2: Final
FROM python:3.11-slim

WORKDIR /app

# Copy the virtual environment and model cache from the builder stage
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /app/model_cache /app/model_cache

# Ensure the virtual environment is used
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV SENTENCE_TRANSFORMERS_HOME=/app/model_cache

# Copy application code
COPY . .

# Create non-root user for security and ensure they own critical directories
RUN useradd -m -u 1000 appuser && \
  chown -R appuser:appuser /app && \
  chown -R appuser:appuser /opt/venv && \
  chown -R appuser:appuser /app/model_cache

USER appuser

# Expose port (optional metadata, Render uses $PORT)
EXPOSE 8000

# Health check (dynamic port)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import os, requests; port = os.getenv('PORT', '8000'); requests.get(f'http://localhost:{port}/health').raise_for_status()" || exit 1

# Run the application (sh -c is used to expand $PORT)
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
