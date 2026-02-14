import os
import uuid
from dotenv import load_dotenv
from fastapi import FastAPI, Request

# Load environment variables from .env file locally
load_dotenv()
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.api.github_routes import router as github_router
from app.core.usage_logging import UsageLoggingMiddleware

app = FastAPI(
    title="AI Code Review Assistant",
    description="Automated code review agent powered by RAG and LLMs.",
    version="1.0.0"
)

# --- Startup Events ---
@app.on_event("startup")
async def startup_event():
    # Pre-warm the RAG orchestrator (loads the AI model into memory)
    from app.services.rag_orchestrator import RAGOrchestrator
    print("Pre-warming AI models...")
    RAGOrchestrator()
    print("AI models ready to serve.")

# --- Security: CORS ---
# In production, restrict to exact frontend domain and disable credentials for unknown origins.
# Example: ALLOWED_ORIGINS=https://a.com, https://b.com
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,  # Consider disabling for unknown origins in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Observability: Request ID ---
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

app.add_middleware(UsageLoggingMiddleware)

app.include_router(router)
app.include_router(github_router)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Serve index.html at root
from fastapi.responses import FileResponse

@app.get("/")
async def read_root():
    return FileResponse("frontend/index.html")
