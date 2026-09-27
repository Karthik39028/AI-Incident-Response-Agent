from fastapi import APIRouter, HTTPException
from app.services.hindsight import HindsightService

router = APIRouter(
    prefix="/api/memory",
    tags=["Memory"]
)

hindsight = HindsightService()


@router.post("/seed")
def seed_incident():

    incident = """
    Incident INC-0871 occurred in the payment service.

    Symptoms:
    Payment latency increased from approximately 200ms to 8.7 seconds.
    Error rate increased above 15%.
    Database connection utilization reached 96%.

    Root Cause:
    Database connection pool exhaustion.

    Remediation:
    The database connection pool was increased from 20 to 50 connections.

    Outcome:
    The incident was successfully resolved.
    Latency returned to approximately 240ms.
    Recovery took approximately 7 minutes.

    A service restart was considered but was not used as the final remediation.
    """

    try:
        return hindsight.retain(incident)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/search")
def search_incident(query: str):

    try:
        return hindsight.recall(query)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )