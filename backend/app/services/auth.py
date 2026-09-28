import requests
from fastapi import Request, HTTPException

from app.services.database import get_connection


def get_current_user(request: Request):
    github_session = request.cookies.get("github_session")

    if not github_session:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    # Validate the GitHub access token
    response = requests.get(
        "https://api.github.com/user",
        headers={
            "Authorization": f"Bearer {github_session}",
            "Accept": "application/vnd.github+json",
        },
        timeout=10,
    )

    if response.status_code != 200:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired GitHub session"
        )

    github_user = response.json()
    github_id = github_user.get("id")

    if not github_id:
        raise HTTPException(
            status_code=401,
            detail="Unable to identify GitHub user"
        )

    # Find the corresponding user in MySQL
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute(
        """
        SELECT
            id,
            github_id,
            github_username,
            name,
            email,
            avatar_url,
            github_profile_url,
            created_at,
            last_login_at
        FROM users
        WHERE github_id = %s
        """,
        (github_id,),
    )

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found in database"
        )

    return user