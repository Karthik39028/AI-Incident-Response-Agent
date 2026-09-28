import { useEffect, useState } from "react";
import { Link } from "react-router-dom";

import {
  Activity,
  AppWindow,
  ArrowLeft,
  ChevronRight,
  Plus,
  RefreshCw,
  Server,
  ShieldCheck,
  GitBranch,
  Globe,
  Layers3,
} from "lucide-react";

import "./Applications.css";

const API_URL = "http://localhost:8081";

function Applications() {
  const [applications, setApplications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadApplications();
  }, []);

  const loadApplications = async () => {
    try {
      setLoading(true);
      setError("");

      const response = await fetch(
        `${API_URL}/api/applications`,
        {
          credentials: "include",
        }
      );

      if (!response.ok) {
        throw new Error("Failed to load applications");
      }

      const data = await response.json();

      setApplications(data.applications || []);

    } catch (err) {
      console.error(err);

      setError(
        "Unable to load applications. Make sure the backend is running."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="applications-page">

      {/* ================= HEADER ================= */}

      <header className="applications-header">

        <div className="applications-header-left">

          <Link
            to="/dashboard"
            className="back-button"
          >
            <ArrowLeft size={18} />
          </Link>

          <div>

            <div className="page-title-row">

              <div className="page-title-icon">
                <AppWindow size={21} />
              </div>

              <h1>Applications</h1>

            </div>

            <p>
              Manage the applications monitored by
              IncidentAI.
            </p>

          </div>

        </div>


        <div className="header-actions">

          <button
            className="refresh-button"
            onClick={loadApplications}
            disabled={loading}
          >
            <RefreshCw
              size={16}
              className={loading ? "spinning" : ""}
            />

            Refresh
          </button>

          <Link
            to="/applications/new"
            className="add-application-button"
          >
            <Plus size={17} />
            Add Application
          </Link>

        </div>

      </header>


      {/* ================= CONTENT ================= */}

      <main className="applications-content">

        {/* Stats */}

        <div className="application-stats">

          <div className="application-stat">

            <div className="application-stat-icon blue">
              <Layers3 size={20} />
            </div>

            <div>
              <span>Total</span>
              <strong>{applications.length}</strong>
            </div>

          </div>


          <div className="application-stat">

            <div className="application-stat-icon green">
              <Activity size={20} />
            </div>

            <div>
              <span>Active</span>

              <strong>
                {
                  applications.filter(
                    (app) => app.status === "active"
                  ).length
                }
              </strong>

            </div>

          </div>


          <div className="application-stat">

            <div className="application-stat-icon purple">
              <Server size={20} />
            </div>

            <div>
              <span>Monitored</span>

              <strong>
                {applications.length}
              </strong>

            </div>

          </div>

        </div>


        {/* Error */}

        {error && (

          <div className="applications-error">
            {error}
          </div>

        )}


        {/* Loading */}

        {loading ? (

          <div className="applications-loading">

            <div className="applications-spinner"></div>

            <p>
              Loading applications...
            </p>

          </div>

        ) : applications.length === 0 ? (

          /* ================= EMPTY STATE ================= */

          <div className="applications-empty">

            <div className="empty-application-icon">
              <AppWindow size={30} />
            </div>

            <h2>
              No applications connected
            </h2>

            <p>
              Connect your first application to start
              monitoring incidents and analyzing failures
              with AI.
            </p>

            <Link
              to="/applications/new"
              className="empty-add-button"
            >
              <Plus size={18} />
              Add Your First Application
            </Link>

          </div>

        ) : (

          /* ================= APPLICATION LIST ================= */

          <div className="applications-list">

            {applications.map((app) => (

              <Link
                key={app.id}
                to={`/applications/${app.id}`}
                className="application-card"
              >

                <div className="application-card-main">

                  <div className="application-main-icon">
                    <Server size={22} />
                  </div>

                  <div className="application-info">

                    <div className="application-name-row">

                      <h2>
                        {app.name}
                      </h2>

                      <span
                        className={`application-status ${
                          app.status === "active"
                            ? "active"
                            : "inactive"
                        }`}
                      >
                        <span></span>

                        {app.status || "active"}
                      </span>

                    </div>

                    <p className="application-description">
                      {app.description ||
                        "No description provided."}
                    </p>


                    <div className="application-meta">

                      {app.runtime_type && (

                        <span>
                          <Globe size={14} />
                          {app.runtime_type}
                        </span>

                      )}

                      {app.deployment_type && (

                        <span>
                          <Layers3 size={14} />
                          {app.deployment_type}
                        </span>

                      )}

                      {app.source_type && (

                        <span>
                          <GitBranch  size={14} />
                          {app.source_type}
                        </span>

                      )}

                    </div>

                  </div>

                </div>


                <div className="application-card-arrow">

                  <ChevronRight size={20} />

                </div>

              </Link>

            ))}

          </div>

        )}

      </main>

    </div>
  );
}

export default Applications;