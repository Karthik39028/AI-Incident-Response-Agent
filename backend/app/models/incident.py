from pydantic import BaseModel


class IncidentAnalysisRequest(BaseModel):

    application_id: int

    service: str

    latencyMs: float

    errorRate: float

    dbConnections: int

    dbConnectionLimit: int

    cpu: float

    memory: float