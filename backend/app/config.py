import os
from dotenv import load_dotenv

load_dotenv()

# Hindsight
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

# OpenRouter

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