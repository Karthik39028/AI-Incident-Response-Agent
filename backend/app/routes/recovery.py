from fastapi import APIRouter, HTTPException, Request

from app.services.auth import get_current_user
from app.services.recovery import RecoveryService
from app.services.incident_analysis import IncidentAnalysisService
from app.models.incident import IncidentAnalysisRequest


router = APIRouter(
    prefix="/api/recovery",
    tags=["Recovery"],
)


recovery_service = RecoveryService()
incident_analysis_service = IncidentAnalysisService()


# =========================================================
# CREATE ACTION
# =========================================================

@router.post("/incidents/{incident_id}/action")
def create_recovery_action(
    incident_id: int,
    request: Request,
):
    try:
        user = get_current_user(request)

        recovery = recovery_service.create_action(
            incident_id=incident_id,
            user_id=user["id"],
        )

        return {
            "success": True,
            "recovery": recovery,
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        print("====================================")
        print("CREATE RECOVERY ACTION ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail="Failed to create recovery action",
        )


# =========================================================
# GET ACTION
# =========================================================

@router.get("/actions/{action_id}")
def get_recovery_action(
    action_id: int,
    request: Request,
):
    try:
        user = get_current_user(request)

        recovery = recovery_service.get_action(
            action_id=action_id,
            user_id=user["id"],
        )

        if not recovery:
            raise HTTPException(
                status_code=404,
                detail="Recovery action not found",
            )

        return {
            "success": True,
            "recovery": recovery,
        }

    except HTTPException:
        raise

    except Exception as e:
        print("====================================")
        print("GET RECOVERY ACTION ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail="Failed to load recovery action",
        )


# =========================================================
# APPROVE ACTION
# =========================================================

@router.post("/actions/{action_id}/approve")
def approve_recovery_action(
    action_id: int,
    request: Request,
):
    try:
        user = get_current_user(request)

        recovery = recovery_service.approve_action(
            action_id=action_id,
            user_id=user["id"],
        )

        return {
            "success": True,
            "recovery": recovery,
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        print("====================================")
        print("APPROVE RECOVERY ACTION ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail="Failed to approve recovery action",
        )


# =========================================================
# INVESTIGATE AGAIN
# =========================================================

@router.post("/actions/{action_id}/investigate")
def investigate_again(
    action_id: int,
    analysis_request: IncidentAnalysisRequest,
    request: Request,
):
    """
    Run a new AI investigation after a previously proposed
    investigation has been explicitly approved by a human.

    The new investigation uses:

        New telemetry
        +
        Repository evidence
        +
        Hindsight recall
        +
        LLM reasoning

    After the investigation completes, the original investigation
    action is marked COMPLETED.

    The incident itself is NOT marked RESOLVED here.

    The newly generated diagnosis determines the next step.
    """

    try:

        # =====================================================
        # 1. Authenticate application user
        # =====================================================

        user = get_current_user(request)

        # =====================================================
        # 2. Verify GitHub session
        # =====================================================

        github_token = request.cookies.get(
            "github_session"
        )

        if not github_token:
            raise HTTPException(
                status_code=401,
                detail=(
                    "GitHub session not found. "
                    "Please login again before investigating."
                ),
            )

        # =====================================================
        # 3. Load recovery action
        # =====================================================

        recovery = recovery_service.get_action(
            action_id=action_id,
            user_id=user["id"],
        )

        if not recovery:
            raise HTTPException(
                status_code=404,
                detail="Investigation action not found",
            )

        # =====================================================
        # 4. Make sure this is an investigation action
        # =====================================================

        if recovery["action_type"] != "investigation_required":
            raise HTTPException(
                status_code=400,
                detail=(
                    "This recovery action is not an "
                    "investigation action."
                ),
            )

        # =====================================================
        # 5. Require explicit human approval
        # =====================================================

        if recovery["status"] != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Investigation must be approved before "
                    "running another investigation."
                ),
            )

        # =====================================================
        # 6. Validate basic telemetry
        # =====================================================

        if analysis_request.application_id <= 0:
            raise HTTPException(
                status_code=400,
                detail="Invalid application_id.",
            )

        if not analysis_request.service:
            raise HTTPException(
                status_code=400,
                detail="Service is required.",
            )

        if analysis_request.latencyMs < 0:
            raise HTTPException(
                status_code=400,
                detail="Latency cannot be negative.",
            )

        if analysis_request.errorRate < 0:
            raise HTTPException(
                status_code=400,
                detail="Error rate cannot be negative.",
            )

        if analysis_request.dbConnections < 0:
            raise HTTPException(
                status_code=400,
                detail="Database connections cannot be negative.",
            )

        if analysis_request.dbConnectionLimit < 0:
            raise HTTPException(
                status_code=400,
                detail="Database connection limit cannot be negative.",
            )

        if analysis_request.cpu < 0:
            raise HTTPException(
                status_code=400,
                detail="CPU cannot be negative.",
            )

        if analysis_request.memory < 0:
            raise HTTPException(
                status_code=400,
                detail="Memory cannot be negative.",
            )

        # =====================================================
        # 7. Log investigation
        # =====================================================

        print("====================================")
        print("RUNNING INVESTIGATION AGAIN")
        print("====================================")
        print("Action ID:", action_id)
        print("Previous Incident ID:", recovery["incident_id"])
        print("Application ID:", analysis_request.application_id)
        print("Service:", analysis_request.service)
        print("Latency:", analysis_request.latencyMs)
        print("Error Rate:", analysis_request.errorRate)
        print("DB Connections:", analysis_request.dbConnections)
        print(
            "DB Connection Limit:",
            analysis_request.dbConnectionLimit,
        )
        print("CPU:", analysis_request.cpu)
        print("Memory:", analysis_request.memory)
        print("====================================")

        # =====================================================
        # 8. Run NEW AI investigation
        # =====================================================

        analysis = incident_analysis_service.analyze(
            incident=analysis_request,
            user_id=user["id"],
            github_token=github_token,
        )

        # =====================================================
        # 9. Complete the investigation action
        # =====================================================

        investigation_completion = (
            recovery_service.complete_investigation(
                action_id=action_id,
                user_id=user["id"],
                investigation_result=analysis,
            )
        )

        # =====================================================
        # 10. Return new diagnosis + lifecycle result
        # =====================================================

        return {
            "success": True,

            "message": (
                "Investigation completed using new telemetry, "
                "repository evidence, and Hindsight."
            ),

            "investigation": analysis,

            "investigationCompletion": investigation_completion,

            "previousRecoveryAction": {
                "actionId": recovery["id"],
                "incidentId": recovery["incident_id"],
                "status": recovery["status"],
                "actionType": recovery["action_type"],
            },
        }

    except HTTPException:
        raise

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )

    except Exception as e:
        print("====================================")
        print("INVESTIGATE AGAIN ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail="Failed to run investigation",
        )