import mysql.connector

from app.config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DATABASE,
    MYSQL_USER,
    MYSQL_PASSWORD,
)


def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DATABASE,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
    )


def save_or_update_github_user(github_user):
    connection = get_connection()
    cursor = connection.cursor()

    github_id = github_user.get("id")
    github_username = github_user.get("login")
    name = github_user.get("name")
    email = github_user.get("email")
    avatar_url = github_user.get("avatar_url")
    github_profile_url = github_user.get("html_url")

    query = """
        INSERT INTO users (
            github_id,
            github_username,
            name,
            email,
            avatar_url,
            github_profile_url
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            github_username = VALUES(github_username),
            name = VALUES(name),
            email = VALUES(email),
            avatar_url = VALUES(avatar_url),
            github_profile_url = VALUES(github_profile_url),
            last_login_at = CURRENT_TIMESTAMP
    """

    values = (
        github_id,
        github_username,
        name,
        email,
        avatar_url,
        github_profile_url,
    )

    cursor.execute(query, values)
    connection.commit()

    cursor.execute(
        "SELECT id, github_id, github_username, name, email, avatar_url, github_profile_url, created_at, last_login_at "
        "FROM users WHERE github_id = %s",
        (github_id,),
    )

    row = cursor.fetchone()

    cursor.close()
    connection.close()

    if not row:
        return None

    return {
        "id": row[0],
        "github_id": row[1],
        "github_username": row[2],
        "name": row[3],
        "email": row[4],
        "avatar_url": row[5],
        "github_profile_url": row[6],
        "created_at": row[7],
        "last_login_at": row[8],
    }