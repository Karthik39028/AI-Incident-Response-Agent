import { Link } from "react-router-dom";

import {
  Activity as ActivityIcon,
  AlertTriangle,
  ArrowLeft,
  Brain,
  CheckCircle2,
  Clock3,
  Database,
  GitBranch,
  Plus,
  Search,
  Server,
  Sparkles,
  User,
} from "lucide-react";

import "./Activity.css";

function Activity() {
  const activities = [
    {
      type: "ai",
      icon: Brain,
      title: "AI Incident Analysis",
      description:
        "Incident analysis was performed using current telemetry and historical Hindsight experience.",
      time: "Available through Incident Analysis",
    },

    {
      type: "memory",
      icon: Database,
      title: "Hindsight Memory",
      description:
        "Historical incident experience can be searched using the Hindsight memory service.",
      time: "Available through Hindsight",
    },

    {
      type: "incident",
      icon: AlertTriangle,
      title: "Incident Investigation",
      description:
        "Production telemetry can be submitted for AI-powered incident investigation.",
      time: "Available through Incident Analysis",
    },

    {
      type: "application",
      icon: Server,
      title: "Application Monitoring",
      description:
        "Connected applications are available for incident analysis.",
      time: "Application service",
    },

    {
      type: "github",
      icon: GitBranch,
      title: "GitHub Authentication",
      description:
        "GitHub authentication provides access to the IncidentAI dashboard.",
      time: "Authentication service",
    },
  ];

  return (
    <div className="activity-page">

      {/* ================= HEADER ================= */}

      <header className="activity-header">

        <div className="activity-header-left">

          <Link
            to="/dashboard"
            className="activity-back"
          >
            <ArrowLeft size={18} />
          </Link>

          <div>

            <div className="activity-title-row">

              <div className="activity-title-icon">
                <ActivityIcon size={20} />
              </div>

              <h1>
                Activity
              </h1>

            </div>

            <p>
              IncidentAI system activity and available
              operations.
            </p>

          </div>

        </div>

      </header>


      <main className="activity-content">

        {/* ================= SUMMARY ================= */}

        <section className="activity-summary">

          <div className="summary-card">

            <div className="summary-icon blue">
              <ActivityIcon size={20} />
            </div>

            <div>

              <span>
                Activity Tracking
              </span>

              <strong>
                Ready
              </strong>

            </div>

          </div>


          <div className="summary-card">

            <div className="summary-icon purple">
              <Brain size={20} />
            </div>

            <div>

              <span>
                AI Analysis
              </span>

              <strong>
                Available
              </strong>

            </div>

          </div>


          <div className="summary-card">

            <div className="summary-icon green">
              <Database size={20} />
            </div>

            <div>

              <span>
                Hindsight
              </span>

              <strong>
                Connected
              </strong>

            </div>

          </div>


          <div className="summary-card">

            <div className="summary-icon orange">
              <Server size={20} />
            </div>

            <div>

              <span>
                Applications
              </span>

              <strong>
                Monitoring
              </strong>

            </div>

          </div>

        </section>


        {/* ================= INFO ================= */}

        <section className="activity-info">

          <div className="activity-info-icon">
            <Clock3 size={20} />
          </div>

          <div>

            <span>
              ACTIVITY CENTER
            </span>

            <h2>
              Understand what IncidentAI can track
            </h2>

            <p>
              This page provides a central place for
              system activity. Detailed persistent
              activity history requires an activity
              endpoint and database table in the backend.
            </p>

          </div>

        </section>


        {/* ================= ACTIVITY LIST ================= */}

        <section className="activity-panel">

          <div className="activity-panel-header">

            <div>

              <span>
                AVAILABLE OPERATIONS
              </span>

              <h2>
                IncidentAI Activity
              </h2>

            </div>

            <div className="activity-status">

              <span></span>

              System Ready

            </div>

          </div>


          <div className="activity-list">

            {activities.map(
              (activity, index) => {

                const Icon = activity.icon;

                return (
                  <div
                    className="activity-item"
                    key={index}
                  >

                    <div
                      className={`activity-item-icon ${activity.type}`}
                    >
                      <Icon size={17} />
                    </div>


                    <div className="activity-item-content">

                      <div className="activity-item-title">

                        <h3>
                          {activity.title}
                        </h3>

                        <span>
                          {activity.time}
                        </span>

                      </div>

                      <p>
                        {activity.description}
                      </p>

                    </div>

                  </div>
                );
              }
            )}

          </div>

        </section>


        {/* ================= QUICK ACTIONS ================= */}

        <section className="quick-actions">

          <div className="quick-actions-header">

            <div className="quick-actions-icon">
              <Sparkles size={18} />
            </div>

            <div>

              <h2>
                Quick Actions
              </h2>

              <p>
                Jump directly to the main IncidentAI
                workflows.
              </p>

            </div>

          </div>


          <div className="quick-action-grid">

            <Link
              to="/applications"
              className="quick-action"
            >

              <Server size={17} />

              <div>

                <strong>
                  Applications
                </strong>

                <span>
                  View connected applications
                </span>

              </div>

            </Link>


            <Link
              to="/hindsight"
              className="quick-action"
            >

              <Brain size={17} />

              <div>

                <strong>
                  Hindsight
                </strong>

                <span>
                  Search historical incidents
                </span>

              </div>

            </Link>


            <Link
              to="/applications/new"
              className="quick-action"
            >

              <Plus size={17} />

              <div>

                <strong>
                  Add Application
                </strong>

                <span>
                  Connect a new application
                </span>

              </div>

            </Link>


            <Link
              to="/dashboard"
              className="quick-action"
            >

              <ActivityIcon size={17} />

              <div>

                <strong>
                  Dashboard
                </strong>

                <span>
                  Return to overview
                </span>

              </div>

            </Link>

          </div>

        </section>


        {/* ================= FUTURE ACTIVITY ================= */}

        <section className="future-activity">

          <div className="future-icon">
            <Clock3 size={18} />
          </div>

          <div>

            <h3>
              Persistent activity history
            </h3>

            <p>
              The current backend does not expose an
              activity API yet. Once we add one, this
              section can show real events such as
              application creation, incident analyses,
              Hindsight searches, and GitHub login
              events with timestamps.
            </p>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Activity;