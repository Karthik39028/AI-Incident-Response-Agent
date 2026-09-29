import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import {
  ArrowLeft,
  AppWindow,
 GitBranch,
  Globe,
  Layers3,
  Plus,
  Server,
  ShieldCheck,
} from "lucide-react";

import "./AddApplication.css";

const API_URL = "http://localhost:8081";

function AddApplication() {
  const navigate = useNavigate();

  const [form, setForm] = useState({
    name: "",
    description: "",
    runtime_type: "",
    runtime_url: "",
    source_type: "",
    source_url: "",
    deployment_type: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [repositories, setRepositories] = useState([]);
  const [repositoriesLoading, setRepositoriesLoading] = useState(true);
  const [repositoryError, setRepositoryError] = useState("");

  useEffect(() => {
    const loadRepositories = async () => {
      try {
        setRepositoriesLoading(true);
        setRepositoryError("");

        const response = await fetch(
          `${API_URL}/api/auth/github/repositories`,
          {
            method: "GET",
            credentials: "include",
          }
        );

        const data = await response.json();

        if (!response.ok) {
          throw new Error(
            data.detail || "Failed to load GitHub repositories."
          );
        }

        setRepositories(data.repositories || []);

        // Since this page is now connected to GitHub repositories,
        // default the source type to GitHub.
        setForm((previous) => ({
          ...previous,
          source_type: "GitHub",
        }));
      } catch (err) {
        console.error("Repository loading error:", err);
        setRepositoryError(
          err.message || "Unable to load GitHub repositories."
        );
      } finally {
        setRepositoriesLoading(false);
      }
    };

    loadRepositories();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");

    if (!form.name.trim()) {
      setError("Application name is required.");
      return;
    }

    try {
      setLoading(true);

      const response = await fetch(
        `${API_URL}/api/applications`,
        {
          method: "POST",
          credentials: "include",

          headers: {
            "Content-Type": "application/json",
          },

          body: JSON.stringify(form),
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail || "Failed to create application."
        );
      }

      // Backend returns the created application.
      // Go directly to its details page.
      if (data.application_id) {
        navigate(
          `/applications/${data.application_id}`
        );
      } else {
        navigate("/applications");
      }

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Something went wrong while creating the application."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="add-application-page">

      {/* ================= HEADER ================= */}

      <header className="add-application-header">

        <div className="add-header-left">

          <Link
            to="/applications"
            className="add-back-button"
          >
            <ArrowLeft size={18} />
          </Link>

          <div>

            <div className="add-title-row">

              <div className="add-title-icon">
                <Plus size={20} />
              </div>

              <h1>Add Application</h1>

            </div>

            <p>
              Connect an application to IncidentAI.
            </p>

          </div>

        </div>

      </header>


      {/* ================= FORM ================= */}

      <main className="add-application-content">

        <form
          className="application-form"
          onSubmit={handleSubmit}
        >

          {/* BASIC INFORMATION */}

          <section className="form-section">

            <div className="form-section-header">

              <div className="form-section-icon">
                <AppWindow size={19} />
              </div>

              <div>
                <h2>Application Information</h2>

                <p>
                  Basic information about the application
                  you want to monitor.
                </p>
              </div>

            </div>


            <div className="form-field">

              <label>
                Application Name
                <span>*</span>
              </label>

              <input
                type="text"
                name="name"
                value={form.name}
                onChange={handleChange}
                placeholder="e.g. Payment Service"
                required
              />

            </div>


            <div className="form-field">

              <label>
                Description
              </label>

              <textarea
                name="description"
                value={form.description}
                onChange={handleChange}
                placeholder="Describe what this application does..."
                rows={4}
              />

            </div>

          </section>


          {/* RUNTIME */}

          <section className="form-section">

            <div className="form-section-header">

              <div className="form-section-icon blue">
                <Server size={19} />
              </div>

              <div>
                <h2>Runtime</h2>

                <p>
                  Tell IncidentAI where and how the
                  application runs.
                </p>
              </div>

            </div>


            <div className="form-grid">

              <div className="form-field">

                <label>
                  Runtime Type
                </label>

                <select
                  name="runtime_type"
                  value={form.runtime_type}
                  onChange={handleChange}
                >

                  <option value="">
                    Select runtime
                  </option>

                  <option value="Node.js">
                    Node.js
                  </option>

                  <option value="Python">
                    Python
                  </option>

                  <option value="Java">
                    Java
                  </option>

                  <option value="Go">
                    Go
                  </option>

                  <option value="React">
                    React
                  </option>

                  <option value="Other">
                    Other
                  </option>

                </select>

              </div>


              <div className="form-field">

                <label>
                  Runtime URL
                </label>

                <div className="input-with-icon">

                  <Globe size={16} />

                  <input
                    type="url"
                    name="runtime_url"
                    value={form.runtime_url}
                    onChange={handleChange}
                    placeholder="https://api.example.com"
                  />

                </div>

              </div>

            </div>

          </section>


          {/* SOURCE */}

          <section className="form-section">

            <div className="form-section-header">

              <div className="form-section-icon purple">
                <GitBranch size={19} />
              </div>

              <div>
                <h2>Source Code</h2>

                <p>
                  Connect the source repository for this
                  application.
                </p>
              </div>

            </div>


            <div className="form-grid">

              <div className="form-field">

                <label>
                  Source Type
                </label>

                <select
                  name="source_type"
                  value={form.source_type}
                  onChange={handleChange}
                >
                  <option value="">
                    Select source
                  </option>

                  <option value="GitHub">
                    GitHub
                  </option>

                  <option value="GitLab">
                    GitLab
                  </option>

                  <option value="Bitbucket">
                    Bitbucket
                  </option>

                  <option value="Other">
                    Other
                  </option>
                </select>

              </div>


              <div className="form-field">

                <label>
                  GitHub Repository
                </label>

                <div className="input-with-icon">
                  <GitBranch size={16} />

                  <select
                    value={form.source_url}
                    onChange={(e) => {
                      const selectedUrl = e.target.value;
                      const selectedRepository = repositories.find(
                        (repo) => repo.url === selectedUrl
                      );

                      setForm((previous) => ({
                        ...previous,
                        source_type: "GitHub",
                        source_url: selectedUrl,
                        name:
                          previous.name ||
                          selectedRepository?.name ||
                          "",
                        description:
                          previous.description ||
                          selectedRepository?.description ||
                          "",
                      }));
                    }}
                    disabled={repositoriesLoading || !!repositoryError}
                  >
                    <option value="">
                      {repositoriesLoading
                        ? "Loading GitHub repositories..."
                        : "Select a repository"}
                    </option>

                    {repositories.map((repo) => (
                      <option key={repo.id} value={repo.url}>
                        {repo.fullName}
                      </option>
                    ))}
                  </select>
                </div>

                {repositoryError && (
                  <div className="form-error">
                    {repositoryError}
                  </div>
                )}

                {form.source_url && (
                  <small style={{ marginTop: "8px", display: "block" }}>
                    {form.source_url}
                  </small>
                )}

              </div>

            </div>

          </section>


          {/* DEPLOYMENT */}

          <section className="form-section">

            <div className="form-section-header">

              <div className="form-section-icon green">
                <Layers3 size={19} />
              </div>

              <div>
                <h2>Deployment</h2>

                <p>
                  Specify where this application is
                  deployed.
                </p>
              </div>

            </div>


            <div className="form-field">

              <label>
                Deployment Type
              </label>

              <select
                name="deployment_type"
                value={form.deployment_type}
                onChange={handleChange}
              >

                <option value="">
                  Select deployment
                </option>

                <option value="AWS">
                  AWS
                </option>

                <option value="Azure">
                  Azure
                </option>

                <option value="Google Cloud">
                  Google Cloud
                </option>

                <option value="Vercel">
                  Vercel
                </option>

                <option value="Netlify">
                  Netlify
                </option>

                <option value="Docker">
                  Docker
                </option>

                <option value="Kubernetes">
                  Kubernetes
                </option>

                <option value="On-Premise">
                  On-Premise
                </option>

                <option value="Other">
                  Other
                </option>

              </select>

            </div>

          </section>


          {/* ERROR */}

          {error && (

            <div className="form-error">
              {error}
            </div>

          )}


          {/* ACTIONS */}

          <div className="form-actions">

            <Link
              to="/applications"
              className="cancel-button"
            >
              Cancel
            </Link>

            <button
              type="submit"
              className="create-button"
              disabled={loading}
            >

              {loading ? (
                <>
                  <span className="button-spinner"></span>
                  Creating...
                </>
              ) : (
                <>
                  <ShieldCheck size={17} />
                  Create Application
                </>
              )}

            </button>

          </div>

        </form>

      </main>

    </div>
  );
}

export default AddApplication;