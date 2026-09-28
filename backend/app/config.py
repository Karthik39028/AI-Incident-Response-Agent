import os
from dotenv import load_dotenv
import os
from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "incident_response")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")

load_dotenv()


# --------------------------------------------------
# HINDSIGHT
# --------------------------------------------------

HINDSIGHT_BASE_URL = os.getenv(
    "HINDSIGHT_BASE_URL",
    "https://api.hindsight.vectorize.io"
)

HINDSIGHT_BANK_ID = os.getenv(
    "HINDSIGHT_BANK_ID",
    "incident-response-agent"
)

HINDSIGHT_API_KEY = os.getenv(
    "HINDSIGHT_API_KEY"
)


# --------------------------------------------------
# OPENROUTER
# --------------------------------------------------

OPENROUTER_BASE_URL = os.getenv(
    "OPENROUTER_BASE_URL",
    "https://openrouter.ai/api/v1"
)

OPENROUTER_API_KEY = os.getenv(
    "OPENROUTER_API_KEY"
)

OPENROUTER_MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "openrouter/free"
)


# --------------------------------------------------
# GITHUB
# --------------------------------------------------

GITHUB_CLIENT_ID = os.getenv(
    "GITHUB_CLIENT_ID"
)

GITHUB_CLIENT_SECRET = os.getenv(
    "GITHUB_CLIENT_SECRET"
)

GITHUB_REDIRECT_URI = os.getenv(
    "GITHUB_REDIRECT_URI",
    "http://localhost:8081/auth/github/callback"
)


# --------------------------------------------------
# FRONTEND
# --------------------------------------------------

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173"
)