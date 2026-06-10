"""MarginTrust AI FastAPI application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import actions_router, agent_router, dashboard_router

settings = get_settings()

app = FastAPI(
    title="MarginTrust AI",
    description="Gemini-powered revenue leakage detection agent for B2B SaaS",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router.router, prefix="/api/agent", tags=["Agent"])
app.include_router(dashboard_router.router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(actions_router.router, prefix="/api/actions", tags=["Actions"])


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "margintrust-ai"}

