from fastapi import FastAPI

from app.routes.memory import router as memory_router
from app.routes.incidents import router as incidents_router
from app.routes.ai import router as ai_router

app = FastAPI(
    title="AI Incident Response Agent",
    description="Real-Time AI Incident Response and Learning Agent",
    version="1.0.0"
)

app.include_router(ai_router)
app.include_router(memory_router)
app.include_router(incidents_router)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "AI Incident Response Agent"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }