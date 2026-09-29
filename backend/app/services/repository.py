import base64
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


# Maximum amount of source code we allow the agent to read
# from one repository file.
MAX_FILE_SIZE = 200_000


# Maximum number of repository files returned by the scanner.
#
# The repository_context service will later select only the
# most relevant files from this list.
MAX_REPOSITORY_FILES = 5_000


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
# GITHUB HEADERS
# ============================================================

def build_github_headers(github_token: str):

    return {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-Incident-Response-Agent",
    }


# ============================================================
# GITHUB ERROR HANDLER
# ============================================================

def raise_github_error(
    response,
    action: str,
):

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
            f"GitHub {action} failed because the repository "
            "or requested resource was not found."
        )

    if response.status_code != 200:

        raise ValueError(
            f"GitHub {action} failed: "
            f"{response.status_code} - "
            f"{response.text[:500]}"
        )


# ============================================================
# GET REPOSITORY INFORMATION
# ============================================================

def get_repository_metadata(
    repository_url: str,
    github_token: str,
):

    owner, repository = parse_github_repository_url(
        repository_url
    )

    headers = build_github_headers(
        github_token
    )

    repository_api_url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}"
    )

    response = requests.get(
        repository_api_url,
        headers=headers,
        timeout=15,
    )

    raise_github_error(
        response,
        "repository request",
    )

    repo_data = response.json()

    default_branch = repo_data.get(
        "default_branch"
    )

    if not default_branch:

        raise ValueError(
            "GitHub repository has no default branch"
        )

    return {
        "owner": owner,
        "repository": repository,
        "default_branch": default_branch,
        "private": repo_data.get(
            "private",
            False,
        ),
        "description": repo_data.get(
            "description"
        ),
        "language": repo_data.get(
            "language"
        ),
    }


# ============================================================
# GET REPOSITORY TREE
# ============================================================

def get_repository_tree(
    repository_url: str,
    github_token: str,
):

    # --------------------------------------------------------
    # 1. Get repository metadata
    # --------------------------------------------------------

    metadata = get_repository_metadata(
        repository_url=repository_url,
        github_token=github_token,
    )

    owner = metadata["owner"]
    repository = metadata["repository"]
    default_branch = metadata["default_branch"]

    headers = build_github_headers(
        github_token
    )

    # --------------------------------------------------------
    # 2. Get branch information
    #
    # We need the branch SHA because the Git Trees API works
    # from a Git tree SHA.
    # --------------------------------------------------------

    branch_url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}/branches/"
        f"{quote(default_branch, safe='')}"
    )

    branch_response = requests.get(
        branch_url,
        headers=headers,
        timeout=15,
    )

    raise_github_error(
        branch_response,
        "branch request",
    )

    branch_data = branch_response.json()

    commit_data = branch_data.get(
        "commit"
    )

    if not commit_data:

        raise ValueError(
            "GitHub branch does not contain commit information"
        )

    commit_sha = commit_data.get(
        "sha"
    )

    if not commit_sha:

        raise ValueError(
            "GitHub branch does not contain a commit SHA"
        )

    # --------------------------------------------------------
    # 3. Get the complete repository tree
    #
    # This is the important performance improvement.
    #
    # Instead of:
    #
    #   directory -> API request
    #   subdirectory -> API request
    #   subdirectory -> API request
    #
    # GitHub returns the repository tree recursively.
    # --------------------------------------------------------

    tree_url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}/git/trees/"
        f"{commit_sha}"
    )

    tree_response = requests.get(
        tree_url,
        params={
            "recursive": "1",
        },
        headers=headers,
        timeout=30,
    )

    if tree_response.status_code == 409:

        raise ValueError(
            "GitHub could not read the repository tree. "
            "The repository may be empty."
        )

    raise_github_error(
        tree_response,
        "repository tree request",
    )

    tree_data = tree_response.json()

    tree_items = tree_data.get(
        "tree",
        [],
    )

    files = []

    # --------------------------------------------------------
    # 4. Process repository files
    # --------------------------------------------------------

    for item in tree_items:

        item_type = item.get(
            "type"
        )

        item_path = item.get(
            "path"
        )

        if item_type != "blob":
            continue

        if not item_path:
            continue

        # Security filtering
        if not is_safe_file(item_path):
            continue

        files.append({
            "path": item_path,
            "sha": item.get("sha"),
            "size": item.get("size"),
            "download_url": (
                f"{GITHUB_API}/repos/"
                f"{owner}/{repository}/contents/"
                f"{quote(item_path, safe='/')}"
            ),
        })

        # Prevent an unexpectedly huge repository from
        # producing an enormous response.
        if len(files) >= MAX_REPOSITORY_FILES:
            break

    # --------------------------------------------------------
    # 5. Return repository structure
    # --------------------------------------------------------

    return {
        "owner": owner,
        "repository": repository,
        "default_branch": default_branch,
        "private": metadata["private"],
        "description": metadata["description"],
        "language": metadata["language"],
        "file_count": len(files),
        "files": files,
    }


# ============================================================
# GET SOURCE FILE CONTENT
# ============================================================

def get_repository_file(
    repository_url: str,
    github_token: str,
    file_path: str,
):

    owner, repository = parse_github_repository_url(
        repository_url
    )

    # --------------------------------------------------------
    # Security check
    # --------------------------------------------------------

    if not is_safe_file(file_path):

        raise ValueError(
            "Access to this file is blocked for security reasons"
        )

    headers = build_github_headers(
        github_token
    )

    # --------------------------------------------------------
    # Get repository metadata
    # --------------------------------------------------------

    repository_api_url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}"
    )

    repository_response = requests.get(
        repository_api_url,
        headers=headers,
        timeout=15,
    )

    raise_github_error(
        repository_response,
        "repository request",
    )

    repository_data = repository_response.json()

    default_branch = repository_data.get(
        "default_branch"
    )

    if not default_branch:

        raise ValueError(
            "GitHub repository has no default branch"
        )

    # --------------------------------------------------------
    # Request the file
    # --------------------------------------------------------

    encoded_path = quote(
        file_path,
        safe="/",
    )

    url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repository}/contents/"
        f"{encoded_path}"
    )

    response = requests.get(
        url,
        params={
            "ref": default_branch,
        },
        headers=headers,
        timeout=20,
    )

    raise_github_error(
        response,
        "file request",
    )

    file_data = response.json()

    # --------------------------------------------------------
    # Make sure GitHub returned a file
    # --------------------------------------------------------

    if file_data.get("type") != "file":

        raise ValueError(
            f"Repository path is not a file: "
            f"{file_path}"
        )

    file_size = file_data.get(
        "size",
        0,
    )

    if file_size > MAX_FILE_SIZE:

        raise ValueError(
            f"Repository file is too large to analyze: "
            f"{file_path}"
        )

    encoded_content = file_data.get(
        "content"
    )

    if not encoded_content:

        raise ValueError(
            f"Repository file has no readable content: "
            f"{file_path}"
        )

    # --------------------------------------------------------
    # Decode GitHub content
    # --------------------------------------------------------

    try:

        content = base64.b64decode(
            encoded_content
        ).decode(
            "utf-8"
        )

    except (
        ValueError,
        UnicodeDecodeError,
    ):

        raise ValueError(
            f"Repository file is not readable as UTF-8 text: "
            f"{file_path}"
        )

    # --------------------------------------------------------
    # Return file
    # --------------------------------------------------------

    return {
        "path": file_path,
        "size": file_size,
        "sha": file_data.get(
            "sha"
        ),
        "content": content,
    }