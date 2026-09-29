from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes.github_auth import router as github_auth_router
from app.routes.memory import router as memory_router
from app.routes.incidents import router as incidents_router
from app.routes.ai import router as ai_router
from app.routes.applications import router as applications_router
from app.routes.recovery import router as recovery_router
from app.services.database import initialize_database
app = FastAPI(
    title="AI Incident Response Agent",
    description="Real-Time AI Incident Response and Learning Agent",
    version="1.0.0"
)


initialize_database()

# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],
)


# ============================================================
# ROUTES
# ============================================================

app.include_router(github_auth_router)
app.include_router(memory_router)
app.include_router(incidents_router)
app.include_router(ai_router)
app.include_router(applications_router)
app.include_router(recovery_router)

@app.get("/")
def root():

    return {
        "status": "online",
        "service": "AI Incident Response Agent",
        "version": "1.0.0"
    }


@app.get("/health")
def health():

    return {
        "status": "healthy"
    }