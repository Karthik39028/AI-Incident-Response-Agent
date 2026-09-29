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


def initialize_database():
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                github_id VARCHAR(255) UNIQUE,
                username VARCHAR(255),
                email VARCHAR(255),
                avatar_url VARCHAR(2048),
                access_token TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                user_id BIGINT NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                runtime_type VARCHAR(100),
                runtime_url VARCHAR(2048),
                source_type VARCHAR(100),
                source_url VARCHAR(2048),
                deployment_type VARCHAR(100),
                status VARCHAR(50) DEFAULT 'active',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_applications_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                application_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,
                service VARCHAR(255) NOT NULL,
                latency_ms DOUBLE,
                error_rate DOUBLE,
                db_connections INT,
                db_connection_limit INT,
                cpu DOUBLE,
                memory DOUBLE,
                status VARCHAR(50) NOT NULL DEFAULT 'INVESTIGATING',
                root_cause TEXT,
                confidence DOUBLE,
                diagnosis_status VARCHAR(50),
                reasoning TEXT,
                recommendation_type VARCHAR(100),
                recommendation_action TEXT,
                recommendation_reason TEXT,
                requires_approval BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP NULL,
                CONSTRAINT fk_incidents_application
                    FOREIGN KEY (application_id)
                    REFERENCES applications(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_incidents_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recovery_actions (
                id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                incident_id BIGINT NOT NULL,
                action_type VARCHAR(100) NOT NULL,
                action_description TEXT NOT NULL,
                target VARCHAR(255),
                status VARCHAR(50) NOT NULL DEFAULT 'PENDING_APPROVAL',
                requires_approval BOOLEAN DEFAULT TRUE,
                approved_by BIGINT,
                approved_at TIMESTAMP NULL,
                started_at TIMESTAMP NULL,
                completed_at TIMESTAMP NULL,
                result TEXT,
                verification_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_recovery_incident
                    FOREIGN KEY (incident_id)
                    REFERENCES incidents(id)
                    ON DELETE CASCADE,
                CONSTRAINT fk_recovery_approver
                    FOREIGN KEY (approved_by)
                    REFERENCES users(id)
                    ON DELETE SET NULL
            )
            """
        )

        connection.commit()

    finally:
        cursor.close()
        connection.close()


def save_or_update_github_user(
    github_id,
    username,
    email,
    avatar_url,
    access_token,
):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT id FROM users WHERE github_id = %s",
            (github_id,),
        )

        existing_user = cursor.fetchone()

        if existing_user:
            cursor.execute(
                """
                UPDATE users
                SET username = %s,
                    email = %s,
                    avatar_url = %s,
                    access_token = %s
                WHERE github_id = %s
                """,
                (
                    username,
                    email,
                    avatar_url,
                    access_token,
                    github_id,
                ),
            )

            user_id = existing_user["id"]

        else:
            cursor.execute(
                """
                INSERT INTO users (
                    github_id,
                    username,
                    email,
                    avatar_url,
                    access_token
                )
                VALUES (%s, %s, %s, %s, %s)
                """,
                (
                    github_id,
                    username,
                    email,
                    avatar_url,
                    access_token,
                ),
            )

            user_id = cursor.lastrowid

        connection.commit()

        return user_id

    finally:
        cursor.close()
        connection.close()