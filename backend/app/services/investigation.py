import json
import re

from app.services.database import get_connection
from app.services.llm import LLMService
from app.services.repository_context import get_relevant_repository_context


class InvestigationService:

    def __init__(self):
        self.llm = LLMService()

    # ============================================================
    # JSON PARSER
    # ============================================================

    def _parse_llm_json(self, content: str):

        if not content:
            raise ValueError("LLM returned an empty investigation response")

        text = content.strip()

        # Remove markdown code fences
        text = re.sub(
            r"^```(?:json)?\s*",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = re.sub(
            r"\s*```$",
            "",
            text,
            flags=re.IGNORECASE,
        )

        text = text.strip()

        # Direct JSON
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try extracting the first JSON object
        decoder = json.JSONDecoder()

        start = text.find("{")

        if start >= 0:
            try:
                parsed, _ = decoder.raw_decode(text[start:])
                return parsed
            except json.JSONDecodeError:
                pass

        raise ValueError(
            "LLM investigation response did not contain valid JSON"
        )

    # ============================================================
    # NORMALIZE RESULT
    # ============================================================

    def _normalize_result(self, result):

        if not isinstance(result, dict):
            result = {}

        diagnosis = result.get("diagnosis")

        if not isinstance(diagnosis, dict):
            diagnosis = {}

        recommendation = result.get("recommendation")

        if not isinstance(recommendation, dict):
            recommendation = {}

        normalized = {
            "status": result.get(
                "status",
                "insufficient_evidence",
            ),

            "diagnosis": {
                "rootCause": diagnosis.get(
                    "rootCause"
                ),
                "confidence": diagnosis.get(
                    "confidence",
                    0.0,
                ),
                "summary": diagnosis.get(
                    "summary"
                ),
            },

            "evidence": result.get(
                "evidence",
                [],
            ),

            "contradictions": result.get(
                "contradictions",
                [],
            ),

            "investigatedFiles": result.get(
                "investigatedFiles",
                [],
            ),

            "affectedFiles": result.get(
                "affectedFiles",
                [],
            ),

            "externalEvidenceRequired": result.get(
                "externalEvidenceRequired",
                [],
            ),

            "recommendation": {
                "type": recommendation.get(
                    "type",
                    "investigation_required",
                ),
                "action": recommendation.get(
                    "action"
                ),
                "reason": recommendation.get(
                    "reason"
                ),
                "targetFiles": recommendation.get(
                    "targetFiles",
                    [],
                ),
                "requiresApproval": recommendation.get(
                    "requiresApproval",
                    True,
                ),
            },

            "nextInvestigation": result.get(
                "nextInvestigation"
            ),
        }

        return normalized

    # ============================================================
    # BUILD SYSTEM PROMPT
    # ============================================================

    def _build_system_prompt(self):

        return """
You are the second-stage investigation agent in an AI
incident-response system.

Your job is NOT to guess a root cause.

You must investigate the actual application repository and
determine whether the available evidence supports a diagnosis.

IMPORTANT EVIDENCE RULES:

1. The GitHub repository is the source of truth for the
   application's implemented architecture.

2. Telemetry describes symptoms. It does NOT prove that a
   component exists.

3. Hindsight/history is supporting evidence only.

4. Do not diagnose a database problem merely because database
   telemetry is present.

5. Do not claim a file is responsible merely because its
   filename looks relevant.

6. A file can only be considered affected when its actual
   source/configuration content supports the diagnosis.

7. If the repository cannot explain the incident, explicitly
   state that additional runtime or external-system evidence
   is required.

8. Contradictory evidence must be reported.

9. Never invent source files, APIs, databases, backend
   services, deployment infrastructure, or runtime behavior.

10. If root cause cannot be established, use:
    status = "insufficient_evidence"

11. Only use:
    status = "diagnosed"
    when the evidence provides a defensible root cause.

12. Recovery recommendations that change application state
    must require human approval.

13. Investigation actions are not recovery actions.

Return ONLY valid JSON.

Required JSON structure:

{
  "status": "diagnosed | insufficient_evidence",

  "diagnosis": {
    "rootCause": "string or null",
    "confidence": 0.0,
    "summary": "string"
  },

  "evidence": [
    "specific evidence"
  ],

  "contradictions": [
    "specific contradiction"
  ],

  "investigatedFiles": [
    "path/to/file"
  ],

  "affectedFiles": [
    {
      "path": "path/to/file",
      "evidence": "specific code/config evidence"
    }
  ],

  "externalEvidenceRequired": [
    "specific runtime evidence needed"
  ],

  "recommendation": {
    "type": "code_change | configuration_change | operational_action | investigation_required",
    "action": "specific action",
    "reason": "why this action is appropriate",
    "targetFiles": [
      "path/to/file"
    ],
    "requiresApproval": true
  },

  "nextInvestigation": {
    "required": true,
    "reason": "specific reason"
  }
}

Do not provide a recovery action when the root cause is
unsupported.
"""

    # ============================================================
    # BUILD USER PROMPT
    # ============================================================

    def _build_user_prompt(
        self,
        incident,
        repository_context,
        previous_analysis,
    ):

        return f"""
Perform a second-stage investigation of the following incident.

CURRENT INCIDENT:

Service:
{incident["service"]}

Latency:
{incident["latencyMs"]} ms

Error rate:
{incident["errorRate"]} %

Database connections:
{incident["dbConnections"]}

Database connection limit:
{incident["dbConnectionLimit"]}

CPU:
{incident["cpu"]} %

Memory:
{incident["memory"]} %

PREVIOUS ANALYSIS:

{json.dumps(previous_analysis, indent=2)}

REPOSITORY INTELLIGENCE:

{json.dumps(repository_context, indent=2)}

INVESTIGATION OBJECTIVE:

The previous investigation could not establish the root cause.

Now inspect the actual repository evidence supplied above.

Pay particular attention to:

- frontend request paths
- fetch()
- axios
- API clients
- external URLs
- Netlify configuration
- Netlify Functions
- serverless functions
- backend/API code
- authentication
- timeout handling
- error handling
- asynchronous requests
- deployment configuration
- environment references
- proxy configuration
- runtime dependencies

Do not assume any of these exist.

Only report them if actual repository evidence shows them.

Determine whether the repository provides enough evidence to
explain the 9400 ms latency and 18.2% error rate.

The database telemetry is especially important because the
previous analysis found no confirmed database implementation.

Therefore explicitly determine whether:

1. the repository actually contains database functionality,
2. the repository contains a backend or serverless backend,
3. frontend code calls external APIs,
4. deployment configuration routes requests somewhere else,
5. the telemetry could belong to an external dependency,
6. the available evidence is still insufficient.

If the repository does not explain the database telemetry,
DO NOT invent a database diagnosis.

Return only the required JSON.
"""

    # ============================================================
    # LOAD INCIDENT
    # ============================================================

    def _get_incident(
        self,
        incident_id: int,
        user_id: int,
    ):

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    id,
                    application_id,
                    user_id,
                    service,
                    latency_ms,
                    error_rate,
                    db_connections,
                    db_connection_limit,
                    cpu,
                    memory,
                    status,
                    root_cause,
                    confidence,
                    diagnosis_status,
                    reasoning,
                    recommendation_type,
                    recommendation_action,
                    recommendation_reason,
                    requires_approval
                FROM incidents
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    incident_id,
                    user_id,
                ),
            )

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # GET APPLICATION
    # ============================================================

    def _get_application(
        self,
        application_id: int,
        user_id: int,
    ):

        connection = get_connection()
        cursor = connection.cursor(dictionary=True)

        try:
            cursor.execute(
                """
                SELECT
                    id,
                    name,
                    description,
                    runtime_type,
                    runtime_url,
                    source_type,
                    source_url,
                    deployment_type,
                    status
                FROM applications
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    application_id,
                    user_id,
                ),
            )

            return cursor.fetchone()

        finally:
            cursor.close()
            connection.close()

    # ============================================================
    # RUN INVESTIGATION
    # ============================================================

    def investigate(
        self,
        incident_id: int,
        user_id: int,
        github_token: str,
    ):

        incident = self._get_incident(
            incident_id=incident_id,
            user_id=user_id,
        )

        if not incident:
            raise ValueError(
                "Incident not found or does not belong to the current user"
            )

        application = self._get_application(
            application_id=incident["application_id"],
            user_id=user_id,
        )

        if not application:
            raise ValueError(
                "Application not found"
            )

        if application.get("source_type") != "GitHub":
            raise ValueError(
                "Second-stage repository investigation currently "
                "supports GitHub applications only"
            )

        repository_url = application.get(
            "source_url"
        )

        if not repository_url:
            raise ValueError(
                "Application does not have a GitHub repository URL"
            )

        # --------------------------------------------------------
        # Build repository intelligence
        # --------------------------------------------------------

        repository_context = get_relevant_repository_context(
            repository_url=repository_url,
            github_token=github_token,
            service=incident["service"],
            latency=incident["latency_ms"],
            error_rate=incident["error_rate"],
            db_connections=incident["db_connections"],
            db_connection_limit=incident["db_connection_limit"],
            cpu=incident["cpu"],
            memory=incident["memory"],
        )

        # --------------------------------------------------------
        # Previous analysis
        # --------------------------------------------------------

        previous_analysis = {
            "status": incident.get(
                "diagnosis_status"
            ),
            "rootCause": incident.get(
                "root_cause"
            ),
            "confidence": incident.get(
                "confidence"
            ),
            "reasoning": incident.get(
                "reasoning"
            ),
            "recommendation": {
                "type": incident.get(
                    "recommendation_type"
                ),
                "action": incident.get(
                    "recommendation_action"
                ),
                "reason": incident.get(
                    "recommendation_reason"
                ),
            },
        }

        # --------------------------------------------------------
        # LLM investigation
        # --------------------------------------------------------

        system_prompt = self._build_system_prompt()

        user_prompt = self._build_user_prompt(
            incident=incident,
            repository_context=repository_context,
            previous_analysis=previous_analysis,
        )

        raw_response = self.llm.analyze(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
        )

        parsed = self._parse_llm_json(
            raw_response
        )

        analysis = self._normalize_result(
            parsed
        )

        # --------------------------------------------------------
        # Persist investigation result
        # --------------------------------------------------------

        self._save_result(
            incident_id=incident_id,
            user_id=user_id,
            analysis=analysis,
        )

        return {
            "success": True,
            "incidentId": incident_id,
            "analysis": analysis,
            "repositoryContext": repository_context,
        }

    # ============================================================
    # SAVE RESULT
    # ============================================================

    def _save_result(
        self,
        incident_id: int,
        user_id: int,
        analysis: dict,
    ):

        diagnosis = analysis.get(
            "diagnosis",
            {},
        )

        recommendation = analysis.get(
            "recommendation",
            {},
        )

        status = analysis.get(
            "status",
            "insufficient_evidence",
        )

        if status == "diagnosed":
            incident_status = "DIAGNOSED"
        else:
            incident_status = "INVESTIGATION_REQUIRED"

        connection = get_connection()
        cursor = connection.cursor()

        try:

            cursor.execute(
                """
                UPDATE incidents
                SET
                    status = %s,
                    root_cause = %s,
                    confidence = %s,
                    diagnosis_status = %s,
                    reasoning = %s,
                    recommendation_type = %s,
                    recommendation_action = %s,
                    recommendation_reason = %s,
                    requires_approval = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                  AND user_id = %s
                """,
                (
                    incident_status,

                    diagnosis.get(
                        "rootCause"
                    ),

                    diagnosis.get(
                        "confidence",
                        0.0,
                    ),

                    status,

                    diagnosis.get(
                        "summary"
                    ),

                    recommendation.get(
                        "type",
                        "investigation_required",
                    ),

                    recommendation.get(
                        "action"
                    ),

                    recommendation.get(
                        "reason"
                    ),

                    bool(
                        recommendation.get(
                            "requiresApproval",
                            True,
                        )
                    ),

                    incident_id,
                    user_id,
                ),
            )

            connection.commit()

        except Exception:
            connection.rollback()
            raise

        finally:
            cursor.close()
            connection.close()