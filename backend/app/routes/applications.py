from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.services.applications import (
    create_application,
    get_user_applications,
    get_application,
)
from app.services.auth import get_current_user


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


@router.get("")
def list_applications(request: Request):
    user = get_current_user(request)

    applications = get_user_applications(user["id"])

    return {
        "success": True,
        "applications": applications
    }


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