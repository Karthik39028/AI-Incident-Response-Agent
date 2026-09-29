from fastapi import APIRouter, HTTPException, Request

from app.models.incident import IncidentAnalysisRequest
from app.services.incident_analysis import IncidentAnalysisService
from app.services.auth import get_current_user


router = APIRouter(
    prefix="/api/incidents",
    tags=["Incidents"]
)

analysis_service = IncidentAnalysisService()


@router.post("/analyze")
def analyze_incident(
    incident: IncidentAnalysisRequest,
    request: Request
):
    try:
        user = get_current_user(request)

        github_token = request.cookies.get(
            "github_session"
        )

        if not github_token:
            raise HTTPException(
                status_code=401,
                detail="GitHub session not found"
            )

        return analysis_service.analyze(
            incident=incident,
            user_id=user["id"],
            github_token=github_token,
        )

    except HTTPException:
        raise

    except Exception as e:
        print("====================================")
        print("INCIDENT ANALYSIS ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )