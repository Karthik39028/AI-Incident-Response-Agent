from app.services.database import get_connection


def create_application(
    user_id,
    name,
    description=None,
    runtime_type=None,
    runtime_url=None,
    source_type=None,
    source_url=None,
    deployment_type=None,
):
    connection = get_connection()
    cursor = connection.cursor()

    query = """
        INSERT INTO applications (
            user_id,
            name,
            description,
            runtime_type,
            runtime_url,
            source_type,
            source_url,
            deployment_type
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """

    values = (
        user_id,
        name,
        description,
        runtime_type,
        runtime_url,
        source_type,
        source_url,
        deployment_type,
    )

    cursor.execute(query, values)
    connection.commit()

    application_id = cursor.lastrowid

    cursor.close()
    connection.close()

    return application_id


def get_user_applications(user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            name,
            description,
            runtime_type,
            runtime_url,
            source_type,
            source_url,
            deployment_type,
            status,
            created_at,
            updated_at
        FROM applications
        WHERE user_id = %s
        ORDER BY created_at DESC
    """

    cursor.execute(query, (user_id,))
    applications = cursor.fetchall()

    cursor.close()
    connection.close()

    return applications


def get_application(application_id, user_id):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    query = """
        SELECT
            id,
            name,
            description,
            runtime_type,
            runtime_url,
            source_type,
            source_url,
            deployment_type,
            status,
            created_at,
            updated_at
        FROM applications
        WHERE id = %s
        AND user_id = %s
    """

    cursor.execute(query, (application_id, user_id))
    application = cursor.fetchone()

    cursor.close()
    connection.close()

    return application