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

  const [error, setError] = useState("");

  useEffect(() => {
    loadApplication();
  }, [id]);

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

  const analyzeIncident = async () => {
    try {
      setAnalyzing(true);
      setError("");
      setAnalysis(null);

      const payload = {
        service: form.service,
        latencyMs: Number(form.latencyMs),
        errorRate: Number(form.errorRate),
        dbConnections: Number(
          form.dbConnections
        ),
        dbConnectionLimit: Number(
          form.dbConnectionLimit
        ),
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

  return (
    <div className="incident-details-page">

      {/* ================= HEADER ================= */}

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

        {/* ================= ERROR ================= */}

        {error && (

          <div className="incident-error-banner">

            <AlertTriangle size={18} />

            <span>
              {error}
            </span>

          </div>

        )}


        {/* ================= INPUT SECTION ================= */}

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
                with historical incidents.
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


        {/* ================= RESULTS ================= */}

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
              evaluate the current evidence and compare
              it with historical experience.
            </p>

          </section>

        )}


        {analyzing && (

          <section className="analysis-placeholder">

            <div className="analysis-animation">

              <Sparkles size={28} />

            </div>

            <h2>
              Analyzing incident...
            </h2>

            <p>
              Checking current telemetry, searching
              Hindsight memory, and generating an
              evidence-based analysis.
            </p>

          </section>

        )}


        {analysis && !analyzing && (

          <div className="analysis-results">

            {/* ================= DIAGNOSIS ================= */}

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


            {/* ================= TWO COLUMN RESULTS ================= */}

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


            {/* ================= RECOMMENDATION ================= */}

            <section className="recommendation-card">

              <div className="recommendation-header">

                <div className="recommendation-icon">
                  <Zap size={19} />
                </div>

                <div>

                  <span>
                    RECOMMENDED NEXT ACTION
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

              </div>

            </section>


            {/* ================= TELEMETRY ================= */}

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


            {/* ================= HINDSIGHT QUERY ================= */}

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


/* ================= TELEMETRY COMPONENT ================= */

function Telemetry({ label, value }) {
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