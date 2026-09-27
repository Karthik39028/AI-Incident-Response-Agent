from pydantic import BaseModel


class IncidentAnalysisRequest(BaseModel):
    service: str
    latencyMs: float
    errorRate: float
    dbConnections: int
    dbConnectionLimit: int
    cpu: float
    memory: float