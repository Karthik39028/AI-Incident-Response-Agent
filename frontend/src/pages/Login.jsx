import { useEffect, useState } from "react";
import { ShieldCheck, BrainCircuit, Activity } from "lucide-react";
import { useNavigate } from "react-router-dom";
import "./Login.css";

function Login() {
  const navigate = useNavigate();

  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const checkAuthentication = async () => {
      try {
        const response = await fetch(
          "http://localhost:8081/api/auth/github/me",
          {
            method: "GET",
            credentials: "include",
          }
        );

        if (response.ok) {
          const data = await response.json();

          if (data.authenticated) {
            navigate("/dashboard", {
              replace: true,
            });

            return;
          }
        }
      } catch (error) {
        console.error("Authentication check failed:", error);
      }

      setChecking(false);
    };

    checkAuthentication();
  }, [navigate]);

  const handleGithubLogin = () => {
    window.location.href =
      "http://localhost:8081/api/auth/github/login";
  };

  /* Loading screen */
  if (checking) {
    return (
      <div className="login-loading-page">
        <div className="login-loading-content">
          <div className="login-spinner"></div>

          <p className="login-loading-text">
            Checking authentication...
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="login-page">

      {/* Background effects */}
      <div className="login-background">
        <div className="login-blue-glow"></div>
        <div className="login-purple-glow"></div>
      </div>

      <div className="login-container">

        {/* Logo */}
        <div className="login-logo-wrapper">
          <div className="login-logo">
            <Activity />
          </div>
        </div>

        {/* Heading */}
        <div className="login-heading">
          <h1>AI SRE Agent</h1>

          <p>
            Real-time incident response
            <br />
            powered by persistent AI memory
          </p>
        </div>

        {/* Login card */}
        <div className="login-card">

          {/* Card heading */}
          <div className="login-card-header">

            <div className="login-card-title">
              <ShieldCheck />

              <h2>Secure sign in</h2>
            </div>

            <p>
              Connect your GitHub account to manage
              applications and incident response.
            </p>

          </div>

          {/* GitHub button */}
          <button
            onClick={handleGithubLogin}
            className="github-login-button"
          >
            <span className="github-icon">
              GH
            </span>

            <span>
              Continue with GitHub
            </span>
          </button>

          {/* Features */}
          <div className="login-features">

            <div className="login-feature">

              <Activity className="feature-blue" />

              <div>
                <p className="feature-title">
                  Real-time monitoring
                </p>

                <p className="feature-description">
                  Detect incidents quickly
                </p>
              </div>

            </div>

            <div className="login-feature">

              <BrainCircuit className="feature-purple" />

              <div>
                <p className="feature-title">
                  Hindsight memory
                </p>

                <p className="feature-description">
                  Learn from past incidents
                </p>
              </div>

            </div>

          </div>

        </div>

        {/* Footer */}
        <p className="login-footer">
          AI Incident Response & Learning Agent
        </p>

      </div>

    </div>
  );
}

export default Login;