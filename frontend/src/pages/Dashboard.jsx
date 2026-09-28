import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  Activity,
  AlertTriangle,
  AppWindow,
  Brain,
  ChevronRight,
  Clock,
  GitBranch,
  LogOut,
  Plus,
  Server,
  ShieldCheck,
  Zap,
} from "lucide-react";

import "./Dashboard.css";

const API_URL = "http://localhost:8081";

function Dashboard() {
  const navigate = useNavigate();

  const [user, setUser] = useState(null);
  const [applications, setApplications] = useState([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError("");

      // Get logged-in GitHub user
      const userResponse = await fetch(
        `${API_URL}/api/auth/github/me`,
        {
          credentials: "include",
        }
      );

      if (!userResponse.ok) {
        navigate("/login");
        return;
      }

      const userData = await userResponse.json();

      if (!userData.authenticated) {
        navigate("/login");
        return;
      }

      setUser(userData.user);

      // Get applications
      const applicationsResponse = await fetch(
        `${API_URL}/api/applications`,
        {
          credentials: "include",
        }
      );

      if (applicationsResponse.ok) {
        const applicationsData =
          await applicationsResponse.json();

        setApplications(
          applicationsData.applications || []
        );
      }

    } catch (err) {
      console.error(err);
      setError(
        "Unable to connect to the backend."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    try {
      await fetch(
        `${API_URL}/api/auth/github/logout`,
        {
          method: "POST",
          credentials: "include",
        }
      );
    } catch (err) {
      console.error(err);
    }

    navigate("/login");
  };

  const activeApplications = applications.filter(
    (app) => app.status === "active"
  );

  const healthyApplications = applications.filter(
    (app) =>
      app.status === "healthy" ||
      app.status === "active"
  );

  if (loading) {
    return (
      <div className="dashboard-loading">
        <div className="loading-spinner"></div>
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard-layout">

      {/* ================= SIDEBAR ================= */}

      <aside className="sidebar">

        <div className="sidebar-logo">

          <div className="sidebar-logo-icon">
            <ShieldCheck size={23} />
          </div>

          <div>
            <h2>IncidentAI</h2>
            <span>Response Agent</span>
          </div>

        </div>

        <nav className="sidebar-nav">

          <Link
            to="/dashboard"
            className="nav-item active"
          >
            <Activity size={19} />
            Dashboard
          </Link>

          <Link
            to="/applications"
            className="nav-item"
          >
            <AppWindow size={19} />
            Applications
          </Link>

          <Link
            to="/hindsight"
            className="nav-item"
          >
            <Brain size={19} />
            Hindsight
          </Link>

          <Link
            to="/activity"
            className="nav-item"
          >
            <Clock size={19} />
            Activity
          </Link>

        </nav>

        <div className="sidebar-bottom">

          <div className="sidebar-status">

            <span className="status-dot"></span>

            <div>
              <strong>System Online</strong>
              <small>All services operational</small>
            </div>

          </div>

          <button
            className="logout-button"
            onClick={handleLogout}
          >
            <LogOut size={18} />
            Logout
          </button>

        </div>

      </aside>


      {/* ================= MAIN ================= */}

      <main className="dashboard-main">

        {/* HEADER */}

        <header className="dashboard-header">

          <div>

            <p className="page-label">
              OVERVIEW
            </p>

            <h1>
              Good to see you
              {user?.name
                ? `, ${user.name.split(" ")[0]}`
                : ""}
              .
            </h1>

            <p className="header-description">
              Monitor your applications and analyze
              production incidents with AI.
            </p>

          </div>


          <div className="header-user">

            {user?.avatar_url ? (
              <img
                src={user.avatar_url}
                alt="GitHub avatar"
              />
            ) : (
              <div className="avatar-placeholder">
                <Github size={20} />
              </div>
            )}

            <div className="user-details">
              <strong>
                {user?.name || user?.login}
              </strong>

              <span>
                @{user?.login}
              </span>
            </div>

          </div>

        </header>


        {/* ERROR */}

        {error && (
          <div className="error-banner">
            <AlertTriangle size={18} />
            {error}
          </div>
        )}


        {/* ================= STATS ================= */}

        <section className="stats-grid">

          <div className="stat-card">

            <div className="stat-icon blue">
              <AppWindow size={22} />
            </div>

            <div className="stat-info">

              <span>Total Applications</span>

              <strong>
                {applications.length}
              </strong>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon green">
              <Server size={22} />
            </div>

            <div className="stat-info">

              <span>Active Applications</span>

              <strong>
                {activeApplications.length}
              </strong>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon purple">
              <Brain size={22} />
            </div>

            <div className="stat-info">

              <span>AI Analysis</span>

              <strong>Ready</strong>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon orange">
              <AlertTriangle size={22} />
            </div>

            <div className="stat-info">

              <span>Incidents</span>

              <strong>0</strong>

            </div>

          </div>

        </section>


        {/* ================= QUICK ACTIONS ================= */}

        <section className="quick-section">

          <div className="section-heading">

            <div>
              <h2>Quick Actions</h2>

              <p>
                Manage your applications and investigate
                incidents.
              </p>
            </div>

          </div>


          <div className="quick-grid">

            <Link
              to="/applications/new"
              className="quick-card"
            >

              <div className="quick-icon blue-bg">
                <Plus size={22} />
              </div>

              <div>
                <h3>Add Application</h3>

                <p>
                  Connect a new application to monitor.
                </p>
              </div>

              <ChevronRight size={18} />

            </Link>


            <Link
              to="/applications"
              className="quick-card"
            >

              <div className="quick-icon purple-bg">
                <AppWindow size={22} />
              </div>

              <div>
                <h3>View Applications</h3>

                <p>
                  Manage your connected applications.
                </p>
              </div>

              <ChevronRight size={18} />

            </Link>


            <Link
              to="/hindsight"
              className="quick-card"
            >

              <div className="quick-icon green-bg">
                <Brain size={22} />
              </div>

              <div>
                <h3>Search Memory</h3>

                <p>
                  Find similar historical incidents.
                </p>
              </div>

              <ChevronRight size={18} />

            </Link>

          </div>

        </section>


        {/* ================= APPLICATIONS ================= */}

        <section className="applications-section">

          <div className="section-heading">

            <div>
              <h2>Recent Applications</h2>

              <p>
                Applications connected to IncidentAI.
              </p>
            </div>

            <Link
              to="/applications"
              className="view-all"
            >
              View all
              <ChevronRight size={16} />
            </Link>

          </div>


          {applications.length === 0 ? (

            <div className="empty-state">

              <div className="empty-icon">
                <AppWindow size={28} />
              </div>

              <h3>
                No applications yet
              </h3>

              <p>
                Add your first application to start
                monitoring incidents.
              </p>

              <Link
                to="/applications/new"
                className="primary-button"
              >
                <Plus size={18} />
                Add Application
              </Link>

            </div>

          ) : (

            <div className="application-list">

              {applications
                .slice(0, 5)
                .map((app) => (

                  <Link
                    key={app.id}
                    to={`/applications/${app.id}`}
                    className="application-row"
                  >

                    <div className="application-left">

                      <div className="application-icon">
                        <Server size={20} />
                      </div>

                      <div>

                        <h3>
                          {app.name}
                        </h3>

                        <p>
                          {app.runtime_type ||
                            "Application"}

                          {app.deployment_type
                            ? ` • ${app.deployment_type}`
                            : ""}
                        </p>

                      </div>

                    </div>


                    <div className="application-right">

                      <span className="app-status">

                        <span className="status-dot"></span>

                        {app.status || "active"}

                      </span>

                      <ChevronRight size={18} />

                    </div>

                  </Link>

                ))}

            </div>

          )}

        </section>


        {/* ================= AI BANNER ================= */}

        <section className="ai-banner">

          <div className="ai-banner-icon">
            <Zap size={25} />
          </div>

          <div>

            <h2>
              AI Incident Response
            </h2>

            <p>
              When an incident occurs, IncidentAI
              analyzes telemetry, recalls historical
              incidents and generates an evidence-based
              diagnosis.
            </p>

          </div>

          <Link
            to="/applications"
            className="ai-banner-button"
          >
            Get Started
            <ChevronRight size={17} />
          </Link>

        </section>

      </main>

    </div>
  );
}

export default Dashboard;