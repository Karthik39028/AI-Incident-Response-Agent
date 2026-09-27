import json

from app.services.hindsight import HindsightService
from app.services.llm import LLMService
from app.models.incident import IncidentAnalysisRequest


class IncidentAnalysisService:

    def __init__(self):
        self.hindsight = HindsightService()
        self.llm = LLMService()

    def analyze(self, incident: IncidentAnalysisRequest):

        # ---------------------------------------------------------
        # 1. Calculate current telemetry
        # ---------------------------------------------------------

        connection_utilization = (
            incident.dbConnections /
            incident.dbConnectionLimit
        ) * 100

        current_incident = {
            "service": incident.service,
            "latencyMs": incident.latencyMs,
            "errorRate": incident.errorRate,
            "dbConnections": incident.dbConnections,
            "dbConnectionLimit": incident.dbConnectionLimit,
            "dbConnectionUtilization": round(
                connection_utilization,
                2
            ),
            "cpu": incident.cpu,
            "memory": incident.memory
        }

        # ---------------------------------------------------------
        # 2. Ask Hindsight for relevant historical experience
        # ---------------------------------------------------------

        query = (
            f"{incident.service} "
            f"high latency {incident.latencyMs} ms "
            f"high error rate {incident.errorRate}% "
            f"database connections {incident.dbConnections} "
            f"connection utilization "
            f"{connection_utilization:.1f}%"
        )

        historical_memory = self.hindsight.recall(query)

        # ---------------------------------------------------------
        # 3. Prepare LLM instructions
        # ---------------------------------------------------------

        system_prompt = """
You are an AI Site Reliability Engineering incident-response agent.

Your job is to analyze a CURRENT production incident using:

1. Current telemetry
2. Historical experiences retrieved from Hindsight

IMPORTANT RULES:

- Analyze the current telemetry independently first.
- Do not blindly copy historical conclusions.
- Treat Hindsight memories as organizational experience and
  supporting evidence, not as guaranteed truth.
- Determine whether each historical experience is actually
  relevant to the current incident.
- If historical experience conflicts with current telemetry,
  prioritize the current telemetry.
- If there is no useful historical experience, reason from
  the current evidence.
- Do not invent historical incidents or facts.
- Recommend an action only when there is reasonable evidence.
- Potential remediation actions should require human approval.

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
  "historicalContext": {
    "relevant": true,
    "reason": "string",
    "incidents": [
      "string"
    ]
  },
  "recommendation": {
    "action": "string",
    "reason": "string",
    "requiresApproval": true
  }
}

The confidence value must be between 0 and 1.
"""

        user_prompt = f"""
CURRENT INCIDENT:

{json.dumps(current_incident, indent=2)}

HISTORICAL EXPERIENCE FROM HINDSIGHT:

{json.dumps(historical_memory, indent=2)}

Analyze the incident.

First reason from the current telemetry.

Then determine whether the historical experience is
relevant to the current conditions.

Finally provide the diagnosis and recommended next action.
"""

        # ---------------------------------------------------------
        # 4. Ask the LLM to reason
        # ---------------------------------------------------------

        llm_response = self.llm.analyze(
            system_prompt,
            user_prompt
        )

        # ---------------------------------------------------------
        # 5. Convert LLM JSON text into actual JSON
        # ---------------------------------------------------------

        try:
            ai_analysis = json.loads(llm_response)

        except json.JSONDecodeError:

            ai_analysis = {
                "rawAnalysis": llm_response
            }

        # ---------------------------------------------------------
        # 6. Return complete agent response
        # ---------------------------------------------------------

        return {
            "incident": current_incident,
            "hindsightQuery": query,
            "historicalExperience": historical_memory,
            "aiAnalysis": ai_analysis
        }