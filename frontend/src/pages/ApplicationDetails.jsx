import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";

import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  Brain,
  Calendar,
  CheckCircle2,
  ChevronRight,
  Clock,
  ExternalLink,
  GitBranch,
  Globe,
  Layers3,
  Server,
  ShieldCheck,
  Sparkles,
  Terminal,
} from "lucide-react";

import "./ApplicationDetails.css";

const API_URL = "http://localhost:8081";

function ApplicationDetails() {
  const { id } = useParams();

  const [application, setApplication] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadApplication();
  }, [id]);

  const loadApplication = async () => {
    try {
      setLoading(true);
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
          data.detail || "Application not found."
        );
      }

      setApplication(data.application);

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to load application."
      );
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (date) => {
    if (!date) return "Not available";

    return new Date(date).toLocaleString(
      "en-IN",
      {
        dateStyle: "medium",
        timeStyle: "short",
      }
    );
  };

  if (loading) {
    return (
      <div className="application-details-loading">
        <div className="details-spinner"></div>
        <p>Loading application...</p>
      </div>
    );
  }

  if (error || !application) {
    return (
      <div className="application-details-error-page">

        <div className="details-error-icon">
          <AlertTriangle size={28} />
        </div>

        <h2>
          Unable to load application
        </h2>

        <p>
          {error || "Application not found."}
        </p>

        <Link
          to="/applications"
          className="back-to-applications"
        >
          <ArrowLeft size={17} />
          Back to Applications
        </Link>

      </div>
    );
  }

  return (
    <div className="application-details-page">

      {/* ================= HEADER ================= */}

      <header className="details-header">

        <div className="details-header-left">

          <Link
            to="/applications"
            className="details-back-button"
          >
            <ArrowLeft size={18} />
          </Link>

          <div className="breadcrumb">

            <Link to="/applications">
              Applications
            </Link>

            <ChevronRight size={14} />

            <span>
              {application.name}
            </span>

          </div>

        </div>

      </header>


      {/* ================= MAIN ================= */}

      <main className="details-content">

        {/* ================= APPLICATION HERO ================= */}

        <section className="application-hero">

          <div className="application-hero-left">

            <div className="large-application-icon">
              <Server size={29} />
            </div>

            <div>

              <div className="application-hero-title">

                <h1>
                  {application.name}
                </h1>

                <span
                  className={`details-status ${
                    application.status === "active"
                      ? "active"
                      : "inactive"
                  }`}
                >
                  <span></span>

                  {application.status || "active"}
                </span>

              </div>

              <p>
                {application.description ||
                  "No description provided for this application."}
              </p>

            </div>

          </div>


          <div className="hero-actions">

            {application.runtime_url && (
              <a
                href={application.runtime_url}
                target="_blank"
                rel="noreferrer"
                className="outline-action"
              >
                <Globe size={16} />
                Open Application
                <ExternalLink size={13} />
              </a>
            )}

            {application.source_url && (
              <a
                href={application.source_url}
                target="_blank"
                rel="noreferrer"
                className="outline-action"
              >
                <GitBranch  size={16} />
                Repository
                <ExternalLink size={13} />
              </a>
            )}

          </div>

        </section>


        {/* ================= STATUS CARDS ================= */}

        <section className="details-stats">

          <div className="details-stat-card">

            <div className="details-stat-icon green">
              <CheckCircle2 size={20} />
            </div>

            <div>
              <span>Status</span>

              <strong>
                {application.status || "active"}
              </strong>
            </div>

          </div>


          <div className="details-stat-card">

            <div className="details-stat-icon blue">
              <Terminal size={20} />
            </div>

            <div>
              <span>Runtime</span>

              <strong>
                {application.runtime_type ||
                  "Not specified"}
              </strong>
            </div>

          </div>


          <div className="details-stat-card">

            <div className="details-stat-icon purple">
              <Layers3 size={20} />
            </div>

            <div>
              <span>Deployment</span>

              <strong>
                {application.deployment_type ||
                  "Not specified"}
              </strong>
            </div>

          </div>


          <div className="details-stat-card">

            <div className="details-stat-icon orange">
              <AlertTriangle size={20} />
            </div>

            <div>
              <span>Incidents</span>

              <strong>0</strong>
            </div>

          </div>

        </section>


        {/* ================= TWO COLUMN ================= */}

        <div className="details-grid">


          {/* LEFT */}

          <div className="details-main-column">

            {/* Technical Information */}

            <section className="details-panel">

              <div className="panel-heading">

                <div className="panel-heading-icon">
                  <Server size={18} />
                </div>

                <div>
                  <h2>Technical Information</h2>

                  <p>
                    Configuration of this application.
                  </p>
                </div>

              </div>


              <div className="technical-grid">

                <div className="technical-item">

                  <span className="technical-label">
                    Runtime
                  </span>

                  <strong>
                    {application.runtime_type ||
                      "Not specified"}
                  </strong>

                </div>


                <div className="technical-item">

                  <span className="technical-label">
                    Deployment
                  </span>

                  <strong>
                    {application.deployment_type ||
                      "Not specified"}
                  </strong>

                </div>


                <div className="technical-item">

                  <span className="technical-label">
                    Source Type
                  </span>

                  <strong>
                    {application.source_type ||
                      "Not specified"}
                  </strong>

                </div>


                <div className="technical-item">

                  <span className="technical-label">
                    Runtime URL
                  </span>

                  {application.runtime_url ? (

                    <a
                      href={application.runtime_url}
                      target="_blank"
                      rel="noreferrer"
                      className="technical-link"
                    >
                      {application.runtime_url}
                      <ExternalLink size={12} />
                    </a>

                  ) : (
                    <strong>
                      Not specified
                    </strong>
                  )}

                </div>


                <div className="technical-item full">

                  <span className="technical-label">
                    Repository
                  </span>

                  {application.source_url ? (

                    <a
                      href={application.source_url}
                      target="_blank"
                      rel="noreferrer"
                      className="technical-link"
                    >
                      <GitBranch  size={14} />

                      {application.source_url}

                      <ExternalLink size={12} />
                    </a>

                  ) : (
                    <strong>
                      Not specified
                    </strong>
                  )}

                </div>

              </div>

            </section>


            {/* AI Incident Response */}

            <section className="incident-response-panel">

              <div className="incident-response-content">

                <div className="ai-icon">
                  <Sparkles size={22} />
                </div>

                <div>

                  <span className="ai-label">
                    AI INCIDENT RESPONSE
                  </span>

                  <h2>
                    Analyze an Incident
                  </h2>

                  <p>
                    Provide current application telemetry
                    and let the AI analyze the incident using
                    historical experience from Hindsight.
                  </p>

                </div>

              </div>


              <Link
                to={`/incidents/${application.id}`}
                className="analyze-button"
              >
                <Sparkles size={16} />
                Analyze Incident
                <ChevronRight size={16} />
              </Link>

            </section>


            {/* Monitoring */}

            <section className="details-panel">

              <div className="panel-heading">

                <div className="panel-heading-icon green">
                  <Activity size={18} />
                </div>

                <div>
                  <h2>Monitoring</h2>

                  <p>
                    Current monitoring status.
                  </p>
                </div>

              </div>


              <div className="monitoring-box">

                <div className="monitoring-status">

                  <div className="monitoring-check">
                    <CheckCircle2 size={18} />
                  </div>

                  <div>

                    <strong>
                      Application connected
                    </strong>

                    <p>
                      IncidentAI is ready to analyze
                      incidents for this application.
                    </p>

                  </div>

                </div>


                <div className="monitoring-line">

                  <span>
                    Monitoring
                  </span>

                  <strong>
                    Ready
                  </strong>

                </div>


                <div className="monitoring-line">

                  <span>
                    AI Analysis
                  </span>

                  <strong>
                    Available
                  </strong>

                </div>

              </div>

            </section>

          </div>


          {/* RIGHT */}

          <aside className="details-side-column">

            {/* Dates */}

            <section className="details-panel">

              <div className="panel-heading">

                <div className="panel-heading-icon">
                  <Calendar size={18} />
                </div>

                <div>
                  <h2>Application Timeline</h2>

                  <p>
                    Application history.
                  </p>
                </div>

              </div>


              <div className="timeline">

                <div className="timeline-item">

                  <div className="timeline-icon">
                    <PlusIcon />
                  </div>

                  <div>
                    <span>
                      Created
                    </span>

                    <strong>
                      {formatDate(
                        application.created_at
                      )}
                    </strong>
                  </div>

                </div>


                <div className="timeline-item">

                  <div className="timeline-icon">
                    <Clock size={14} />
                  </div>

                  <div>
                    <span>
                      Last Updated
                    </span>

                    <strong>
                      {formatDate(
                        application.updated_at
                      )}
                    </strong>
                  </div>

                </div>

              </div>

            </section>


            {/* Quick Links */}

            <section className="details-panel">

              <div className="panel-heading">

                <div className="panel-heading-icon purple">
                  <Brain size={18} />
                </div>

                <div>
                  <h2>AI Tools</h2>

                  <p>
                    Incident investigation tools.
                  </p>
                </div>

              </div>


              <div className="tool-links">

                <Link to="/hindsight">
                  <Brain size={16} />

                  <div>
                    <strong>
                      Hindsight Memory
                    </strong>

                    <span>
                      Search previous incidents
                    </span>
                  </div>

                  <ChevronRight size={15} />
                </Link>


                <Link to="/activity">
                  <Activity size={16} />

                  <div>
                    <strong>
                      Activity
                    </strong>

                    <span>
                      View recent activity
                    </span>
                  </div>

                  <ChevronRight size={15} />
                </Link>

              </div>

            </section>


            {/* Security */}

            <div className="security-card">

              <ShieldCheck size={19} />

              <div>

                <strong>
                  User Access Protected
                </strong>

                <p>
                  This application is visible only to
                  your authenticated account.
                </p>

              </div>

            </div>

          </aside>

        </div>

      </main>

    </div>
  );
}


/* Small icon component */

function PlusIcon() {
  return <span className="timeline-plus">+</span>;
}

export default ApplicationDetails;