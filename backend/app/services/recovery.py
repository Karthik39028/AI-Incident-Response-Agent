from typing import Any, Dict, Optional

import requests
from fastapi import HTTPException

from app.database import get_connection
from app.services.hindsight import HindsightService


class RecoveryService:
    """
    Controls incident recovery.

    Recovery lifecycle:

        PENDING_APPROVAL
              ↓
           APPROVED
              ↓
          EXECUTING
              ↓
          VERIFYING
              ↓
        ┌─────┴─────┐
        ↓           ↓
     COMPLETED    FAILED
        ↓           ↓
     RESOLVED   INVESTIGATION_REQUIRED

    Safety rules:

    1. investigation_required actions never modify production.
    2. State-changing recovery always requires human approval.
    3. Recovery is allowed only for confirmed/supported diagnoses.
    4. Code/config changes are never blindly executed.
    5. Operational execution is restricted to explicitly supported
       operations.
    6. Failed/unverified recovery is NOT stored as confirmed
       Hindsight learning.
    7. Only successfully executed AND verified recovery is retained
       as confirmed recovery learning.
    """

    ALLOWED_ACTION_TYPES = {
        "code_change",
        "configuration_change",
        "operational_action",
        "investigation_required",
    }

    SAFE_OPERATIONAL_ACTIONS = {
        "retry",
        "restart",
        "rollback",
        "refresh",
    }

    def __init__(self):
        self.hindsight = HindsightService()

    # ================================================================
    # CREATE RECOVERY ACTION
    # ================================================================

    def create_action(
        self,
        incident_id: int,
        user_id: int,
    ) -> Dict[str, Any]:

        incident = self._get_incident_for_user(
            incident_id=incident_id,
            user_id=user_id,
        )

        if not incident:
            raise HTTPException(
                status_code=404,
                detail="Incident not found",
            )

        recommendation_type = (
            incident.get("recommendation_type")
            or ""
        ).strip().lower()

        recommendation_action = (
            incident.get("recommendation_action")
            or ""
        ).strip()

        recommendation_reason = (
            incident.get("recommendation_reason")
            or ""
        ).strip()

        if recommendation_type not in self.ALLOWED_ACTION_TYPES:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported recommendation type: "
                    f"{recommendation_type}"
                ),
            )

        # ------------------------------------------------------------
        # Safety rule:
        #
        # Do not create remediation for an unconfirmed diagnosis.
        #
        # Investigation actions are allowed because they do not
        # modify production state.
        # ------------------------------------------------------------

        diagnosis_status = incident.get("diagnosis_status")

        if recommendation_type != "investigation_required":
            if diagnosis_status not in {
                "confirmed",
                "supported",
            }:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Recovery cannot be created because the "
                        f"diagnosis status is '{diagnosis_status}'. "
                        "The incident must have a confirmed or "
                        "supported diagnosis before remediation "
                        "is proposed."
                    ),
                )

        # ------------------------------------------------------------
        # Prevent duplicate active actions for the same incident.
        # ------------------------------------------------------------

        existing_action = self._get_active_action_for_incident(
            incident_id=incident_id,
        )

        if existing_action:
            return {
                "action": existing_action,
                "message": (
                    "An active recovery action already exists "
                    "for this incident."
                ),
            }

        # ------------------------------------------------------------
        # Investigation action
        # ------------------------------------------------------------

        if recommendation_type == "investigation_required":

            action_description = (
                recommendation_action
                or "Additional investigation is required."
            )

            action_id = self._insert_action(
                incident_id=incident_id,
                action_type="investigation_required",
                action_description=action_description,
                target=incident.get("service"),
                status="INVESTIGATION_PENDING",
                requires_approval=True,
            )

            self._update_incident_status(
                incident_id=incident_id,
                status="INVESTIGATION_REQUIRED",
            )

            return {
                "action": {
                    "id": action_id,
                    "incidentId": incident_id,
                    "actionType": "investigation_required",
                    "actionDescription": action_description,
                    "target": incident.get("service"),
                    "status": "INVESTIGATION_PENDING",
                    "requiresApproval": True,
                },
                "message": (
                    "Investigation action created. "
                    "Human approval is required before "
                    "investigation."
                ),
            }

        # ------------------------------------------------------------
        # Normal recovery action
        #
        # IMPORTANT:
        # Never trust the LLM's requiresApproval value for a
        # state-changing operation.
        #
        # Every remediation requires explicit human approval.
        # ------------------------------------------------------------

        action_description = (
            recommendation_action
            or "Recovery action proposed by incident analysis."
        )

        action_id = self._insert_action(
            incident_id=incident_id,
            action_type=recommendation_type,
            action_description=action_description,
            target=incident.get("service"),
            status="PENDING_APPROVAL",
            requires_approval=True,
        )

        self._update_incident_status(
            incident_id=incident_id,
            status="RECOVERY_PROPOSED",
        )

        return {
            "action": {
                "id": action_id,
                "incidentId": incident_id,
                "actionType": recommendation_type,
                "actionDescription": action_description,
                "reason": recommendation_reason,
                "target": incident.get("service"),
                "status": "PENDING_APPROVAL",
                "requiresApproval": True,
            },
            "message": (
                "Recovery action created. "
                "Explicit human approval is required."
            ),
        }

    # ================================================================
    # GET ACTION
    # ================================================================

    def get_action(
        self,
        action_id: int,
        user_id: int,
    ) -> Dict[str, Any]:

        connection = get_connection()

        try:
            cursor = connection.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT
                    ra.*,
                    i.application_id,
                    i.user_id AS incident_user_id,
                    i.service,
                    i.status AS incident_status,
                    i.root_cause,
                    i.confidence,
                    i.diagnosis_status
                FROM recovery_actions ra
                INNER JOIN incidents i
                    ON i.id = ra.incident_id
                WHERE ra.id = %s
                  AND i.user_id = %s
                LIMIT 1
                """,
                (
                    action_id,
                    user_id,
                ),
            )

            action = cursor.fetchone()

            cursor.close()

            if not action:
                raise HTTPException(
                    status_code=404,
                    detail="Recovery action not found",
                )

            return action

        finally:
            connection.close()

    # ================================================================
    # APPROVE ACTION
    # ================================================================

    def approve_action(
        self,
        action_id: int,
        user_id: int,
    ) -> Dict[str, Any]:

        action = self.get_action(
            action_id=action_id,
            user_id=user_id,
        )

        action_type = (
            action.get("action_type")
            or ""
        ).strip().lower()

        current_status = (
            action.get("status")
            or ""
        ).strip().upper()

        # ------------------------------------------------------------
        # Investigation approval
        # ------------------------------------------------------------

        if action_type == "investigation_required":

            if current_status != "INVESTIGATION_PENDING":
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Investigation action cannot be approved "
                        f"from status '{current_status}'."
                    ),
                )

            connection = get_connection()

            try:
                cursor = connection.cursor()

                cursor.execute(
                    """
                    UPDATE recovery_actions
                    SET
                        status = 'APPROVED',
                        approved_by = %s,
                        approved_at = CURRENT_TIMESTAMP,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                    """,
                    (
                        user_id,
                        action_id,
                    ),
                )

                connection.commit()
                cursor.close()

            finally:
                connection.close()

            return {
                "actionId": action_id,
                "status": "APPROVED",
                "nextStep": "INVESTIGATE_AGAIN",
                "message": (
                    "Investigation approved. "
                    "Run the investigation again with "
                    "current evidence."
                ),
            }

        # ------------------------------------------------------------
        # Normal recovery approval
        # ------------------------------------------------------------

        if current_status != "PENDING_APPROVAL":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Recovery action cannot be approved "
                    f"from status '{current_status}'."
                ),
            )

        # ------------------------------------------------------------
        # Re-check diagnosis before execution.
        #
        # This prevents a stale recovery action from being executed
        # after the diagnosis changed.
        # ------------------------------------------------------------

        diagnosis_status = action.get("diagnosis_status")

        if diagnosis_status not in {
            "confirmed",
            "supported",
        }:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Recovery cannot be approved because the "
                    f"diagnosis status is '{diagnosis_status}'. "
                    "Only confirmed or supported diagnoses may "
                    "be executed."
                ),
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE recovery_actions
                SET
                    status = 'EXECUTING',
                    approved_by = %s,
                    approved_at = CURRENT_TIMESTAMP,
                    started_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND status = 'PENDING_APPROVAL'
                """,
                (
                    user_id,
                    action_id,
                ),
            )

            if cursor.rowcount != 1:
                connection.rollback()

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Recovery action was already processed "
                        "or is no longer pending approval."
                    ),
                )

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = 'RECOVERY_EXECUTING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    action["incident_id"],
                ),
            )

            connection.commit()
            cursor.close()

        finally:
            connection.close()

        # ------------------------------------------------------------
        # Execute outside the database transaction.
        # ------------------------------------------------------------

        execution = self._execute_action(
            action=action,
        )

        execution_status = (
            execution.get("status")
            or ""
        ).upper()

        # ------------------------------------------------------------
        # Execution failed / executor unavailable
        # ------------------------------------------------------------

        if execution_status not in {
            "SUCCESS",
            "COMPLETED",
        }:

            self._mark_action_failed(
                action_id=action_id,
                incident_id=action["incident_id"],
                result=execution,
            )

            return {
                "actionId": action_id,
                "status": "FAILED",
                "execution": execution,
                "nextStep": "INVESTIGATE_AGAIN",
                "learning": {
                    "retained": False,
                    "reason": (
                        "Recovery was not executed successfully, "
                        "so no recovery outcome was retained as "
                        "confirmed Hindsight learning."
                    ),
                },
            }

        # ------------------------------------------------------------
        # Execution succeeded.
        #
        # Now verify the application.
        # ------------------------------------------------------------

        self._mark_action_verifying(
            action_id=action_id,
            incident_id=action["incident_id"],
            execution_result=execution,
        )

        verification = self._verify_application(
            action=action,
        )

        verification_status = (
            verification.get("status")
            or ""
        ).upper()

        # ------------------------------------------------------------
        # Verification succeeded
        # ------------------------------------------------------------

        if verification_status == "HEALTHY":

            self._mark_action_completed(
                action_id=action_id,
                incident_id=action["incident_id"],
                execution_result=execution,
                verification_result=verification,
            )

            learning = self._retain_recovery_outcome(
                action=action,
                execution=execution,
                verification=verification,
            )

            return {
                "actionId": action_id,
                "status": "COMPLETED",
                "execution": execution,
                "verification": verification,
                "nextStep": "LEARN",
                "learning": learning,
            }

        # ------------------------------------------------------------
        # Verification failed
        # ------------------------------------------------------------

        self._mark_verification_failed(
            action_id=action_id,
            incident_id=action["incident_id"],
            execution_result=execution,
            verification_result=verification,
        )

        return {
            "actionId": action_id,
            "status": "VERIFICATION_FAILED",
            "execution": execution,
            "verification": verification,
            "nextStep": "INVESTIGATE_AGAIN",
            "learning": {
                "retained": False,
                "reason": (
                    "Recovery verification failed, so the "
                    "outcome was not retained as confirmed "
                    "Hindsight learning."
                ),
            },
        }

    # ================================================================
    # INVESTIGATION COMPLETION
    # ================================================================

    def complete_investigation(
        self,
        action_id: int,
        user_id: int,
        investigation_result: Dict[str, Any],
    ) -> Dict[str, Any]:

        action = self.get_action(
            action_id=action_id,
            user_id=user_id,
        )

        action_type = (
            action.get("action_type")
            or ""
        ).strip().lower()

        current_status = (
            action.get("status")
            or ""
        ).strip().upper()

        if action_type != "investigation_required":
            raise HTTPException(
                status_code=400,
                detail=(
                    "The specified action is not an "
                    "investigation action."
                ),
            )

        if current_status != "APPROVED":
            raise HTTPException(
                status_code=400,
                detail=(
                    "Investigation must be approved before "
                    "it can be completed."
                ),
            )

        connection = get_connection()

        try:
            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE recovery_actions
                SET
                    status = 'COMPLETED',
                    completed_at = CURRENT_TIMESTAMP,
                    result = %s,
                    verification_result = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    self._safe_json(investigation_result),
                    "INVESTIGATION_COMPLETED",
                    action_id,
                ),
            )

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = 'INVESTIGATING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    action["incident_id"],
                ),
            )

            connection.commit()
            cursor.close()

        finally:
            connection.close()

        return {
            "actionId": action_id,
            "status": "COMPLETED",
            "nextStep": "PROCESS_NEW_DIAGNOSIS",
            "investigation": investigation_result,
            "message": (
                "Investigation completed. "
                "The new diagnosis should be evaluated separately "
                "before any recovery is proposed."
            ),
        }

    # ================================================================
    # EXECUTION
    # ================================================================

    def _execute_action(
        self,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:

        action_type = (
            action.get("action_type")
            or ""
        ).strip().lower()

        description = (
            action.get("action_description")
            or ""
        ).strip()

        target = (
            action.get("target")
            or ""
        ).strip()

        # ------------------------------------------------------------
        # Code changes
        # ------------------------------------------------------------

        if action_type == "code_change":

            return {
                "status": "MANUAL_EXECUTION_REQUIRED",
                "actionType": action_type,
                "message": (
                    "Code changes are intentionally not executed "
                    "automatically. The proposed source change "
                    "must be reviewed and applied through a "
                    "controlled development/deployment workflow."
                ),
                "target": target,
                "description": description,
            }

        # ------------------------------------------------------------
        # Configuration changes
        # ------------------------------------------------------------

        if action_type == "configuration_change":

            return {
                "status": "MANUAL_EXECUTION_REQUIRED",
                "actionType": action_type,
                "message": (
                    "Configuration changes are intentionally not "
                    "executed automatically. The proposed change "
                    "requires controlled deployment."
                ),
                "target": target,
                "description": description,
            }

        # ------------------------------------------------------------
        # Operational actions
        # ------------------------------------------------------------

        if action_type == "operational_action":

            normalized_description = description.lower()

            requested_operation = None

            for operation in self.SAFE_OPERATIONAL_ACTIONS:

                if operation in normalized_description:
                    requested_operation = operation
                    break

            if not requested_operation:

                return {
                    "status": "EXECUTOR_NOT_CONFIGURED",
                    "actionType": action_type,
                    "message": (
                        "The requested operational action is "
                        "not connected to a production executor."
                    ),
                    "target": target,
                    "description": description,
                }

            # --------------------------------------------------------
            # Retry is currently executable.
            #
            # It does not mutate production state. It performs a
            # fresh runtime availability check.
            # --------------------------------------------------------

            if requested_operation == "retry":

                verification = self._verify_application(
                    action=action,
                )

                if verification.get("status") == "HEALTHY":

                    return {
                        "status": "SUCCESS",
                        "actionType": action_type,
                        "operation": "retry",
                        "message": (
                            "Runtime retry/check completed "
                            "successfully."
                        ),
                        "verification": verification,
                    }

                return {
                    "status": "FAILED",
                    "actionType": action_type,
                    "operation": "retry",
                    "message": (
                        "Runtime retry/check did not produce "
                        "a healthy application response."
                    ),
                    "verification": verification,
                }

            # --------------------------------------------------------
            # Restart / rollback / refresh require real executors.
            # --------------------------------------------------------

            return {
                "status": "EXECUTOR_NOT_CONFIGURED",
                "actionType": action_type,
                "operation": requested_operation,
                "message": (
                    f"The '{requested_operation}' operation is "
                    "recognized but no production executor is "
                    "configured yet."
                ),
                "target": target,
                "description": description,
            }

        return {
            "status": "FAILED",
            "message": (
                f"Unsupported recovery action type: {action_type}"
            ),
        }

    # ================================================================
    # VERIFY APPLICATION
    # ================================================================

    def _verify_application(
        self,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:

        application_id = action.get("application_id")

        if not application_id:
            return {
                "status": "UNKNOWN",
                "message": (
                    "Application ID is missing; runtime "
                    "verification cannot be performed."
                ),
            }

        application = self._get_application(
            application_id=application_id,
        )

        if not application:
            return {
                "status": "UNKNOWN",
                "message": (
                    "Application could not be loaded "
                    "for runtime verification."
                ),
            }

        runtime_url = (
            application.get("runtime_url")
            or ""
        ).strip()

        if not runtime_url:
            return {
                "status": "UNKNOWN",
                "message": (
                    "Application does not have a runtime URL."
                ),
            }

        try:
            response = requests.get(
                runtime_url,
                timeout=15,
                allow_redirects=True,
            )

            status_code = response.status_code

            if 200 <= status_code < 400:

                return {
                    "status": "HEALTHY",
                    "httpStatus": status_code,
                    "runtimeUrl": runtime_url,
                    "message": (
                        "Runtime endpoint returned a successful "
                        "HTTP response."
                    ),
                }

            return {
                "status": "UNHEALTHY",
                "httpStatus": status_code,
                "runtimeUrl": runtime_url,
                "message": (
                    "Runtime endpoint returned an unsuccessful "
                    "HTTP response."
                ),
            }

        except requests.RequestException as exc:

            return {
                "status": "UNHEALTHY",
                "runtimeUrl": runtime_url,
                "message": (
                    "Runtime verification request failed."
                ),
                "error": str(exc),
            }

    # ================================================================
    # HINDSIGHT LEARNING
    # ================================================================

    def _retain_recovery_outcome(
        self,
        action: Dict[str, Any],
        execution: Dict[str, Any],
        verification: Dict[str, Any],
    ) -> Dict[str, Any]:

        incident_id = action.get("incident_id")
        application_id = action.get("application_id")

        incident = self._get_incident_for_learning(
            incident_id=incident_id,
        )

        if not incident:

            return {
                "retained": False,
                "reason": (
                    "Incident could not be loaded for "
                    "recovery learning."
                ),
            }

        # ------------------------------------------------------------
        # Only retain successful AND verified outcomes.
        # ------------------------------------------------------------

        content = (
            "CONFIRMED RECOVERY OUTCOME\n"
            f"Application ID: {application_id}\n"
            f"Incident ID: {incident_id}\n"
            f"Service: {incident.get('service')}\n"
            f"Diagnosis status: "
            f"{incident.get('diagnosis_status')}\n"
            f"Root cause: {incident.get('root_cause')}\n"
            f"Recovery action type: "
            f"{action.get('action_type')}\n"
            f"Recovery action: "
            f"{action.get('action_description')}\n"
            f"Target: {action.get('target')}\n"
            f"Execution result: "
            f"{self._safe_json(execution)}\n"
            f"Verification result: "
            f"{self._safe_json(verification)}\n"
            "Outcome: Recovery executed successfully and "
            "runtime verification confirmed application health."
        )

        try:

            self.hindsight.retain(content)

            return {
                "retained": True,
                "message": (
                    "Successfully verified recovery outcome "
                    "retained in Hindsight."
                ),
            }

        except Exception as exc:

            return {
                "retained": False,
                "reason": (
                    "Recovery succeeded and was verified, "
                    "but Hindsight retention failed."
                ),
                "error": str(exc),
            }

    # ================================================================
    # DATABASE HELPERS
    # ================================================================

    def _get_incident_for_user(
        self,
        incident_id: int,
        user_id: int,
    ) -> Optional[Dict[str, Any]]:

        connection = get_connection()

        try:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM incidents
                WHERE id = %s
                  AND user_id = %s
                LIMIT 1
                """,
                (
                    incident_id,
                    user_id,
                ),
            )

            incident = cursor.fetchone()

            cursor.close()

            return incident

        finally:

            connection.close()

    def _get_incident_for_learning(
        self,
        incident_id: int,
    ) -> Optional[Dict[str, Any]]:

        connection = get_connection()

        try:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM incidents
                WHERE id = %s
                LIMIT 1
                """,
                (
                    incident_id,
                ),
            )

            incident = cursor.fetchone()

            cursor.close()

            return incident

        finally:

            connection.close()

    def _get_application(
        self,
        application_id: int,
    ) -> Optional[Dict[str, Any]]:

        connection = get_connection()

        try:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM applications
                WHERE id = %s
                LIMIT 1
                """,
                (
                    application_id,
                ),
            )

            application = cursor.fetchone()

            cursor.close()

            return application

        finally:

            connection.close()

    def _get_active_action_for_incident(
        self,
        incident_id: int,
    ) -> Optional[Dict[str, Any]]:

        connection = get_connection()

        try:

            cursor = connection.cursor(
                dictionary=True
            )

            cursor.execute(
                """
                SELECT *
                FROM recovery_actions
                WHERE incident_id = %s
                  AND status IN (
                      'PENDING_APPROVAL',
                      'APPROVED',
                      'EXECUTING',
                      'VERIFYING',
                      'INVESTIGATION_PENDING'
                  )
                ORDER BY id DESC
                LIMIT 1
                """,
                (
                    incident_id,
                ),
            )

            action = cursor.fetchone()

            cursor.close()

            return action

        finally:

            connection.close()

    def _insert_action(
        self,
        incident_id: int,
        action_type: str,
        action_description: str,
        target: Optional[str],
        status: str,
        requires_approval: bool,
    ) -> int:

        connection = get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                INSERT INTO recovery_actions (
                    incident_id,
                    action_type,
                    action_description,
                    target,
                    status,
                    requires_approval
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    incident_id,
                    action_type,
                    action_description,
                    target,
                    status,
                    1 if requires_approval else 0,
                ),
            )

            action_id = cursor.lastrowid

            connection.commit()

            cursor.close()

            return action_id

        finally:

            connection.close()

    def _update_incident_status(
        self,
        incident_id: int,
        status: str,
    ):

        connection = get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    status,
                    incident_id,
                ),
            )

            connection.commit()

            cursor.close()

        finally:

            connection.close()

    # ================================================================
    # ACTION STATE HELPERS
    # ================================================================

    def _mark_action_failed(
        self,
        action_id: int,
        incident_id: int,
        result: Dict[str, Any],
    ):

        connection = get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE recovery_actions
                SET
                    status = 'FAILED',
                    result = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    self._safe_json(result),
                    action_id,
                ),
            )

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = 'INVESTIGATION_REQUIRED',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    incident_id,
                ),
            )

            connection.commit()

            cursor.close()

        finally:

            connection.close()

    def _mark_action_verifying(
        self,
        action_id: int,
        incident_id: int,
        execution_result: Dict[str, Any],
    ):

        connection = get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE recovery_actions
                SET
                    status = 'VERIFYING',
                    result = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    self._safe_json(execution_result),
                    action_id,
                ),
            )

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = 'VERIFYING',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    incident_id,
                ),
            )

            connection.commit()

            cursor.close()

        finally:

            connection.close()

    def _mark_action_completed(
        self,
        action_id: int,
        incident_id: int,
        execution_result: Dict[str, Any],
        verification_result: Dict[str, Any],
    ):

        connection = get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE recovery_actions
                SET
                    status = 'COMPLETED',
                    result = %s,
                    verification_result = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    self._safe_json(execution_result),
                    self._safe_json(verification_result),
                    action_id,
                ),
            )

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = 'RESOLVED',
                    resolved_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    incident_id,
                ),
            )

            connection.commit()

            cursor.close()

        finally:

            connection.close()

    def _mark_verification_failed(
        self,
        action_id: int,
        incident_id: int,
        execution_result: Dict[str, Any],
        verification_result: Dict[str, Any],
    ):

        connection = get_connection()

        try:

            cursor = connection.cursor()

            cursor.execute(
                """
                UPDATE recovery_actions
                SET
                    status = 'VERIFICATION_FAILED',
                    result = %s,
                    verification_result = %s,
                    completed_at = CURRENT_TIMESTAMP,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    self._safe_json(execution_result),
                    self._safe_json(verification_result),
                    action_id,
                ),
            )

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = 'INVESTIGATION_REQUIRED',
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """,
                (
                    incident_id,
                ),
            )

            connection.commit()

            cursor.close()

        finally:

            connection.close()

    # ================================================================
    # UTILITY
    # ================================================================

    def _safe_json(
        self,
        value: Any,
    ) -> str:

        import json

        try:

            return json.dumps(
                value,
                default=str,
            )

        except Exception:

            return str(value)