import { useState } from "react";
import { Link } from "react-router-dom";

import {
  ArrowLeft,
  Brain,
  CheckCircle2,
  Clock,
  Database,
  Search,
  Sparkles,
  Upload,
  AlertTriangle,
  ChevronRight,
  History,
} from "lucide-react";

import "./Hindsight.css";

const API_URL = "http://localhost:8081";

function Hindsight() {
  const [query, setQuery] = useState("");

  const [results, setResults] = useState(null);

  const [searching, setSearching] =
    useState(false);

  const [seeding, setSeeding] =
    useState(false);

  const [message, setMessage] = useState("");

  const [error, setError] = useState("");

  const searchMemory = async () => {
    if (!query.trim()) {
      setError("Enter a search query first.");
      return;
    }

    try {
      setSearching(true);
      setError("");
      setMessage("");

      const response = await fetch(
        `${API_URL}/api/memory/search?query=${encodeURIComponent(
          query
        )}`
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to search Hindsight."
        );
      }

      setResults(data);

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to search Hindsight."
      );
    } finally {
      setSearching(false);
    }
  };

  const seedMemory = async () => {
    try {
      setSeeding(true);
      setError("");
      setMessage("");

      const response = await fetch(
        `${API_URL}/api/memory/seed`,
        {
          method: "POST",
        }
      );

      const data = await response.json();

      if (!response.ok) {
        throw new Error(
          data.detail ||
            "Unable to seed memory."
        );
      }

      setMessage(
        "Historical incident successfully added to Hindsight."
      );

    } catch (err) {
      console.error(err);

      setError(
        err.message ||
          "Unable to seed Hindsight memory."
      );
    } finally {
      setSeeding(false);
    }
  };

  return (
    <div className="hindsight-page">

      {/* ================= HEADER ================= */}

      <header className="hindsight-header">

        <div className="hindsight-header-left">

          <Link
            to="/dashboard"
            className="hindsight-back"
          >
            <ArrowLeft size={18} />
          </Link>

          <div>

            <div className="hindsight-title-row">

              <div className="hindsight-title-icon">
                <Brain size={20} />
              </div>

              <h1>
                Hindsight Memory
              </h1>

            </div>

            <p>
              Search historical incident experience
              stored by IncidentAI.
            </p>

          </div>

        </div>


        <button
          className="seed-button"
          onClick={seedMemory}
          disabled={seeding}
        >

          {seeding ? (
            <>
              <span className="small-spinner"></span>
              Seeding...
            </>
          ) : (
            <>
              <Upload size={16} />
              Seed Example Incident
            </>
          )}

        </button>

      </header>


      <main className="hindsight-content">

        {/* ================= INFO ================= */}

        <section className="memory-info">

          <div className="memory-info-icon">
            <Sparkles size={21} />
          </div>

          <div>

            <span>
              ORGANIZATIONAL MEMORY
            </span>

            <h2>
              Learn from previous incidents
            </h2>

            <p>
              Hindsight stores previous incident
              experiences and retrieves relevant
              information when a new incident occurs.
            </p>

          </div>

        </section>


        {/* ================= SEARCH ================= */}

        <section className="memory-search-panel">

          <div className="section-heading">

            <div className="section-heading-icon">
              <Search size={18} />
            </div>

            <div>

              <h2>
                Search Incident Memory
              </h2>

              <p>
                Ask Hindsight about previous incidents,
                symptoms, root causes, or remediation.
              </p>

            </div>

          </div>


          <div className="search-box">

            <Search size={17} />

            <input
              type="text"
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  searchMemory();
                }
              }}
              placeholder="e.g. database connection pool exhaustion"
            />

            <button
              onClick={searchMemory}
              disabled={searching}
            >

              {searching ? (
                <span className="small-spinner"></span>
              ) : (
                <>
                  Search
                  <ChevronRight size={15} />
                </>
              )}

            </button>

          </div>


          <div className="example-queries">

            <span>
              Try:
            </span>

            <button
              onClick={() =>
                setQuery(
                  "high latency database connection pool"
                )
              }
            >
              High latency + database connections
            </button>

            <button
              onClick={() =>
                setQuery(
                  "payment service error rate"
                )
              }
            >
              Payment service errors
            </button>

            <button
              onClick={() =>
                setQuery(
                  "connection pool exhaustion"
                )
              }
            >
              Connection pool exhaustion
            </button>

          </div>

        </section>


        {/* ================= MESSAGES ================= */}

        {error && (

          <div className="memory-error">

            <AlertTriangle size={17} />

            {error}

          </div>

        )}

        {message && (

          <div className="memory-success">

            <CheckCircle2 size={17} />

            {message}

          </div>

        )}


        {/* ================= RESULTS ================= */}

        {results && (

          <section className="memory-results">

            <div className="results-heading">

              <div>

                <span>
                  SEARCH RESULTS
                </span>

                <h2>
                  Historical Experience
                </h2>

              </div>

              <div className="query-badge">

                <Search size={13} />

                {query}

              </div>

            </div>


            <MemoryResult data={results} />

          </section>

        )}


        {/* ================= EMPTY ================= */}

        {!results && !searching && (

          <section className="memory-empty">

            <div className="memory-empty-icon">
              <History size={28} />
            </div>

            <h2>
              No search performed yet
            </h2>

            <p>
              Search for a previous incident to see
              what IncidentAI remembers.
            </p>

          </section>

        )}

      </main>

    </div>
  );
}


/* ================= RESULT COMPONENT ================= */

function MemoryResult({ data }) {

  /*
   * Hindsight's response can vary depending on
   * the API response. We therefore display the
   * returned object safely instead of assuming
   * an undocumented response shape.
   */

  const items =
    data?.results ||
    data?.memories ||
    data?.items ||
    data?.data ||
    [];

  if (Array.isArray(items) && items.length > 0) {

    return (
      <div className="memory-result-list">

        {items.map((item, index) => (

          <div
            className="memory-result-card"
            key={index}
          >

            <div className="memory-result-number">
              {index + 1}
            </div>

            <div className="memory-result-content">

              <div className="memory-result-top">

                <span>
                  HISTORICAL EXPERIENCE
                </span>

                <Database size={14} />

              </div>

              <p>
                {typeof item === "string"
                  ? item
                  : item.content ||
                    item.text ||
                    item.memory ||
                    JSON.stringify(item)}
              </p>

            </div>

          </div>

        ))}

      </div>
    );
  }

  /*
   * If Hindsight returns an object that doesn't
   * match the expected list shape, show the actual
   * response rather than hiding it.
   */

  return (
    <div className="raw-memory-result">

      <div className="raw-result-header">

        <Database size={17} />

        <span>
          Hindsight Response
        </span>

      </div>

      <pre>
        {JSON.stringify(
          data,
          null,
          2
        )}
      </pre>

    </div>
  );
}

export default Hindsight;