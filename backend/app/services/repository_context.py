import os
import re

from app.services.repository import (
    get_repository_tree,
    get_repository_file,
)


MAX_FILES_TO_ANALYZE = 15
MAX_FILE_CONTENT_LENGTH = 30_000


# ============================================================
# FILE CLASSIFICATION
# ============================================================

SOURCE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".java",
    ".kt",
    ".go",
    ".rs",
    ".php",
    ".rb",
    ".cs",
    ".cpp",
    ".c",
    ".h",
}

CONFIG_EXTENSIONS = {
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".conf",
    ".xml",
    ".properties",
}

INFRASTRUCTURE_FILES = {
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "netlify.toml",
    "vercel.json",
    "render.yaml",
    "fly.toml",
    "Procfile",
    "nginx.conf",
}

IMPORTANT_FILES = {
    "package.json",
    "requirements.txt",
    "pyproject.toml",
    "pom.xml",
    "build.gradle",
    "build.gradle.kts",
    "go.mod",
    "cargo.toml",
    "dockerfile",
    "docker-compose.yml",
    "docker-compose.yaml",
    "netlify.toml",
    "vercel.json",
    "render.yaml",
    "vite.config.js",
    "vite.config.ts",
}


# ============================================================
# ARCHITECTURE DETECTION
# ============================================================

