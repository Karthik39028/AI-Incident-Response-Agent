import requests
from urllib.parse import urlparse, quote


GITHUB_API = "https://api.github.com"


# ============================================================
# SECURITY
# ============================================================

BLOCKED_FILE_NAMES = {
    ".env",
    ".env.local",
    ".env.production",
    ".env.development",
    ".env.test",
    "credentials.json",
    "secrets.json",
}

BLOCKED_EXTENSIONS = {
    ".pem",
    ".key",
    ".crt",
    ".p12",
    ".pfx",
}


# ============================================================
# PARSE GITHUB URL
# ============================================================

def parse_github_repository_url(repository_url: str):

    parsed = urlparse(repository_url)

    if parsed.netloc.lower() not in {
        "github.com",
        "www.github.com",
    }:
        raise ValueError(
            "Only GitHub repository URLs are supported"
        )

    parts = [
        part
        for part in parsed.path.strip("/").split("/")
        if part
    ]

    if len(parts) < 2:
        raise ValueError(
            "Invalid GitHub repository URL"
        )

    owner = parts[0]
    repository = parts[1]

    if repository.endswith(".git"):
        repository = repository[:-4]

    return owner, repository


# ============================================================
# FILE SECURITY CHECK
# ============================================================

def is_safe_file(path: str):

    filename = path.split("/")[-1].lower()

    # Exact blocked filenames
    if filename in BLOCKED_FILE_NAMES:
        return False

    # Block every .env variant
    if filename.startswith(".env"):
        return False

    # Block private keys / certificates
    for extension in BLOCKED_EXTENSIONS:

        if filename.endswith(extension):
            return False

    return True


# ============================================================
# GET REPOSITORY INFORMATION
# ============================================================

def get_repository_tree(
    repository_url: str,
    github_token: str,
):

    owner, repository = parse_github_repository_url(
        repository_url
    )

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-Incident-Response-Agent",
    }

    # ========================================================
    # 1. GET REPOSITORY METADATA
    # ========================================================

    repository_api_url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}"
    )

    response = requests.get(
        repository_api_url,
        headers=headers,
        timeout=15,
    )

    if response.status_code == 401:

        raise ValueError(
            "GitHub authentication failed. "
            "Please login to GitHub again."
        )

    if response.status_code == 403:

        raise ValueError(
            "GitHub access denied. "
            "Your GitHub OAuth token may not have "
            "repository access."
        )

    if response.status_code == 404:

        raise ValueError(
            "GitHub repository not found or not accessible. "
            "Check the repository URL and GitHub permissions."
        )

    if response.status_code != 200:

        raise ValueError(
            f"GitHub repository request failed: "
            f"{response.status_code} - "
            f"{response.text[:500]}"
        )

    repo_data = response.json()

    default_branch = repo_data.get(
        "default_branch"
    )

    if not default_branch:

        raise ValueError(
            "GitHub repository has no default branch"
        )

    # ========================================================
    # 2. REPOSITORY FILE COLLECTION
    # ========================================================

    files = []

    # Prevent runaway recursion
    visited_directories = set()

    # ========================================================
    # 3. SCAN DIRECTORY USING CONTENTS API
    # ========================================================

    def scan_directory(path=""):

        if path in visited_directories:
            return

        visited_directories.add(path)

        # ----------------------------------------------------
        # Build GitHub Contents API URL
        # ----------------------------------------------------

        if path:

            encoded_path = quote(
                path,
                safe="/"
            )

            url = (
                f"{GITHUB_API}/repos/"
                f"{owner}/{repository}/contents/"
                f"{encoded_path}"
            )

        else:

            url = (
                f"{GITHUB_API}/repos/"
                f"{owner}/{repository}/contents"
            )

        # ----------------------------------------------------
        # Request directory
        # ----------------------------------------------------

        response = requests.get(
            url,
            params={
                "ref": default_branch,
            },
            headers=headers,
            timeout=20,
        )

        # ----------------------------------------------------
        # Authentication
        # ----------------------------------------------------

        if response.status_code == 401:

            raise ValueError(
                "GitHub authentication failed. "
                "Please login to GitHub again."
            )

        # ----------------------------------------------------
        # Permission
        # ----------------------------------------------------

        if response.status_code == 403:

            raise ValueError(
                "GitHub denied access to repository contents. "
                "Your OAuth token may not have repository access."
            )

        # ----------------------------------------------------
        # Not found
        # ----------------------------------------------------

        if response.status_code == 404:

            raise ValueError(
                "GitHub repository contents could not be accessed. "
                f"Path: {path or '/'} | "
                f"Branch: {default_branch} | "
                f"Response: {response.text[:500]}"
            )

        # ----------------------------------------------------
        # Other errors
        # ----------------------------------------------------

        if response.status_code != 200:

            raise ValueError(
                f"GitHub contents request failed: "
                f"{response.status_code} - "
                f"{response.text[:500]}"
            )

        # ----------------------------------------------------
        # Parse response
        # ----------------------------------------------------

        items = response.json()

        # GitHub returns an object instead of a list if
        # the requested path is a single file.
        if not isinstance(items, list):

            return

        # ====================================================
        # PROCESS DIRECTORY CONTENTS
        # ====================================================

        for item in items:

            item_type = item.get("type")
            item_path = item.get("path")

            if not item_path:
                continue

            # ------------------------------------------------
            # Directory
            # ------------------------------------------------

            if item_type == "dir":

                scan_directory(item_path)

            # ------------------------------------------------
            # File
            # ------------------------------------------------

            elif item_type == "file":

                if not is_safe_file(item_path):
                    continue

                files.append({
                    "path": item_path,
                    "sha": item.get("sha"),
                    "size": item.get("size"),
                    "download_url": item.get(
                        "download_url"
                    ),
                })

    # ========================================================
    # START SCANNING
    # ========================================================

    scan_directory()

    # ========================================================
    # 4. RETURN REPOSITORY STRUCTURE
    # ========================================================

    return {
        "owner": owner,
        "repository": repository,
        "default_branch": default_branch,
        "private": repo_data.get(
            "private",
            False
        ),
        "description": repo_data.get(
            "description"
        ),
        "language": repo_data.get(
            "language"
        ),
        "file_count": len(files),
        "files": files,
    }