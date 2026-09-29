import json

from app.services.hindsight import HindsightService
from app.services.llm import LLMService
from app.services.applications import get_application
from app.services.repository_context import (
    get_relevant_repository_context,
)
from app.models.incident import IncidentAnalysisRequest


class IncidentAnalysisService:

    def __init__(self):
        self.hindsight = HindsightService()
        self.llm = LLMService()

    def analyze(
        self,
        incident: IncidentAnalysisRequest,
        user_id: int,
        github_token: str,
    ):

        # ---------------------------------------------------------
        # 1. Load application and verify ownership
        # ---------------------------------------------------------

        application = get_application(
            application_id=incident.application_id,
            user_id=user_id,
        )

        if not application:
            raise ValueError(
                "Application not found or does not belong to the current user"
            )

        # ---------------------------------------------------------
        # 2. Calculate current telemetry
        # ---------------------------------------------------------

        if incident.dbConnectionLimit <= 0:
            raise ValueError(
                "Database connection limit must be greater than zero"
            )

        connection_utilization = (
            incident.dbConnections /
            incident.dbConnectionLimit
        ) * 100

        current_incident = {
            "applicationId": incident.application_id,
            "service": incident.service,
            "latencyMs": incident.latencyMs,
            "errorRate": incident.errorRate,
            "dbConnections": incident.dbConnections,
            "dbConnectionLimit": incident.dbConnectionLimit,
            "dbConnectionUtilization": round(
                connection_utilization,
                2,
            ),
            "cpu": incident.cpu,
            "memory": incident.memory,
        }

        # ---------------------------------------------------------
        # 3. Build application context
        # ---------------------------------------------------------

        application_context = {
            "id": application.get("id"),
            "name": application.get("name"),
            "description": application.get("description"),
            "runtimeType": application.get("runtime_type"),
            "runtimeUrl": application.get("runtime_url"),
            "sourceType": application.get("source_type"),
            "sourceUrl": application.get("source_url"),
            "deploymentType": application.get("deployment_type"),
            "status": application.get("status"),
        }

        # ---------------------------------------------------------
        # 4. Read relevant repository files
        # ---------------------------------------------------------

        repository_context = None

        if (
            application.get("source_type") == "GitHub"
            and application.get("source_url")
        ):

            repository_context = (
                get_relevant_repository_context(
                    repository_url=application.get(
                        "source_url"
                    ),
                    github_token=github_token,
                    service=incident.service,
                    latency=incident.latencyMs,
                    error_rate=incident.errorRate,
                    db_connections=incident.dbConnections,
                    db_connection_limit=incident.dbConnectionLimit,
                    cpu=incident.cpu,
                    memory=incident.memory,
                )
            )

        # ---------------------------------------------------------
        # 5. Ask Hindsight for relevant historical experience
        # ---------------------------------------------------------

        query = (
            f"application {application.get('name')} "
            f"service {incident.service} "
            f"high latency {incident.latencyMs} ms "
            f"high error rate {incident.errorRate}% "
            f"database connections {incident.dbConnections} "
            f"connection utilization "
            f"{connection_utilization:.1f}%"
        )

        historical_memory = self.hindsight.recall(query)

        # ---------------------------------------------------------
        # 6. Prepare LLM instructions
        # ---------------------------------------------------------

        system_prompt = """
You are an AI Site Reliability Engineering incident-response agent.

Your job is to investigate a CURRENT production incident using:

1. Current runtime telemetry
2. Application metadata
3. Relevant source code and configuration files
4. Historical operational experience retrieved from Hindsight

IMPORTANT INVESTIGATION RULES:

- Current telemetry tells you what is happening.
- Repository files help determine how the application works
  and what may be causing the incident.
- Use the actual repository file contents as evidence.
- Do not invent code, configuration, files, or application behavior.
- Identify specific repository files when they provide evidence
  for the diagnosis.
- Do not assume that a file is responsible merely because its
  filename contains a relevant keyword.
- Inspect the actual file content before using it as evidence.
- Distinguish confirmed evidence from hypotheses.
- Treat Hindsight memories as organizational experience and
  supporting evidence, not guaranteed truth.
- If historical experience conflicts with current evidence,
  prioritize the current evidence.
- If repository evidence conflicts with assumptions,
  prioritize the actual repository evidence.
- If there is insufficient evidence to determine a root cause,
  explicitly say so.
- Do not invent historical incidents.
- Do not invent remediation commands.
- Potential remediation actions require human approval.

IMPORTANT CODE-CHANGE RULE:

If the evidence suggests that source code or configuration
must be changed, identify the specific file and explain what
should be changed.

Do NOT pretend that a code change has already been applied.

Return ONLY valid JSON.

Use exactly this structure:

{
  "diagnosis": {
    "rootCause": "string",
    "confidence": 0.0
  },
  "reasoning": "string",
  "evidence": [
    "string"
  ],
  "affectedFiles": [
    {
      "path": "string",
      "reason": "string"
    }
  ],
  "historicalContext": {
    "relevant": true,
    "reason": "string",
    "incidents": [
      "string"
    ]
  },
  "recommendation": {
    "type": "code_change | configuration_change | operational_action | investigation_required",
    "action": "string",
    "targetFiles": [
      "string"
    ],
    "reason": "string",
    "requiresApproval": true
  }
}

The confidence value must be between 0 and 1.
"""

        user_prompt = f"""
APPLICATION CONTEXT:

{json.dumps(
    application_context,
    indent=2,
)}

CURRENT INCIDENT TELEMETRY:

{json.dumps(
    current_incident,
    indent=2,
)}

RELEVANT REPOSITORY CONTEXT:

{json.dumps(
    repository_context,
    indent=2,
)}

HISTORICAL EXPERIENCE FROM HINDSIGHT:

{json.dumps(
    historical_memory,
    indent=2,
)}

INVESTIGATION TASK:

Investigate the current incident.

Use the telemetry to identify what is currently failing.

Then inspect the actual repository files provided in the
RELEVANT REPOSITORY CONTEXT.

Determine whether the source code or configuration provides
evidence for the observed failure.

When repository evidence supports a diagnosis, identify the
specific file path and explain the relevant behavior.

Then compare the findings with relevant Hindsight experience.

Finally provide:

1. The most evidence-supported root cause.
2. Your confidence.
3. Evidence from telemetry and repository files.
4. The specific affected files, if any.
5. A proposed remediation.
6. Whether the remediation is a code change, configuration
   change, operational action, or requires further investigation.

Do not claim that any change has already been made.
"""

        # ---------------------------------------------------------
        # 7. Ask the LLM to investigate
        # ---------------------------------------------------------

        llm_response = self.llm.analyze(
            system_prompt,
            user_prompt,
        )

        # ---------------------------------------------------------
        # 8. Convert LLM JSON text into actual JSON
        # ---------------------------------------------------------

        try:

            ai_analysis = json.loads(
                llm_response
            )

        except json.JSONDecodeError:

            ai_analysis = {
                "rawAnalysis": llm_response
            }

        # ---------------------------------------------------------
        # 9. Return complete investigation result
        # ---------------------------------------------------------

        return {
            "application": application_context,
            "incident": current_incident,
            "repositoryContext": repository_context,
            "hindsightQuery": query,
            "historicalExperience": historical_memory,
            "aiAnalysis": ai_analysis,
        }