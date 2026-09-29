import json

from app.services.hindsight import HindsightService
from app.services.llm import LLMService
from app.services.applications import get_application
from app.services.repository_context import (
    get_relevant_repository_context,
)
from app.services.database import get_connection
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
            incident.dbConnections
            / incident.dbConnectionLimit
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
        # 4. Understand the actual repository
        # ---------------------------------------------------------

        repository_context = None

        if (
            application.get("source_type") == "GitHub"
            and application.get("source_url")
        ):
            repository_context = (
                get_relevant_repository_context(
                    repository_url=application.get("source_url"),
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
        # 5. Ask Hindsight for historical experience
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
        # 6. Prepare evidence-driven investigation instructions
        # ---------------------------------------------------------

        system_prompt = """
You are an AI Site Reliability Engineering incident-response agent.

Your job is to investigate a CURRENT production incident using:

1. Current runtime telemetry
2. Application metadata
3. Repository architecture
4. Actual source code and configuration
5. Historical operational experience from Hindsight

============================================================
CORE INVESTIGATION PRINCIPLE
============================================================

The repository is the primary source of truth for determining
what components, technologies, dependencies, and failure
mechanisms actually exist inside the application.

Telemetry tells you WHAT is happening.

The repository tells you WHAT THE APPLICATION CAN ACTUALLY DO.

Hindsight tells you WHAT HAS HAPPENED BEFORE.

You must combine these sources instead of allowing one source
to automatically determine the diagnosis.

============================================================
REPOSITORY-FIRST REASONING
============================================================

Before accepting a root-cause hypothesis, inspect the
repository architecture.

Ask:

- What type of application is this?
- Is it frontend, backend, or full-stack?
- What frameworks are actually present?
- What deployment platform is actually present?
- Does the repository contain database code?
- Does the repository contain backend/API code?
- Does the repository contain external-service/API calls?
- What source/configuration files are relevant to the incident?

A telemetry field does NOT prove that the corresponding
component exists.

For example:

If telemetry reports:

    dbConnections = 97
    dbConnectionLimit = 100

but repository evidence shows:

    databaseDetected = false

then you MUST NOT automatically diagnose database connection
pool exhaustion.

Instead, explain the contradiction and investigate whether:

- the telemetry is incorrectly attributed,
- the application depends on an external backend,
- another service owns the database,
- monitoring configuration is incorrect,
- or additional external evidence is required.

============================================================
EVIDENCE HIERARCHY
============================================================

Use evidence in this order:

1. Actual repository code/configuration
2. Current runtime telemetry
3. Application metadata
4. Hindsight historical experience

This does NOT mean telemetry is unimportant.

Telemetry is essential for identifying symptoms.

However, telemetry must not be used to invent components
that the repository does not contain.

Hindsight must never override current repository evidence.

============================================================
HYPOTHESIS DISCIPLINE
============================================================

For every potential root cause:

1. Identify the hypothesis.
2. Check whether the repository supports the required
   component or mechanism.
3. Inspect the actual relevant files.
4. Compare the repository evidence with telemetry.
5. Compare with Hindsight.
6. Decide whether the hypothesis is:
   - supported,
   - contradicted,
   - or unconfirmed.

Never treat a filename alone as proof.

Never treat a telemetry field alone as proof.

Never treat a historical incident alone as proof.

============================================================
WHEN EVIDENCE CONFLICTS
============================================================

If telemetry suggests one thing but the repository contradicts
it, explicitly report the contradiction.

============================================================
WHEN ROOT CAUSE IS UNKNOWN
============================================================

You are allowed and encouraged to say:

"Root cause cannot be determined from the currently available
evidence."

This is preferable to inventing a diagnosis.

When evidence is insufficient, recommend the NEXT
INVESTIGATION that would reduce uncertainty.

Examples:

- verify monitoring attribution
- inspect external API dependency
- inspect backend service
- inspect deployment logs
- inspect runtime logs
- inspect network requests
- inspect actual database service

Do not invent results from investigations that were not performed.

============================================================
AFFECTED FILES
============================================================

Only identify a repository file as an affected file if its
ACTUAL CONTENT provides evidence related to the suspected
failure.

Do NOT mark a file as affected because:

- its filename sounds relevant,
- it is a commonly problematic file,
- it contains generic application code,
- or it was merely selected for investigation.

Distinguish:

"investigated file"

from:

"affected file."

============================================================
HINDSIGHT RULES
============================================================

Hindsight contains historical operational experience.

Use it as supporting evidence.

Do not treat it as ground truth.

A historical incident may look similar while involving a
completely different application architecture.

If the historical incident conflicts with the current
repository evidence, explain why it does not directly apply.

Do not invent historical incidents.

Do not invent historical resolutions.

============================================================
REMEDIATION RULES
============================================================

A recommendation must be supported by the investigation.

Possible recommendation types:

- code_change
- configuration_change
- operational_action
- investigation_required

If a code or configuration change is recommended:

- identify the actual file,
- explain what should change,
- explain why,
- do not claim the change has already happened.

If an operational action is recommended:

- explain what should be done,
- explain what evidence supports it,
- require human approval.

Do not invent shell commands or infrastructure actions.

============================================================
HUMAN APPROVAL
============================================================

Any state-changing remediation requires human approval.

Never claim that recovery has already been executed.

============================================================
OUTPUT
============================================================

Return ONLY valid JSON.

DO NOT use Markdown.

DO NOT wrap the JSON in ```json fences.

DO NOT add explanations before or after the JSON.

Use exactly this structure:

{
  "diagnosis": {
    "rootCause": "string",
    "confidence": 0.0,
    "status": "confirmed | supported | unconfirmed | insufficient_evidence | contradicted"
  },

  "reasoning": "string",

  "evidence": [
    "string"
  ],

  "contradictions": [
    "string"
  ],

  "affectedFiles": [
    {
      "path": "string",
      "reason": "string"
    }
  ],

  "investigatedFiles": [
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
  },

  "nextInvestigation": {
    "required": true,
    "action": "string",
    "reason": "string"
  }
}

The confidence value must be between 0 and 1.

Use low confidence when evidence is contradictory or
incomplete.

Use high confidence only when telemetry and repository
evidence support the same explanation.

IMPORTANT:
Every field must be present.
Use empty arrays [] when there is no evidence.
Never omit diagnosis, reasoning, evidence, historicalContext,
recommendation, or nextInvestigation.
"""

        # ---------------------------------------------------------
        # 7. Build investigation prompt
        # ---------------------------------------------------------

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

REPOSITORY INTELLIGENCE:

{json.dumps(
    repository_context,
    indent=2,
)}

HISTORICAL EXPERIENCE FROM HINDSIGHT:

{json.dumps(
    historical_memory,
    indent=2,
)}

============================================================
INVESTIGATION TASK
============================================================

Investigate this incident systematically.

STEP 1 — UNDERSTAND THE APPLICATION

Use the repository architecture to determine what this
application actually contains.

STEP 2 — IDENTIFY POSSIBLE FAILURE MECHANISMS

Determine which failure mechanisms are actually possible
given the repository architecture.

Do not create hypotheses for components that do not exist
unless the repository explicitly indicates an external
dependency.

STEP 3 — INSPECT ACTUAL FILES

Use the selected repository files as evidence.

Identify the specific files that genuinely contribute to the
investigation.

STEP 4 — CORRELATE TELEMETRY

Use the telemetry to determine which symptoms are occurring.

Do not use telemetry alone to prove the existence of a
component.

STEP 5 — COMPARE HINDSIGHT

Determine whether historical incidents genuinely match the
current application's architecture and evidence.

STEP 6 — DIAGNOSE

Determine the most evidence-supported explanation.

If evidence is insufficient or contradictory, say so.

STEP 7 — RECOMMEND

Recommend either:

- a supported remediation, or
- the next investigation required to obtain missing evidence.

Do not claim that any remediation has already been executed.

============================================================
IMPORTANT
============================================================

The goal is not to always produce a root cause.

The goal is to produce the most defensible conclusion from
the available evidence.

A correct answer may be:

"Root cause cannot currently be determined."

That is preferable to an unsupported diagnosis.

REMEMBER:
Return ONLY valid JSON.
Do not use Markdown fences.
Do not omit any required top-level field.
"""

        # ---------------------------------------------------------
        # 8. Ask the LLM to investigate
        # ---------------------------------------------------------

        llm_response = self.llm.analyze(
            system_prompt,
            user_prompt,
        )

        print("====================================")
        print("LLM RAW RESPONSE")
        print("====================================")
        print(llm_response)
        print("====================================")
        

        ai_analysis = self._parse_llm_json(llm_response)

        # ---------------------------------------------------------
        # 10. Persist incident + analysis
        # ---------------------------------------------------------

        incident_id = self._save_incident(
            incident=incident,
            user_id=user_id,
            ai_analysis=ai_analysis,
        )

        # ---------------------------------------------------------
        # 11. Learn from this investigation
        # ---------------------------------------------------------
        # The diagnosis is retained only when a sufficiently similar
        # diagnosis is not already present in Hindsight. Hindsight
        # failures must never break the incident-analysis workflow.
        hindsight_learning = self._retain_diagnosis_if_new(
            incident=incident,
            application=application_context,
            repository_context=repository_context,
            ai_analysis=ai_analysis,
            incident_id=incident_id,
        )

        # ---------------------------------------------------------
        # 12. Return complete investigation result
        # ---------------------------------------------------------

        return {
            "incidentId": incident_id,
            "application": application_context,
            "incident": current_incident,
            "repositoryContext": repository_context,
            "hindsightQuery": query,
            "historicalExperience": historical_memory,
            "aiAnalysis": ai_analysis,
            "hindsightLearning": hindsight_learning,
        }

    # =============================================================
    # HINDSIGHT DIAGNOSIS LEARNING
    # =============================================================

    def _retain_diagnosis_if_new(
        self,
        incident,
        application,
        repository_context,
        ai_analysis,
        incident_id,
    ):
        """
        Retain the current investigation result in Hindsight when
        a sufficiently similar diagnosis is not already available.

        This is intentionally best-effort: Hindsight is a learning
        layer and must never cause the incident analysis itself to fail.
        """

        diagnosis = ai_analysis.get("diagnosis", {})
        root_cause = str(
            diagnosis.get(
                "rootCause",
                "",
            )
        ).strip()

        diagnosis_status = str(
            diagnosis.get(
                "status",
                "insufficient_evidence",
            )
        ).strip().lower()

        # Do not store uncertain or contradictory diagnoses as reusable
        # organizational knowledge. Hindsight should learn only from a
        # confirmed diagnosis.
        if diagnosis_status != "confirmed":
            return {
                "retained": False,
                "reason": (
                    "Diagnosis is not confirmed; uncertain investigation "
                    "results are not retained as reusable Hindsight learning."
                ),
            }

        if not root_cause:
            return {
                "retained": False,
                "reason": "No diagnosis was available to retain.",
            }

        try:
            duplicate_query = (
                f"incident diagnosis for application {application.get('name')} "
                f"service {incident.service}: {root_cause}"
            )

            existing_memory = self.hindsight.recall(duplicate_query)

            if self._has_matching_historical_diagnosis(
                existing_memory=existing_memory,
                root_cause=root_cause,
                application_name=str(application.get("name") or ""),
                service=str(incident.service or ""),
            ):
                return {
                    "retained": False,
                    "reason": "A sufficiently similar diagnosis already exists in Hindsight.",
                }

            repository_summary = self._build_learning_repository_summary(
                repository_context
            )

            learning_content = {
                "type": "incident_diagnosis",
                "incidentId": incident_id,
                "application": {
                    "id": application.get("id"),
                    "name": application.get("name"),
                    "runtimeType": application.get("runtimeType"),
                    "deploymentType": application.get("deploymentType"),
                },
                "service": incident.service,
                "telemetry": {
                    "latencyMs": incident.latencyMs,
                    "errorRate": incident.errorRate,
                    "dbConnections": incident.dbConnections,
                    "dbConnectionLimit": incident.dbConnectionLimit,
                    "cpu": incident.cpu,
                    "memory": incident.memory,
                },
                "repositoryEvidence": repository_summary,
                "diagnosis": {
                    "rootCause": root_cause,
                    "confidence": diagnosis.get("confidence", 0.0),
                    "status": diagnosis_status,
                },
                "reasoning": ai_analysis.get("reasoning", ""),
                "evidence": ai_analysis.get("evidence", []),
                "contradictions": ai_analysis.get("contradictions", []),
                "affectedFiles": ai_analysis.get("affectedFiles", []),
                "investigatedFiles": ai_analysis.get("investigatedFiles", []),
                "recommendation": ai_analysis.get("recommendation", {}),
                "nextInvestigation": ai_analysis.get("nextInvestigation", {}),
            }

            self.hindsight.retain(
                content=json.dumps(
                    learning_content,
                    ensure_ascii=False,
                )
            )

            return {
                "retained": True,
                "reason": "New incident diagnosis retained in Hindsight.",
            }

        except Exception as exc:
            print(
                "HINDSIGHT DIAGNOSIS RETENTION ERROR",
                type(exc).__name__,
                str(exc),
            )

            return {
                "retained": False,
                "reason": "Hindsight retention failed, but incident analysis was preserved.",
            }

    def _has_matching_historical_diagnosis(
        self,
        historical_memory,
        root_cause,
        application_name="",
        service="",
    ):
        """
        Check whether Hindsight appears to contain the same diagnosis.

        Hindsight response shapes can vary, so this uses a conservative
        text-overlap check instead of assuming a particular response schema.
        A weak or unrelated historical result is not treated as a duplicate.
        """

        if not historical_memory:
            return False

        try:
            memory_text = json.dumps(
                historical_memory,
                ensure_ascii=False,
            ).lower()
        except Exception:
            memory_text = str(historical_memory).lower()

        diagnosis_text = root_cause.lower().strip()

        if not diagnosis_text:
            return False

        # A diagnosis should only be considered a duplicate when the
        # historical memory also belongs to the same application/service.
        # This prevents a similar diagnosis from another application from
        # suppressing useful learning for the current application.
        # Require the same application context before treating a memory
        # as a duplicate. If a service is available, it must also match.
        if application_name:
            normalized_application = application_name.lower().strip()
            if (
                not normalized_application
                or normalized_application not in memory_text
            ):
                return False

        if service:
            normalized_service = service.lower().strip()
            if (
                not normalized_service
                or normalized_service not in memory_text
            ):
                return False

        # Exact phrase match is the strongest duplicate signal.
        if diagnosis_text in memory_text:
            return True

        # Compare meaningful words while ignoring common language.
        stop_words = {
            "this", "that", "with", "from", "into",
            "cannot", "currently", "determined", "available",
            "evidence", "application", "incident", "root",
            "cause", "the", "and", "for", "are", "is",
            "not", "does", "have", "has", "could",
            "would", "should", "possible",
        }

        words = {
            word
            for word in diagnosis_text.replace("/", " ").replace("-", " ").split()
            if len(word) >= 5 and word not in stop_words
        }

        if len(words) < 3:
            return False

        matched = sum(1 for word in words if word in memory_text)

        return (matched / len(words)) >= 0.70

    def _build_learning_repository_summary(
        self,
        repository_context,
    ):
        if not isinstance(repository_context, dict):
            return {}

        architecture = repository_context.get("architecture")

        if not isinstance(architecture, dict):
            architecture = {}

        return {
            "architecture": architecture,
            "relevantFiles": repository_context.get("relevantFiles", []),
            "constraints": repository_context.get("constraints", []),
        }

    # =============================================================
    # ROBUST LLM JSON PARSER
    # =============================================================

    def _parse_llm_json(self, llm_response):

        fallback = {
            "diagnosis": {
                "rootCause": (
                    "Root cause cannot currently be determined "
                    "from the available evidence."
                ),
                "confidence": 0.0,
                "status": "insufficient_evidence",
            },

            "reasoning": (
                "The AI response could not be parsed into the "
                "required structured incident-analysis format."
            ),

            "evidence": [],

            "contradictions": [
                "The LLM response was not valid structured JSON."
            ],

            "affectedFiles": [],

            "investigatedFiles": [],

            "historicalContext": {
                "relevant": False,
                "reason": (
                    "Historical context could not be reliably "
                    "evaluated because the AI response was malformed."
                ),
                "incidents": [],
            },

            "recommendation": {
                "type": "investigation_required",
                "action": (
                    "Retry the investigation with structured "
                    "JSON output."
                ),
                "targetFiles": [],
                "reason": (
                    "No production remediation should be proposed "
                    "until the AI response can be parsed reliably."
                ),
                "requiresApproval": True,
            },

            "nextInvestigation": {
                "required": True,
                "action": "Retry the AI investigation.",
                "reason": (
                    "The previous AI response was not valid "
                    "structured JSON."
                ),
            },
        }

        if llm_response is None:
            fallback["reasoning"] = (
                "The LLM returned no response."
            )
            return fallback

        # Some LLM services may already return a Python dict.
        if isinstance(llm_response, dict):
            return self._normalize_analysis(llm_response)

        text = str(llm_response).strip()

        if not text:
            fallback["reasoning"] = (
                "The LLM returned an empty response."
            )
            return fallback

        # ---------------------------------------------------------
        # Remove Markdown code fences
        # ---------------------------------------------------------

        if text.startswith("```"):

            lines = text.splitlines()

            if lines:
                first_line = lines[0].strip()

                if first_line.startswith("```"):
                    lines = lines[1:]

            if lines:
                last_line = lines[-1].strip()

                if last_line == "```":
                    lines = lines[:-1]

            text = "\n".join(lines).strip()

        # ---------------------------------------------------------
        # Attempt 1: entire response is JSON
        # ---------------------------------------------------------

        try:

            parsed = json.loads(text)

            if isinstance(parsed, dict):
                return self._normalize_analysis(parsed)

        except json.JSONDecodeError:
            pass

        # ---------------------------------------------------------
        # Attempt 2: find JSON object inside extra text
        # ---------------------------------------------------------

        start = text.find("{")
        end = text.rfind("}")

        if start != -1 and end != -1 and end > start:

            candidate = text[start:end + 1]

            try:

                parsed = json.loads(candidate)

                if isinstance(parsed, dict):
                    return self._normalize_analysis(parsed)

            except json.JSONDecodeError:
                pass

        # ---------------------------------------------------------
        # Attempt 3: try to extract a JSON object using decoder
        # ---------------------------------------------------------

        decoder = json.JSONDecoder()

        for index, character in enumerate(text):

            if character != "{":
                continue

            try:

                parsed, _ = decoder.raw_decode(
                    text[index:]
                )

                if isinstance(parsed, dict):
                    return self._normalize_analysis(parsed)

            except json.JSONDecodeError:
                continue

        # ---------------------------------------------------------
        # Final fallback
        # ---------------------------------------------------------

        fallback["rawAnalysis"] = text

        return fallback

    # =============================================================
    # NORMALIZE AI ANALYSIS
    # =============================================================

    def _normalize_analysis(self, analysis):

        if not isinstance(analysis, dict):
            return self._parse_llm_json(None)

        diagnosis = analysis.get("diagnosis")

        if not isinstance(diagnosis, dict):
            diagnosis = {}

        reasoning = analysis.get(
            "reasoning",
            "",
        )

        if reasoning is None:
            reasoning = ""

        evidence = analysis.get(
            "evidence",
            [],
        )

        if not isinstance(evidence, list):
            evidence = [str(evidence)]

        contradictions = analysis.get(
            "contradictions",
            [],
        )

        if not isinstance(contradictions, list):
            contradictions = [str(contradictions)]

        affected_files = analysis.get(
            "affectedFiles",
            [],
        )

        if not isinstance(affected_files, list):
            affected_files = []

        investigated_files = analysis.get(
            "investigatedFiles",
            [],
        )

        if not isinstance(investigated_files, list):
            investigated_files = []

        historical_context = analysis.get(
            "historicalContext"
        )

        if not isinstance(historical_context, dict):
            historical_context = {}

        historical_incidents = historical_context.get(
            "incidents",
            [],
        )

        if not isinstance(historical_incidents, list):
            historical_incidents = [
                str(historical_incidents)
            ]

        recommendation = analysis.get(
            "recommendation"
        )

        if not isinstance(recommendation, dict):
            recommendation = {}

        target_files = recommendation.get(
            "targetFiles",
            [],
        )

        if not isinstance(target_files, list):
            target_files = []

        next_investigation = analysis.get(
            "nextInvestigation"
        )

        if not isinstance(next_investigation, dict):
            next_investigation = {}

        root_cause = diagnosis.get(
            "rootCause"
        )

        if not root_cause:
            root_cause = (
                "Root cause cannot currently be determined "
                "from the available evidence."
            )

        confidence = diagnosis.get(
            "confidence",
            0.0,
        )

        try:
            confidence = float(confidence)
        except (TypeError, ValueError):
            confidence = 0.0

        confidence = max(
            0.0,
            min(1.0, confidence),
        )

        diagnosis_status = diagnosis.get(
            "status",
            "insufficient_evidence",
        )

        valid_statuses = {
            "confirmed",
            "supported",
            "unconfirmed",
            "insufficient_evidence",
            "contradicted",
        }

        if diagnosis_status not in valid_statuses:
            diagnosis_status = "insufficient_evidence"

        recommendation_type = recommendation.get(
            "type",
            "investigation_required",
        )

        valid_recommendation_types = {
            "code_change",
            "configuration_change",
            "operational_action",
            "investigation_required",
        }

        if (
            recommendation_type
            not in valid_recommendation_types
        ):
            recommendation_type = "investigation_required"

        recommendation_action = recommendation.get(
            "action"
        )

        if not recommendation_action:
            recommendation_action = (
                "Perform additional investigation before "
                "taking remediation action."
            )

        recommendation_reason = recommendation.get(
            "reason"
        )

        if not recommendation_reason:
            recommendation_reason = (
                "Available evidence is insufficient to "
                "justify a state-changing remediation."
            )

        requires_approval = recommendation.get(
            "requiresApproval",
            True,
        )

        # The agent never gets to bypass human approval for a
        # state-changing recommendation, even if the LLM returns false.
        if recommendation_type in {
            "code_change",
            "configuration_change",
            "operational_action",
        }:
            requires_approval = True

        return {
            "diagnosis": {
                "rootCause": root_cause,
                "confidence": confidence,
                "status": diagnosis_status,
            },

            "reasoning": str(reasoning),

            "evidence": evidence,

            "contradictions": contradictions,

            "affectedFiles": affected_files,

            "investigatedFiles": investigated_files,

            "historicalContext": {
                "relevant": bool(
                    historical_context.get(
                        "relevant",
                        False,
                    )
                ),
                "reason": str(
                    historical_context.get(
                        "reason",
                        "No historical context available.",
                    )
                ),
                "incidents": historical_incidents,
            },

            "recommendation": {
                "type": recommendation_type,
                "action": str(
                    recommendation_action
                ),
                "targetFiles": target_files,
                "reason": str(
                    recommendation_reason
                ),
                "requiresApproval": bool(
                    requires_approval
                ),
            },

            "nextInvestigation": {
                "required": bool(
                    next_investigation.get(
                        "required",
                        True,
                    )
                ),
                "action": str(
                    next_investigation.get(
                        "action",
                        "Perform additional investigation.",
                    )
                ),
                "reason": str(
                    next_investigation.get(
                        "reason",
                        "Additional evidence is required.",
                    )
                ),
            },

            **(
                {"rawAnalysis": analysis["rawAnalysis"]}
                if "rawAnalysis" in analysis
                else {}
            ),
        }

    # =============================================================
    # INCIDENT PERSISTENCE
    # =============================================================

    def _save_incident(
        self,
        incident: IncidentAnalysisRequest,
        user_id: int,
        ai_analysis: dict,
    ):

        diagnosis = ai_analysis.get(
            "diagnosis",
            {},
        )

        recommendation = ai_analysis.get(
            "recommendation",
            {},
        )

        diagnosis_status = diagnosis.get(
            "status"
        )

        if diagnosis_status == "confirmed":
            status = "DIAGNOSED"

        elif diagnosis_status in {
            "supported",
            "unconfirmed",
            "insufficient_evidence",
            "contradicted",
        }:
            status = "INVESTIGATING"

        else:
            status = "INVESTIGATING"

        connection = get_connection()

        cursor = connection.cursor()

        query = """
            INSERT INTO incidents (
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
            )
            VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s,
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """

        values = (
            incident.application_id,
            user_id,
            incident.service,
            incident.latencyMs,
            incident.errorRate,
            incident.dbConnections,
            incident.dbConnectionLimit,
            incident.cpu,
            incident.memory,
            status,
            diagnosis.get("rootCause"),
            diagnosis.get("confidence"),
            diagnosis_status,
            ai_analysis.get("reasoning"),
            recommendation.get("type"),
            recommendation.get("action"),
            recommendation.get("reason"),
            bool(
                recommendation.get(
                    "requiresApproval",
                    True,
                )
            ),
        )

        try:

            cursor.execute(
                query,
                values,
            )

            connection.commit()

            incident_id = cursor.lastrowid

        except Exception:

            connection.rollback()

            raise

        finally:

            cursor.close()
            connection.close()

        return incident_id