def detect_architecture(files):
    """
    Determine what the repository actually contains.

    This is intentionally based on repository evidence rather
    than incident telemetry.
    """

    paths = [
        file.get("path", "")
        for file in files
        if file.get("path")
    ]

    lowered_paths = [
        path.lower()
        for path in paths
    ]

    architecture = {
        "applicationTypes": [],
        "frameworks": [],
        "languages": [],
        "databaseDetected": False,
        "backendDetected": False,
        "frontendDetected": False,
        "deploymentPlatforms": [],
        "apiIndicators": [],
        "databaseIndicators": [],
    }

    # --------------------------------------------------------
    # Frontend / React / Vite
    # --------------------------------------------------------

    if any(
        path.endswith(
            (
                ".jsx",
                ".tsx",
            )
        )
        for path in lowered_paths
    ):
        architecture["frontendDetected"] = True

    if "package.json" in lowered_paths:
        architecture["languages"].append("JavaScript/TypeScript")

    if any(
        "vite.config" in path
        for path in lowered_paths
    ):
        architecture["frameworks"].append("Vite")

    if any(
        path.endswith(".jsx")
        for path in lowered_paths
    ):
        architecture["frameworks"].append("React")

    # --------------------------------------------------------
    # Python / FastAPI / Django
    # --------------------------------------------------------

    if (
        "requirements.txt" in lowered_paths
        or "pyproject.toml" in lowered_paths
        or any(
            path.endswith(".py")
            for path in lowered_paths
        )
    ):
        architecture["languages"].append("Python")
        architecture["backendDetected"] = True

    # --------------------------------------------------------
    # Java / Spring
    # --------------------------------------------------------

    if (
        "pom.xml" in lowered_paths
        or "build.gradle" in lowered_paths
        or "build.gradle.kts" in lowered_paths
        or any(
            path.endswith(".java")
            for path in lowered_paths
        )
    ):
        architecture["languages"].append("Java")
        architecture["backendDetected"] = True

    # --------------------------------------------------------
    # Node.js
    # --------------------------------------------------------

    if "package.json" in lowered_paths:
        architecture["frameworks"].append("Node.js ecosystem")

    # --------------------------------------------------------
    # Go
    # --------------------------------------------------------

    if "go.mod" in lowered_paths:
        architecture["languages"].append("Go")
        architecture["backendDetected"] = True

    # --------------------------------------------------------
    # Docker
    # --------------------------------------------------------

    if any(
        os.path.basename(path).lower() == "dockerfile"
        for path in lowered_paths
    ):
        architecture["deploymentPlatforms"].append("Docker")

    if (
        "docker-compose.yml" in lowered_paths
        or "docker-compose.yaml" in lowered_paths
    ):
        architecture["deploymentPlatforms"].append(
            "Docker Compose"
        )

    # --------------------------------------------------------
    # Netlify
    # --------------------------------------------------------

    if "netlify.toml" in lowered_paths:
        architecture["deploymentPlatforms"].append(
            "Netlify"
        )

    # --------------------------------------------------------
    # Vercel
    # --------------------------------------------------------

    if "vercel.json" in lowered_paths:
        architecture["deploymentPlatforms"].append(
            "Vercel"
        )

    # --------------------------------------------------------
    # Database indicators
    # --------------------------------------------------------

    database_patterns = [
        r"\.sql$",
        r"database",
        r"db/",
        r"models/",
        r"migrations/",
        r"migration",
        r"schema",
        r"prisma",
        r"sequelize",
        r"typeorm",
        r"sqlalchemy",
        r"hibernate",
        r"jdbc",
        r"mongodb",
        r"postgres",
        r"mysql",
        r"redis",
    ]

    database_matches = []

    for path in paths:
        lower_path = path.lower()

        for pattern in database_patterns:
            if re.search(pattern, lower_path):
                database_matches.append(path)
                break

    if database_matches:
        architecture["databaseDetected"] = True
        architecture["databaseIndicators"] = database_matches[:20]

    # --------------------------------------------------------
    # Backend indicators
    # --------------------------------------------------------

    backend_patterns = [
        r"/api/",
        r"\\api\\",
        r"routes/",
        r"controllers/",
        r"services/",
        r"server\.",
        r"app\.",
        r"main\.",
        r"server/",
        r"backend/",
    ]

    backend_matches = []

    for path in paths:
        lower_path = path.lower()

        for pattern in backend_patterns:
            if re.search(pattern, lower_path):
                backend_matches.append(path)
                break

    if backend_matches:
        architecture["backendDetected"] = True

    # --------------------------------------------------------
    # API indicators
    # --------------------------------------------------------

    api_patterns = [
        r"api",
        r"axios",
        r"fetch",
        r"graphql",
        r"endpoint",
        r"request",
        r"http",
    ]

    api_matches = []

    for path in paths:
        lower_path = path.lower()

        for pattern in api_patterns:
            if re.search(pattern, lower_path):
                api_matches.append(path)
                break

    architecture["apiIndicators"] = api_matches[:30]

    # --------------------------------------------------------
    # Application type
    # --------------------------------------------------------

    if architecture["frontendDetected"]:
        architecture["applicationTypes"].append(
            "Frontend application"
        )

    if architecture["backendDetected"]:
        architecture["applicationTypes"].append(
            "Backend/API application"
        )

    if architecture["databaseDetected"]:
        architecture["applicationTypes"].append(
            "Database-related components"
        )

    if not architecture["applicationTypes"]:
        architecture["applicationTypes"].append(
            "Unknown"
        )

    # Remove duplicates while preserving order.
    for key in [
        "applicationTypes",
        "frameworks",
        "languages",
        "deploymentPlatforms",
    ]:
        architecture[key] = list(
            dict.fromkeys(
                architecture[key]
            )
        )

    return architecture


# ============================================================
# FILE SCORING
# ============================================================

def score_file(
    file_path,
    architecture,
    service,
    latency,
    error_rate,
    db_connections,
    db_connection_limit,
    cpu,
    memory,
):
    """
    Score a file according to what the repository actually
    contains and what the current incident could plausibly
    involve.

    Telemetry is used only to prioritize investigation areas.
    It does NOT prove that a component exists.
    """

    path = file_path.lower()
    filename = os.path.basename(path)

    score = 0
    reasons = []

    # --------------------------------------------------------
    # Important application files
    # --------------------------------------------------------

    if filename in IMPORTANT_FILES:
        score += 8
        reasons.append(
            "Important application or deployment configuration"
        )

    # --------------------------------------------------------
    # Source code
    # --------------------------------------------------------

    extension = os.path.splitext(filename)[1]

    if extension in SOURCE_EXTENSIONS:
        score += 4
        reasons.append(
            "Application source code"
        )

    if extension in CONFIG_EXTENSIONS:
        score += 2
        reasons.append(
            "Application configuration"
        )

    # --------------------------------------------------------
    # Infrastructure
    # --------------------------------------------------------

    if filename in INFRASTRUCTURE_FILES:
        score += 7
        reasons.append(
            "Deployment or infrastructure configuration"
        )

    # --------------------------------------------------------
    # Service name
    # --------------------------------------------------------

    if service:
        service_tokens = [
            token.lower()
            for token in re.split(
                r"[^a-zA-Z0-9]+",
                service,
            )
            if token
        ]

        for token in service_tokens:
            if len(token) >= 3 and token in path:
                score += 3
                reasons.append(
                    f"Path matches incident service '{token}'"
                )

    # --------------------------------------------------------
    # API-related investigation
    # --------------------------------------------------------

    api_tokens = [
        "api",
        "fetch",
        "axios",
        "request",
        "endpoint",
        "http",
        "client",
        "service",
    ]

    if architecture["apiIndicators"]:
        if any(
            token in path
            for token in api_tokens
        ):
            score += 6
            reasons.append(
                "Potential API or external-service interaction"
            )

    # --------------------------------------------------------
    # Database-related investigation
    #
    # IMPORTANT:
    # Only score these strongly if the repository actually
    # contains database indicators.
    # --------------------------------------------------------

    if architecture["databaseDetected"]:
        database_tokens = [
            "database",
            "db",
            "sql",
            "migration",
            "schema",
            "prisma",
            "sequelize",
            "typeorm",
            "sqlalchemy",
            "hibernate",
            "jdbc",
            "redis",
            "mongo",
        ]

        if any(
            token in path
            for token in database_tokens
        ):
            score += 8
            reasons.append(
                "Repository contains database-related implementation"
            )

        if db_connection_limit > 0:
            utilization = (
                db_connections /
                db_connection_limit
            ) * 100

            if utilization >= 80:
                if any(
                    token in path
                    for token in database_tokens
                ):
                    score += 4
                    reasons.append(
                        "Database implementation is relevant to "
                        "high connection utilization"
                    )

    # --------------------------------------------------------
    # Latency investigation
    # --------------------------------------------------------

    if latency >= 1000:
        latency_tokens = [
            "api",
            "fetch",
            "axios",
            "request",
            "service",
            "client",
            "loader",
            "loading",
            "timeout",
            "async",
        ]

        if any(
            token in path
            for token in latency_tokens
        ):
            score += 5
            reasons.append(
                "Potential latency/request execution path"
            )

    # --------------------------------------------------------
    # Error investigation
    # --------------------------------------------------------

    if error_rate >= 5:
        error_tokens = [
            "api",
            "fetch",
            "axios",
            "request",
            "error",
            "auth",
            "login",
            "service",
            "client",
        ]

        if any(
            token in path
            for token in error_tokens
        ):
            score += 5
            reasons.append(
                "Potential source of request or application errors"
            )

    # --------------------------------------------------------
    # CPU investigation
    # --------------------------------------------------------

    if cpu >= 80:
        cpu_tokens = [
            "worker",
            "process",
            "service",
            "loop",
            "compute",
            "processor",
            "worker",
        ]

        if any(
            token in path
            for token in cpu_tokens
        ):
            score += 4
            reasons.append(
                "Potential CPU-intensive component"
            )

    # --------------------------------------------------------
    # Memory investigation
    # --------------------------------------------------------

    if memory >= 80:
        memory_tokens = [
            "cache",
            "store",
            "state",
            "worker",
            "process",
            "service",
        ]

        if any(
            token in path
            for token in memory_tokens
        ):
            score += 4
            reasons.append(
                "Potential memory-intensive component"
            )

    return score, list(
        dict.fromkeys(reasons)
    )


# ============================================================
# MAIN REPOSITORY CONTEXT BUILDER
# ============================================================

def get_relevant_repository_context(
    repository_url,
    github_token,
    service,
    latency,
    error_rate,
    db_connections,
    db_connection_limit,
    cpu,
    memory,
):
    """
    Build evidence-driven repository context.

    The important distinction is:

        telemetry -> investigation signal

        repository -> actual application capabilities

    The function deliberately does NOT assume that every
    telemetry field represents a component in the repository.
    """

    # --------------------------------------------------------
    # 1. Get repository inventory
    # --------------------------------------------------------

    repository = get_repository_tree(
        repository_url=repository_url,
        github_token=github_token,
    )

    files = repository.get(
        "files",
        [],
    )

    # --------------------------------------------------------
    # 2. Understand repository architecture
    # --------------------------------------------------------

    architecture = detect_architecture(
        files
    )

    # --------------------------------------------------------
    # 3. Score files
    # --------------------------------------------------------

    scored_files = []

    for file in files:
        path = file.get("path")

        if not path:
            continue

        score, reasons = score_file(
            file_path=path,
            architecture=architecture,
            service=service,
            latency=latency,
            error_rate=error_rate,
            db_connections=db_connections,
            db_connection_limit=db_connection_limit,
            cpu=cpu,
            memory=memory,
        )

        if score <= 0:
            continue

        scored_files.append(
            {
                "path": path,
                "score": score,
                "reasons": reasons,
                "size": file.get("size"),
            }
        )

    # --------------------------------------------------------
    # 4. Sort by investigation relevance
    # --------------------------------------------------------

    scored_files.sort(
        key=lambda item: (
            -item["score"],
            item["path"],
        )
    )

    selected = scored_files[
        :MAX_FILES_TO_ANALYZE
    ]

    # --------------------------------------------------------
    # 5. Retrieve actual contents
    # --------------------------------------------------------

    selected_files = []

    for item in selected:
        try:
            file_data = get_repository_file(
                repository_url=repository_url,
                github_token=github_token,
                file_path=item["path"],
            )

            content = file_data.get(
                "content",
                "",
            )

            if len(content) > MAX_FILE_CONTENT_LENGTH:
                content = (
                    content[
                        :MAX_FILE_CONTENT_LENGTH
                    ]
                    + "\n\n"
                    + "[FILE CONTENT TRUNCATED]"
                )

            selected_files.append(
                {
                    "path": item["path"],
                    "score": item["score"],
                    "reasons": item["reasons"],
                    "content": content,
                }
            )

        except Exception as exc:
            selected_files.append(
                {
                    "path": item["path"],
                    "score": item["score"],
                    "reasons": item["reasons"],
                    "content": "",
                    "readError": str(exc),
                }
            )

    # --------------------------------------------------------
    # 6. Build explicit investigation constraints
    # --------------------------------------------------------

    investigation_constraints = {
        "databaseEvidencePresent": architecture[
            "databaseDetected"
        ],
        "backendEvidencePresent": architecture[
            "backendDetected"
        ],
        "frontendEvidencePresent": architecture[
            "frontendDetected"
        ],
        "rules": [
            "Telemetry fields are symptoms and do not prove that a component exists.",
            "Do not diagnose a database problem unless repository evidence or explicit external-system evidence supports a database dependency.",
            "Do not identify a file as affected merely because its filename appears relevant.",
            "Affected files must contain actual code or configuration evidence related to the suspected failure.",
            "If the repository cannot explain the incident, explicitly report that additional external-system evidence is required.",
            "Distinguish confirmed repository evidence from hypotheses.",
        ],
    }

    # --------------------------------------------------------
    # 7. Return structured repository intelligence
    # --------------------------------------------------------

    return {
        "repository": {
            "owner": repository.get("owner"),
            "name": repository.get("repository"),
            "defaultBranch": repository.get(
                "default_branch"
            ),
            "language": repository.get(
                "language"
            ),
            "fileCount": repository.get(
                "file_count"
            ),
        },

        "architecture": architecture,

        "investigationConstraints": investigation_constraints,

        "selectedFiles": selected_files,
    }