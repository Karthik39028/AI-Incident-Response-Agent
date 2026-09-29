import secrets
import requests

from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.database import save_or_update_github_user

from app.config import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GITHUB_REDIRECT_URI,
    FRONTEND_URL,
)


router = APIRouter(
    prefix="/api/auth/github",
    tags=["GitHub Authentication"]
)


# ============================================================
# START GITHUB LOGIN
# ============================================================

@router.get("/login")
def github_login():

    print("\n========================================")
    print("STARTING GITHUB LOGIN")
    print("========================================")

    if not GITHUB_CLIENT_ID:
        print("ERROR: GITHUB_CLIENT_ID is missing")

        raise HTTPException(
            status_code=500,
            detail="GITHUB_CLIENT_ID is not configured"
        )

    if not GITHUB_CLIENT_SECRET:
        print("ERROR: GITHUB_CLIENT_SECRET is missing")

        raise HTTPException(
            status_code=500,
            detail="GITHUB_CLIENT_SECRET is not configured"
        )

    # --------------------------------------------------------
    # Generate OAuth state
    # --------------------------------------------------------

    state = secrets.token_urlsafe(32)

    print("GitHub Client ID configured:", bool(GITHUB_CLIENT_ID))
    print("GitHub Client Secret configured:", bool(GITHUB_CLIENT_SECRET))
    print("GitHub Redirect URI:", GITHUB_REDIRECT_URI)
    print("OAuth state generated:", True)

    # --------------------------------------------------------
    # GitHub authorization URL
    #
    # IMPORTANT:
    # repo scope is required so the OAuth token can access
    # repository contents, including private repositories
    # that the authenticated user can access.
    # --------------------------------------------------------

    oauth_params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,
        "state": state,
        "scope": "repo",
    }

    github_authorize_url = (
        "https://github.com/login/oauth/authorize?"
        + urlencode(oauth_params)
    )

    print("GitHub OAuth scope: repo")
    print("Redirecting user to GitHub")
    print("========================================\n")

    response = RedirectResponse(
        url=github_authorize_url,
        status_code=302
    )

    # --------------------------------------------------------
    # Store OAuth state in cookie
    # --------------------------------------------------------

    response.set_cookie(
        key="github_oauth_state",
        value=state,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=600,
        path="/",
    )

    return response


# ============================================================
# GITHUB CALLBACK
# ============================================================

@router.get("/callback")
def github_callback(
    request: Request,
    code: str | None = None,
    state: str | None = None,
):

    print("\n========================================")
    print("GITHUB CALLBACK")
    print("========================================")

    # --------------------------------------------------------
    # Check authorization code
    # --------------------------------------------------------

    print("Authorization code received:", bool(code))
    print("State received:", bool(state))

    if not code:
        print("ERROR: GitHub authorization code missing")

        raise HTTPException(
            status_code=400,
            detail="GitHub authorization code missing"
        )

    # --------------------------------------------------------
    # Read stored OAuth state
    # --------------------------------------------------------

    stored_state = request.cookies.get(
        "github_oauth_state"
    )

    print("OAuth state received:", bool(state))
    print("OAuth state cookie:", bool(stored_state))

    # --------------------------------------------------------
    # Validate OAuth state
    # --------------------------------------------------------

    if (
        not state
        or not stored_state
        or state != stored_state
    ):
        print("ERROR: Invalid OAuth state")

        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state"
        )

    print("OAuth state validation: PASSED")

    # --------------------------------------------------------
    # Validate configuration
    # --------------------------------------------------------

    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_CLIENT_ID is not configured"
        )

    if not GITHUB_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="GITHUB_CLIENT_SECRET is not configured"
        )

    print("GitHub Client ID configured:", True)
    print("GitHub Client Secret configured:", True)
    print("GitHub Redirect URI:", GITHUB_REDIRECT_URI)

    # ========================================================
    # EXCHANGE AUTHORIZATION CODE FOR ACCESS TOKEN
    # ========================================================

    print("\n----------------------------------------")
    print("EXCHANGING CODE FOR GITHUB TOKEN")
    print("----------------------------------------")

    try:

        token_response = requests.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },
            headers={
                "Accept": "application/json",
            },
            timeout=15,
        )

    except requests.RequestException as error:

        print("GitHub token request failed:")
        print(str(error))

        raise HTTPException(
            status_code=502,
            detail="Could not connect to GitHub token service"
        )

    print(
        "GitHub token response:",
        token_response.status_code
    )

    # --------------------------------------------------------
    # Parse response
    # --------------------------------------------------------

    try:

        token_data = token_response.json()

    except ValueError:

        print("ERROR: GitHub returned invalid JSON")

        raise HTTPException(
            status_code=502,
            detail="GitHub returned an invalid token response"
        )

    # --------------------------------------------------------
    # Safe debug output
    # --------------------------------------------------------

    print(
        "GitHub token response keys:",
        list(token_data.keys())
    )

    if token_data.get("error"):

        print(
            "GitHub OAuth error:",
            token_data.get("error")
        )

        print(
            "GitHub OAuth error description:",
            token_data.get("error_description")
        )

        print(
            "GitHub OAuth error URI:",
            token_data.get("error_uri")
        )

    # --------------------------------------------------------
    # HTTP status check
    # --------------------------------------------------------

    if token_response.status_code != 200:

        raise HTTPException(
            status_code=502,
            detail=(
                "GitHub token exchange failed: "
                + token_data.get(
                    "error_description",
                    token_data.get(
                        "error",
                        "Unknown GitHub error"
                    )
                )
            )
        )

    # --------------------------------------------------------
    # Get access token
    # --------------------------------------------------------

    access_token = token_data.get(
        "access_token"
    )

    if not access_token:

        print(
            "ERROR: GitHub did not return an access token"
        )

        raise HTTPException(
            status_code=400,
            detail=token_data.get(
                "error_description",
                token_data.get(
                    "error",
                    "GitHub did not return an access token"
                )
            )
        )

    print("GitHub access token received: True")

    # ========================================================
    # GET GITHUB USER
    # ========================================================

    print("\n----------------------------------------")
    print("GETTING GITHUB USER")
    print("----------------------------------------")

    try:

        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "AI-Incident-Response-Agent",
            },
            timeout=15,
        )

    except requests.RequestException as error:

        print("GitHub user request failed:")
        print(str(error))

        raise HTTPException(
            status_code=502,
            detail="Could not connect to GitHub user API"
        )

    print(
        "GitHub user response:",
        user_response.status_code
    )

    if user_response.status_code != 200:

        print(
            "GitHub user API response:",
            user_response.text[:500]
        )

        raise HTTPException(
            status_code=502,
            detail="Could not retrieve GitHub user"
        )

    github_user = user_response.json()

    print(
        "GitHub username:",
        github_user.get("login")
    )

    print(
        "GitHub user ID:",
        github_user.get("id")
    )

    # ========================================================
    # SAVE / UPDATE USER IN MYSQL
    # ========================================================

    print("\n----------------------------------------")
    print("SAVING USER TO DATABASE")
    print("----------------------------------------")

    try:

        db_user = save_or_update_github_user(
            github_user
        )

    except Exception as error:

        print("DATABASE ERROR:")
        print(str(error))

        raise HTTPException(
            status_code=500,
            detail="Could not save GitHub user to database"
        )

    if not db_user:

        print("ERROR: Database user was not returned")

        raise HTTPException(
            status_code=500,
            detail="User could not be saved"
        )

    print(
        "DATABASE USER SAVED:",
        f"id={db_user['id']},",
        f"github={db_user['github_username']}"
    )

    # ========================================================
    # CREATE FRONTEND REDIRECT
    # ========================================================

    response = RedirectResponse(
        url=f"{FRONTEND_URL}/dashboard",
        status_code=302
    )

    # --------------------------------------------------------
    # Remove OAuth state cookie
    # --------------------------------------------------------

    response.delete_cookie(
        key="github_oauth_state",
        path="/"
    )

    # ========================================================
    # CREATE SESSION COOKIE
    # ========================================================

    response.set_cookie(
        key="github_session",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 7,
        path="/",
    )

    print("\n----------------------------------------")
    print("SESSION CREATED")
    print("----------------------------------------")

    print("github_session cookie SET: True")

    print(
        "Redirecting to:",
        f"{FRONTEND_URL}/dashboard"
    )

    print("========================================")
    print("GITHUB LOGIN SUCCESS")
    print("========================================\n")

    return response


# ============================================================
# GET CURRENT USER
# ============================================================

@router.get("/me")
def github_me(request: Request):

    print("\n----------------------------------------")
    print("GITHUB /ME")
    print("----------------------------------------")

    # --------------------------------------------------------
    # Read session cookie
    # --------------------------------------------------------

    access_token = request.cookies.get(
        "github_session"
    )

    print(
        "github_session received:",
        bool(access_token)
    )

    # --------------------------------------------------------
    # No session
    # --------------------------------------------------------

    if not access_token:

        print("NO SESSION COOKIE")
        print("----------------------------------------\n")

        return JSONResponse(
            status_code=401,
            content={
                "authenticated": False,
                "reason": "github_session cookie missing"
            }
        )

    # --------------------------------------------------------
    # Validate token with GitHub
    # --------------------------------------------------------

    try:

        user_response = requests.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "AI-Incident-Response-Agent",
            },
            timeout=15,
        )

    except requests.RequestException as error:

        print(
            "GitHub /user request failed:",
            str(error)
        )

        return JSONResponse(
            status_code=502,
            content={
                "authenticated": False,
                "reason": "Could not connect to GitHub"
            }
        )

    print(
        "GitHub API status:",
        user_response.status_code
    )

    # --------------------------------------------------------
    # Invalid token
    # --------------------------------------------------------

    if user_response.status_code != 200:

        print("INVALID GITHUB TOKEN")

        response = JSONResponse(
            status_code=401,
            content={
                "authenticated": False,
                "reason": "GitHub token invalid"
            }
        )

        response.delete_cookie(
            key="github_session",
            path="/"
        )

        return response

    # --------------------------------------------------------
    # Parse GitHub user
    # --------------------------------------------------------

    user = user_response.json()

    print(
        "Authenticated user:",
        user.get("login")
    )

    print("----------------------------------------\n")

    return {
        "authenticated": True,
        "user": {
            "id": user.get("id"),
            "login": user.get("login"),
            "name": user.get("name"),
            "avatar_url": user.get("avatar_url"),
            "html_url": user.get("html_url"),
        }
    }


# ============================================================
# GET GITHUB REPOSITORIES
# ============================================================

@router.get("/repositories")
def get_github_repositories(request: Request):
    """
    Return the real GitHub repositories belonging to
    the currently authenticated GitHub user.
    """

    access_token = request.cookies.get(
        "github_session"
    )

    if not access_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub session not found. Please login again."
        )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AI-Incident-Response-Agent",
    }

    repositories = []
    page = 1

    try:

        while True:

            response = requests.get(
                "https://api.github.com/user/repos",
                headers=headers,
                params={
                    "per_page": 100,
                    "page": page,
                    "sort": "updated",
                    "direction": "desc",
                },
                timeout=15,
            )

            if response.status_code != 200:

                try:
                    github_error = response.json()

                    detail = github_error.get(
                        "message",
                        "GitHub repository request failed"
                    )

                except ValueError:

                    detail = (
                        "GitHub repository request failed"
                    )

                raise HTTPException(
                    status_code=response.status_code,
                    detail=detail,
                )

            page_data = response.json()

            if not page_data:
                break

            for repo in page_data:

                repositories.append({
                    "id": repo.get("id"),
                    "name": repo.get("name"),
                    "fullName": repo.get("full_name"),
                    "url": repo.get("html_url"),
                    "private": repo.get("private", False),
                    "defaultBranch": repo.get("default_branch"),
                    "owner": (
                        repo.get("owner") or {}
                    ).get("login"),
                    "description": repo.get(
                        "description"
                    ),
                    "language": repo.get("language"),
                })

            if len(page_data) < 100:
                break

            page += 1

    except requests.RequestException:

        raise HTTPException(
            status_code=502,
            detail="Could not connect to GitHub repository API"
        )

    return {
        "repositories": repositories,
        "total": len(repositories),
    }


# ============================================================
# LOGOUT
# ============================================================

@router.post("/logout")
def github_logout():

    print("\n----------------------------------------")
    print("GITHUB LOGOUT")
    print("----------------------------------------")

    response = JSONResponse(
        content={
            "message": "Logged out successfully"
        }
    )

    response.delete_cookie(
        key="github_session",
        path="/"
    )

    print("github_session cookie deleted")
    print("----------------------------------------\n")

    return response