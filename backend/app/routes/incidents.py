from fastapi import APIRouter, HTTPException

from app.models.incident import IncidentAnalysisRequest
from app.services.incident_analysis import IncidentAnalysisService


router = APIRouter(
    prefix="/api/incidents",
    tags=["Incidents"]
)

analysis_service = IncidentAnalysisService()


@router.post("/analyze")
def analyze_incident(incident: IncidentAnalysisRequest):

    try:
        return analysis_service.analyze(incident)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )