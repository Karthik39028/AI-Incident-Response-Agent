import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Brain,
  CheckCircle2,
  ChevronRight,
  Clock,
  Database,
  Gauge,
  Loader2,
  Server,
  ShieldAlert,
  Sparkles,
  Zap,
} from "lucide-react";

import "./IncidentDetails.css";

const API_URL = "http://localhost:8081";

function IncidentDetails() {
  const { id } = useParams();

  const [application, setApplication] = useState(null);

  const [form, setForm] = useState({
    service: "",
    latencyMs: 9400,
    errorRate: 18.2,
    dbConnections: 97,
    dbConnectionLimit: 100,
    cpu: 48,
    memory: 61,
  });

  const [analysis, setAnalysis] = useState(null);

  const [loadingApplication, setLoadingApplication] =
    useState(true);

  const [analyzing, setAnalyzing] =
    useState(false);

  const [recoveryAction, setRecoveryAction] =
    useState(null);

  const [creatingRecovery, setCreatingRecovery] =
    useState(false);

  const [approvingRecovery, setApprovingRecovery] =
    useState(false);

  const [investigatingAgain, setInvestigatingAgain] =
    useState(false);

  const [error, setError] = useState("");

  useEffect(() => {
    loadApplication();
  }, [id]);

  // =========================================================
  // LOAD APPLICATION
  // =========================================================

  const loadApplication = async () => {
    try {
      setLoadingApplication(true);
      setError("");

      const response = await fetch(
        `${API_URL}/api/applications/${id}`,
        {
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to load application."
        );
      }

      setApplication(data.application);

      setForm((previous) => ({
        ...previous,
        service:
          data.application?.name || "",
      }));
    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to load application."
      );
    } finally {
      setLoadingApplication(false);
    }
  };

  // =========================================================
  // HANDLE FORM
  // =========================================================

  const handleChange = (event) => {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]:
        name === "service"
          ? value
          : Number(value),
    }));
  };

  // =========================================================
  // ANALYZE INCIDENT
  // =========================================================

  const analyzeIncident = async () => {
    try {
      setAnalyzing(true);
      setError("");
      setAnalysis(null);
      setRecoveryAction(null);

      const payload = {
        application_id: Number(id),
        service: form.service,
        latencyMs: Number(form.latencyMs),
        errorRate: Number(form.errorRate),
        dbConnections: Number(form.dbConnections),
        dbConnectionLimit: Number(form.dbConnectionLimit),
        cpu: Number(form.cpu),
        memory: Number(form.memory),
      };

      const response = await fetch(
        `${API_URL}/api/incidents/analyze`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          credentials: "include",

          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Incident analysis failed."
        );
      }

      setAnalysis(data);

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to analyze incident."
      );
    } finally {
      setAnalyzing(false);
    }
  };

  // =========================================================
  // CREATE RECOVERY / INVESTIGATION ACTION
  // =========================================================

  const createRecoveryAction = async () => {
    try {
      setCreatingRecovery(true);
      setError("");

      const incidentId =
        analysis?.incidentId;

      if (!incidentId) {
        throw new Error(
          "No persisted incident ID was returned by the analysis."
        );
      }

      const response = await fetch(
        `${API_URL}/api/recovery/incidents/${incidentId}/action`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to create recovery action."
        );
      }

      // Backend response: { success: true, recovery: { action: { id: ... } } }
      const actionId =
        data.recovery?.action?.id ??
        data.recovery?.action?.actionId ??
        data.recovery?.actionId ??
        data.actionId ??
        data.action?.id ??
        data.action?.actionId;

      if (!actionId) {
        throw new Error(
          "Action was created but no action ID was returned."
        );
      }

      const actionResponse = await fetch(
        `${API_URL}/api/recovery/actions/${actionId}`,
        {
          credentials: "include",
        }
      );

      const actionData =
        await actionResponse.json();

      if (!actionResponse.ok) {
        throw new Error(
          actionData.detail ||
            "Unable to load the action."
        );
      }

      setRecoveryAction(
        actionData.recovery
      );

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to create action."
      );
    } finally {
      setCreatingRecovery(false);
    }
  };

  // =========================================================
  // APPROVE ACTION
  // =========================================================

  const approveRecoveryAction = async () => {
    try {
      setApprovingRecovery(true);
      setError("");

      if (!recoveryAction?.id) {
        throw new Error(
          "No action is available for approval."
        );
      }

      const response = await fetch(
        `${API_URL}/api/recovery/actions/${recoveryAction.id}/approve`,
        {
          method: "POST",
          credentials: "include",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to approve action."
        );
      }

      setRecoveryAction((previous) => ({
        ...previous,

        status:
          data.recovery?.status ||
          "APPROVED",

        approved_by:
          data.recovery?.approvedBy ||
          previous?.approved_by,
      }));

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to approve action."
      );
    } finally {
      setApprovingRecovery(false);
    }
  };

  // =========================================================
  // INVESTIGATE AGAIN
  // =========================================================

  const investigateAgain = async () => {
    try {
      setInvestigatingAgain(true);
      setError("");

      if (!recoveryAction?.id) {
        throw new Error(
          "No approved investigation action is available."
        );
      }

      if (
        recoveryAction.action_type !==
        "investigation_required"
      ) {
        throw new Error(
          "This action is not an investigation action."
        );
      }

      if (
        recoveryAction.status !==
        "APPROVED"
      ) {
        throw new Error(
          "The investigation must be approved before running it."
        );
      }

      const payload = {
        application_id: Number(id),
        service: form.service,
        latencyMs: Number(form.latencyMs),
        errorRate: Number(form.errorRate),
        dbConnections: Number(form.dbConnections),
        dbConnectionLimit: Number(form.dbConnectionLimit),
        cpu: Number(form.cpu),
        memory: Number(form.memory),
      };

      const response = await fetch(
        `${API_URL}/api/recovery/actions/${recoveryAction.id}/investigate`,
        {
          method: "POST",

          headers: {
            "Content-Type": "application/json",
          },

          credentials: "include",

          body: JSON.stringify(payload),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Investigation failed."
        );
      }

      /*
       * The backend returns:
       *
       * {
       *   success: true,
       *   message: "...",
       *   investigation: {...}
       * }
       *
       * Keep this defensive so the UI also works
       * if the backend returns the analysis object
       * directly.
       */
      const newAnalysis =
        data.investigation || data;

      setAnalysis(newAnalysis);

      /*
       * The old investigation action belongs to the
       * previous incident attempt. Clear it so the
       * engineer can create a NEW recovery/investigation
       * action for the NEW analysis.
       */
      setRecoveryAction(null);

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to investigate the incident again."
      );
    } finally {
      setInvestigatingAgain(false);
    }
  };

  // =========================================================
  // ANALYSIS DATA
  // =========================================================

  const confidence =
    analysis?.aiAnalysis?.diagnosis?.confidence;

  const confidencePercent =
    typeof confidence === "number"
      ? Math.round(confidence * 100)
      : null;

  const diagnosis =
    analysis?.aiAnalysis?.diagnosis;

  const historical =
    analysis?.aiAnalysis?.historicalContext;

  const recommendation =
    analysis?.aiAnalysis?.recommendation;

  const recommendationType =
    recommendation?.type ||
    recommendation?.recommendationType ||
    recommendation?.recommendation_type;

  const isInvestigation =
    recommendationType ===
    "investigation_required";

  // =========================================================
  // LOADING
  // =========================================================

  if (loadingApplication) {
    return (
      <div className="incident-loading-page">

        <Loader2
          size={30}
          className="incident-spinner"
        />

        <p>
          Loading incident analyzer...
        </p>

      </div>
    );
  }

  // =========================================================
  // APPLICATION NOT FOUND
  // =========================================================

  if (!application) {
    return (
      <div className="incident-error-page">

        <div className="incident-error-icon">
          <AlertTriangle size={28} />
        </div>

        <h2>
          Application not found
        </h2>

        <p>
          {error ||
            "The application could not be loaded."}
        </p>

        <Link
          to="/applications"
          className="back-applications"
        >
          <ArrowLeft size={17} />
          Back to Applications
        </Link>

      </div>
    );
  }

  // =========================================================
  // PAGE
  // =========================================================

  return (
    <div className="incident-details-page">

      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="incident-header">

        <div className="incident-header-left">

          <Link
            to={`/applications/${id}`}
            className="incident-back-button"
          >
            <ArrowLeft size={18} />
          </Link>

          <div>

            <div className="incident-breadcrumb">

              <Link to="/applications">
                Applications
              </Link>

              <ChevronRight size={13} />

              <Link
                to={`/applications/${id}`}
              >
                {application.name}
              </Link>

              <ChevronRight size={13} />

              <span>
                Incident Analysis
              </span>

            </div>

            <div className="incident-title-row">

              <div className="incident-title-icon">
                <Sparkles size={21} />
              </div>

              <div>

                <h1>
                  Incident Analysis
                </h1>

                <p>
                  Investigate an incident using
                  telemetry and historical experience.
                </p>

              </div>

            </div>

          </div>

        </div>

      </header>


      <main className="incident-content">

        {/* =================================================
            ERROR
        ================================================= */}

        {error && (

          <div className="incident-error-banner">

            <AlertTriangle size={18} />

            <span>
              {error}
            </span>

          </div>

        )}


        {/* =================================================
            INPUT
        ================================================= */}

        <section className="incident-input-panel">

          <div className="incident-panel-heading">

            <div className="incident-panel-icon">
              <Activity size={19} />
            </div>

            <div>

              <h2>
                Current Telemetry
              </h2>

              <p>
                Enter the current production metrics
                for this incident.
              </p>

            </div>

          </div>


          <div className="incident-form">

            {/* SERVICE */}

            <div className="incident-field full">

              <label>
                Service
              </label>

              <div className="incident-input-icon">

                <Server size={16} />

                <input
                  type="text"
                  name="service"
                  value={form.service}
                  onChange={handleChange}
                  placeholder="payment-service"
                />

              </div>

            </div>


            {/* LATENCY */}

            <div className="incident-field">

              <label>
                Latency
                <span>ms</span>
              </label>

              <div className="metric-input">

                <Gauge size={16} />

                <input
                  type="number"
                  name="latencyMs"
                  value={form.latencyMs}
                  onChange={handleChange}
                  min="0"
                />

                <small>ms</small>

              </div>

            </div>


            {/* ERROR RATE */}

            <div className="incident-field">

              <label>
                Error Rate
                <span>%</span>
              </label>

              <div className="metric-input">

                <AlertTriangle size={16} />

                <input
                  type="number"
                  name="errorRate"
                  value={form.errorRate}
                  onChange={handleChange}
                  min="0"
                  step="0.1"
                />

                <small>%</small>

              </div>

            </div>


            {/* DB CONNECTIONS */}

            <div className="incident-field">

              <label>
                DB Connections
              </label>

              <div className="metric-input">

                <Database size={16} />

                <input
                  type="number"
                  name="dbConnections"
                  value={form.dbConnections}
                  onChange={handleChange}
                  min="0"
                />

              </div>

            </div>


            {/* DB LIMIT */}

            <div className="incident-field">

              <label>
                DB Connection Limit
              </label>

              <div className="metric-input">

                <Database size={16} />

                <input
                  type="number"
                  name="dbConnectionLimit"
                  value={
                    form.dbConnectionLimit
                  }
                  onChange={handleChange}
                  min="1"
                />

              </div>

            </div>


            {/* CPU */}

            <div className="incident-field">

              <label>
                CPU Utilization
                <span>%</span>
              </label>

              <div className="metric-input">

                <Activity size={16} />

                <input
                  type="number"
                  name="cpu"
                  value={form.cpu}
                  onChange={handleChange}
                  min="0"
                  max="100"
                  step="0.1"
                />

                <small>%</small>

              </div>

            </div>


            {/* MEMORY */}

            <div className="incident-field">

              <label>
                Memory Utilization
                <span>%</span>
              </label>

              <div className="metric-input">

                <Activity size={16} />

                <input
                  type="number"
                  name="memory"
                  value={form.memory}
                  onChange={handleChange}
                  min="0"
                  max="100"
                  step="0.1"
                />

                <small>%</small>

              </div>

            </div>

          </div>


          {/* ANALYZE BUTTON */}

          <div className="analyze-action">

            <div className="analyze-hint">

              <Brain size={17} />

              <span>
                AI will compare current telemetry
                with repository evidence and
                historical experience.
              </span>

            </div>

            <button
              className="run-analysis-button"
              onClick={analyzeIncident}
              disabled={analyzing}
            >

              {analyzing ? (
                <>
                  <Loader2
                    size={17}
                    className="button-spin"
                  />

                  Analyzing...
                </>
              ) : (
                <>
                  <Sparkles size={17} />

                  Analyze Incident
                </>
              )}

            </button>

          </div>

        </section>


        {/* =================================================
            PLACEHOLDER
        ================================================= */}

        {!analysis && !analyzing && (

          <section className="analysis-placeholder">

            <div className="placeholder-icon">
              <Brain size={30} />
            </div>

            <h2>
              Ready to investigate
            </h2>

            <p>
              Enter the current telemetry above and
              run the AI analysis. The agent will
              evaluate the current evidence, inspect
              repository context, and compare it
              with historical experience.
            </p>

          </section>

        )}


        {/* =================================================
            ANALYZING
        ================================================= */}

        {analyzing && (

          <section className="analysis-placeholder">

            <div className="analysis-animation">
              <Sparkles size={28} />
            </div>

            <h2>
              Analyzing incident...
            </h2>

            <p>
              Understanding the repository,
              checking telemetry, searching
              Hindsight memory, and generating
              an evidence-based analysis.
            </p>

          </section>

        )}


        {/* =================================================
            RESULTS
        ================================================= */}

        {analysis && !analyzing && (

          <div className="analysis-results">

            {/* =================================================
                DIAGNOSIS
            ================================================= */}

            <section className="diagnosis-card">

              <div className="diagnosis-top">

                <div>

                  <span className="result-label">
                    AI DIAGNOSIS
                  </span>

                  <h2>
                    {diagnosis?.rootCause ||
                      "Analysis completed"}
                  </h2>

                </div>


                {confidencePercent !== null && (

                  <div className="confidence">

                    <span>
                      Confidence
                    </span>

                    <strong>
                      {confidencePercent}%
                    </strong>

                    <div className="confidence-bar">

                      <div
                        style={{
                          width: `${confidencePercent}%`,
                        }}
                      />

                    </div>

                  </div>

                )}

              </div>


              <div className="diagnosis-reasoning">

                <div className="reasoning-icon">
                  <Brain size={18} />
                </div>

                <div>

                  <h3>
                    Reasoning
                  </h3>

                  <p>
                    {analysis.aiAnalysis
                      ?.reasoning ||
                      "No reasoning returned."}
                  </p>

                </div>

              </div>

            </section>


            {/* =================================================
                EVIDENCE + HISTORY
            ================================================= */}

            <div className="result-grid">

              {/* EVIDENCE */}

              <section className="result-card">

                <div className="result-card-header">

                  <div className="result-card-icon blue">
                    <CheckCircle2 size={18} />
                  </div>

                  <div>

                    <h2>
                      Evidence
                    </h2>

                    <p>
                      Signals supporting the diagnosis.
                    </p>

                  </div>

                </div>


                <div className="evidence-list">

                  {Array.isArray(
                    analysis.aiAnalysis?.evidence
                  ) &&
                  analysis.aiAnalysis.evidence
                    .length > 0 ? (

                    analysis.aiAnalysis.evidence.map(
                      (item, index) => (

                        <div
                          className="evidence-item"
                          key={index}
                        >

                          <CheckCircle2 size={15} />

                          <span>
                            {item}
                          </span>

                        </div>

                      )
                    )

                  ) : (

                    <p className="no-result">
                      No evidence returned.
                    </p>

                  )}

                </div>

              </section>


              {/* HISTORICAL CONTEXT */}

              <section className="result-card">

                <div className="result-card-header">

                  <div className="result-card-icon purple">
                    <Brain size={18} />
                  </div>

                  <div>

                    <h2>
                      Historical Context
                    </h2>

                    <p>
                      Experience retrieved from Hindsight.
                    </p>

                  </div>

                </div>


                <div className="historical-content">

                  <div
                    className={`historical-status ${
                      historical?.relevant
                        ? "relevant"
                        : "not-relevant"
                    }`}
                  >

                    {historical?.relevant ? (
                      <CheckCircle2 size={15} />
                    ) : (
                      <AlertTriangle size={15} />
                    )}

                    <span>
                      {historical?.relevant
                        ? "Relevant historical experience"
                        : "No relevant historical experience"}
                    </span>

                  </div>


                  <p>
                    {historical?.reason ||
                      "No historical context returned."}
                  </p>


                  {Array.isArray(
                    historical?.incidents
                  ) &&
                  historical.incidents.length > 0 && (

                    <div className="historical-incidents">

                      <span>
                        Related incidents
                      </span>

                      {historical.incidents.map(
                        (incident, index) => (

                          <div
                            key={index}
                            className="historical-incident"
                          >
                            {incident}
                          </div>

                        )
                      )}

                    </div>

                  )}

                </div>

              </section>

            </div>


            {/* =================================================
                RECOMMENDATION
            ================================================= */}

            <section className="recommendation-card">

              <div className="recommendation-header">

                <div className="recommendation-icon">
                  <Zap size={19} />
                </div>

                <div>

                  <span>
                    {isInvestigation
                      ? "RECOMMENDED NEXT INVESTIGATION"
                      : "RECOMMENDED NEXT ACTION"}
                  </span>

                  <h2>
                    {recommendation?.action ||
                      "No recommendation returned."}
                  </h2>

                </div>

              </div>


              <div className="recommendation-body">

                <p>
                  {recommendation?.reason ||
                    "No recommendation reason returned."}
                </p>


                {recommendation?.requiresApproval && (

                  <div className="approval-warning">

                    <ShieldAlert size={17} />

                    <div>

                      <strong>
                        Human approval required
                      </strong>

                      <span>
                        This recommendation should be
                        reviewed by an engineer before
                        taking action.
                      </span>

                    </div>

                  </div>

                )}


                {/* =================================================
                    ACTION
                ================================================= */}

                {recommendation && (

                  <div
                    style={{
                      marginTop: "20px",
                      paddingTop: "18px",
                      borderTop:
                        "1px solid rgba(255,255,255,0.08)",
                    }}
                  >

                    {!recoveryAction && (

                      <button
                        className="run-analysis-button"
                        onClick={createRecoveryAction}
                        disabled={
                          creatingRecovery ||
                          investigatingAgain
                        }
                      >

                        {creatingRecovery ? (
                          <>
                            <Loader2
                              size={17}
                              className="button-spin"
                            />

                            {isInvestigation
                              ? "Creating Investigation..."
                              : "Creating Recovery Action..."}
                          </>
                        ) : (
                          <>
                            <ShieldAlert size={17} />

                            {isInvestigation
                              ? "Investigate Further"
                              : "Create Recovery Action"}
                          </>
                        )}

                      </button>

                    )}


                    {recoveryAction && (

                      <div>

                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "10px",
                            marginBottom: "12px",
                          }}
                        >

                          {recoveryAction.status ===
                          "APPROVED" ? (
                            <CheckCircle2
                              size={18}
                              style={{
                                color: "#22c55e",
                              }}
                            />
                          ) : (
                            <ShieldAlert
                              size={18}
                              style={{
                                color: "#f59e0b",
                              }}
                            />
                          )}

                          <strong>

                            {recoveryAction.action_type ===
                            "investigation_required"
                              ? "Investigation: "
                              : "Recovery Action: "}

                            {recoveryAction.status}

                          </strong>

                        </div>


                        <p>
                          {recoveryAction.action_description ||
                            recoveryAction.action ||
                            "No action description available."}
                        </p>


                        {/* APPROVAL BUTTON */}

                        {(
                          recoveryAction.status ===
                            "PENDING_APPROVAL" ||
                          recoveryAction.status ===
                            "INVESTIGATION_PENDING"
                        ) && (

                          <button
                            className="run-analysis-button"
                            onClick={
                              approveRecoveryAction
                            }
                            disabled={approvingRecovery}
                            style={{
                              marginTop: "12px",
                            }}
                          >

                            {approvingRecovery ? (
                              <>
                                <Loader2
                                  size={17}
                                  className="button-spin"
                                />

                                Approving...
                              </>
                            ) : (
                              <>
                                <CheckCircle2
                                  size={17}
                                />

                                {recoveryAction.action_type ===
                                "investigation_required"
                                  ? "Approve Investigation"
                                  : "Approve Recovery Action"}

                              </>
                            )}

                          </button>

                        )}


                        {/* INVESTIGATION APPROVED */}

                        {recoveryAction.action_type ===
                          "investigation_required" &&
                        recoveryAction.status ===
                          "APPROVED" && (

                          <div
                            style={{
                              marginTop: "14px",
                              padding: "16px",
                              borderRadius: "10px",
                              border:
                                "1px solid rgba(34,197,94,0.25)",
                              background:
                                "rgba(34,197,94,0.06)",
                            }}
                          >

                            <p
                              style={{
                                margin: 0,
                                color: "#22c55e",
                              }}
                            >
                              Human approval recorded.
                              Investigation is now authorized.
                            </p>

                            <p
                              style={{
                                marginTop: "8px",
                                marginBottom: 0,
                                opacity: 0.8,
                              }}
                            >
                              Update the telemetry values above
                              with the latest production evidence,
                              then run the investigation again.
                            </p>

                            <button
                              className="run-analysis-button"
                              onClick={
                                investigateAgain
                              }
                              disabled={
                                investigatingAgain
                              }
                              style={{
                                marginTop: "14px",
                              }}
                            >

                              {investigatingAgain ? (
                                <>
                                  <Loader2
                                    size={17}
                                    className="button-spin"
                                  />

                                  Investigating Again...
                                </>
                              ) : (
                                <>
                                  <Brain size={17} />

                                  Investigate Again
                                </>
                              )}

                            </button>

                          </div>

                        )}


                        {/* NORMAL RECOVERY APPROVED */}

                        {recoveryAction.action_type !==
                          "investigation_required" &&
                        recoveryAction.status ===
                          "APPROVED" && (

                          <p
                            style={{
                              marginTop: "12px",
                              color: "#22c55e",
                            }}
                          >
                            Human approval recorded.
                            No recovery operation has
                            been executed yet.
                          </p>

                        )}

                      </div>

                    )}

                  </div>

                )}

              </div>

            </section>


            {/* =================================================
                TELEMETRY
            ================================================= */}

            <section className="telemetry-result-card">

              <div className="result-card-header">

                <div className="result-card-icon green">
                  <Activity size={18} />
                </div>

                <div>

                  <h2>
                    Incident Telemetry
                  </h2>

                  <p>
                    Values used by the AI during analysis.
                  </p>

                </div>

              </div>


              <div className="telemetry-grid">

                <Telemetry
                  label="Service"
                  value={analysis.incident?.service}
                />

                <Telemetry
                  label="Latency"
                  value={`${analysis.incident?.latencyMs} ms`}
                />

                <Telemetry
                  label="Error Rate"
                  value={`${analysis.incident?.errorRate}%`}
                />

                <Telemetry
                  label="DB Connections"
                  value={`${analysis.incident?.dbConnections} / ${analysis.incident?.dbConnectionLimit}`}
                />

                <Telemetry
                  label="DB Utilization"
                  value={`${analysis.incident?.dbConnectionUtilization}%`}
                />

                <Telemetry
                  label="CPU"
                  value={`${analysis.incident?.cpu}%`}
                />

                <Telemetry
                  label="Memory"
                  value={`${analysis.incident?.memory}%`}
                />

              </div>

            </section>


            {/* =================================================
                HINDSIGHT QUERY
            ================================================= */}

            {analysis.hindsightQuery && (

              <section className="hindsight-query">

                <Clock size={15} />

                <div>

                  <span>
                    HINDSIGHT QUERY
                  </span>

                  <p>
                    {analysis.hindsightQuery}
                  </p>

                </div>

              </section>

            )}

          </div>

        )}

      </main>

    </div>
  );
}


// =========================================================
// TELEMETRY COMPONENT
// =========================================================

function Telemetry({
  label,
  value,
}) {
  return (
    <div className="telemetry-item">

      <span>
        {label}
      </span>

      <strong>
        {value ?? "-"}
      </strong>

    </div>
  );
}


export default IncidentDetails;