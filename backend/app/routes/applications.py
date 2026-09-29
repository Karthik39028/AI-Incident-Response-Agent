from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.applications import (
    create_application,
    get_user_applications,
    get_application,
)
from app.services.auth import get_current_user
from app.services.repository import get_repository_tree


router = APIRouter(
    prefix="/api/applications",
    tags=["Applications"]
)


class ApplicationCreate(BaseModel):
    name: str
    description: str | None = None

    runtime_type: str | None = None
    runtime_url: str | None = None

    source_type: str | None = None
    source_url: str | None = None

    deployment_type: str | None = None


# ============================================================
# CREATE APPLICATION
# ============================================================

@router.post("")
def create_new_application(
    application: ApplicationCreate,
    request: Request
):
    user = get_current_user(request)

    application_id = create_application(
        user_id=user["id"],
        name=application.name,
        description=application.description,
        runtime_type=application.runtime_type,
        runtime_url=application.runtime_url,
        source_type=application.source_type,
        source_url=application.source_url,
        deployment_type=application.deployment_type,
    )

    return {
        "success": True,
        "application_id": application_id
    }


# ============================================================
# LIST APPLICATIONS
# ============================================================

@router.get("")
def list_applications(request: Request):

    try:

        print("====================================")
        print("GET APPLICATIONS")
        print("====================================")

        user = get_current_user(request)

        print("USER:")
        print(user)

        applications = get_user_applications(
            user["id"]
        )

        print("APPLICATIONS:")
        print(applications)

        return {
            "success": True,
            "applications": applications
        }

    except Exception as e:

        print("====================================")
        print("APPLICATIONS ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ============================================================
# GET SINGLE APPLICATION
# ============================================================

@router.get("/{application_id}")
def get_single_application(
    application_id: int,
    request: Request
):
    user = get_current_user(request)

    application = get_application(
        application_id,
        user["id"]
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    return {
        "success": True,
        "application": application
    }


# ============================================================
# GET GITHUB REPOSITORY
# ============================================================

@router.get("/{application_id}/repository")
def get_application_repository(
    application_id: int,
    request: Request
):
    """
    Fetch the GitHub repository connected to an application.

    Flow:

    User
      ↓
    GitHub session
      ↓
    Verify application ownership
      ↓
    Get repository URL
      ↓
    repository.py
      ↓
    GitHub API
      ↓
    Safe repository file tree
    """

    # --------------------------------------------------------
    # 1. Authenticate user
    # --------------------------------------------------------

    user = get_current_user(request)

    # --------------------------------------------------------
    # 2. Get application belonging to this user
    # --------------------------------------------------------

    application = get_application(
        application_id,
        user["id"]
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found"
        )

    # --------------------------------------------------------
    # 3. Make sure repository source is GitHub
    # --------------------------------------------------------

    source_type = application.get("source_type")

    if source_type != "GitHub":
        raise HTTPException(
            status_code=400,
            detail="Only GitHub repositories are supported currently"
        )

    # --------------------------------------------------------
    # 4. Get repository URL
    # --------------------------------------------------------

    repository_url = application.get("source_url")

    if not repository_url:
        raise HTTPException(
            status_code=400,
            detail="Application does not have a repository URL"
        )

    # --------------------------------------------------------
    # 5. Get GitHub session token
    # --------------------------------------------------------

    github_token = request.cookies.get(
        "github_session"
    )

    if not github_token:
        raise HTTPException(
            status_code=401,
            detail="GitHub session not found"
        )

    # --------------------------------------------------------
    # 6. Read repository
    # --------------------------------------------------------

    try:

        repository = get_repository_tree(
            repository_url=repository_url,
            github_token=github_token,
        )

        # ----------------------------------------------------
        # 7. Return repository information
        # ----------------------------------------------------

        return {
            "success": True,
            "application_id": application_id,
            "repository": repository,
        }

    except ValueError as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:

        print("====================================")
        print("REPOSITORY ERROR")
        print("====================================")
        print(type(e).__name__)
        print(str(e))
        print("====================================")

        raise HTTPException(
            status_code=500,
            detail="Failed to read GitHub repository"
        )