import mysql.connector

from app.config import (
    MYSQL_HOST,
    MYSQL_PORT,
    MYSQL_DATABASE,
    MYSQL_USER,
    MYSQL_PASSWORD,
)


# ============================================================
# DATABASE CONNECTION
# ============================================================

def get_connection():
    return mysql.connector.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        database=MYSQL_DATABASE,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
    )


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def initialize_database():
    """
    Create all application tables automatically if they do not
    already exist.

    This function is safe to run every time the backend starts.
    Existing tables and data are preserved.
    """

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # --------------------------------------------------------
        # USERS
        # --------------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id BIGINT NOT NULL AUTO_INCREMENT,
                github_id BIGINT NOT NULL,
                github_username VARCHAR(255) NOT NULL,
                name VARCHAR(255),
                email VARCHAR(255),
                avatar_url VARCHAR(2048),
                github_profile_url VARCHAR(2048),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,

                PRIMARY KEY (id),
                UNIQUE KEY uq_users_github_id (github_id)
            )
            """
        )

        # --------------------------------------------------------
        # APPLICATIONS
        # --------------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS applications (
                id BIGINT NOT NULL AUTO_INCREMENT,
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

                PRIMARY KEY (id),

                KEY idx_applications_user_id (user_id),

                CONSTRAINT fk_applications_user
                    FOREIGN KEY (user_id)
                    REFERENCES users(id)
                    ON DELETE CASCADE
            )
            """
        )

        # --------------------------------------------------------
        # INCIDENTS
        # --------------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS incidents (
                id BIGINT NOT NULL AUTO_INCREMENT,

                application_id BIGINT NOT NULL,
                user_id BIGINT NOT NULL,

                service VARCHAR(255) NOT NULL,

                latency_ms DOUBLE,
                error_rate DOUBLE,

                db_connections INT,
                db_connection_limit INT,

                cpu DOUBLE,
                memory DOUBLE,

                status VARCHAR(50) NOT NULL
                    DEFAULT 'INVESTIGATING',

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

                PRIMARY KEY (id),

                KEY idx_incidents_application_id (
                    application_id
                ),

                KEY idx_incidents_user_id (
                    user_id
                ),

                KEY idx_incidents_status (
                    status
                ),

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

        # --------------------------------------------------------
        # RECOVERY ACTIONS
        # --------------------------------------------------------

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS recovery_actions (
                id BIGINT NOT NULL AUTO_INCREMENT,

                incident_id BIGINT NOT NULL,

                action_type VARCHAR(100) NOT NULL,
                action_description TEXT NOT NULL,

                target VARCHAR(255),

                status VARCHAR(50) NOT NULL
                    DEFAULT 'PENDING_APPROVAL',

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

                PRIMARY KEY (id),

                KEY idx_recovery_incident_id (
                    incident_id
                ),

                KEY idx_recovery_approver (
                    approved_by
                ),

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

        print("====================================")
        print("DATABASE INITIALIZATION")
        print("====================================")
        print("Database schema verified successfully.")
        print("Users table: ready")
        print("Applications table: ready")
        print("Incidents table: ready")
        print("Recovery actions table: ready")
        print("====================================")

    except Exception:
        connection.rollback()
        raise

    finally:
        cursor.close()
        connection.close()


# ============================================================
# GITHUB USER
# ============================================================

def save_or_update_github_user(github_user):

    connection = get_connection()
    cursor = connection.cursor()

    try:

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

        row = cursor.fetchone()

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

    finally:

        cursor.close()
        connection.close()