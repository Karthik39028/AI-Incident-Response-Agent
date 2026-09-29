import requests

from app.config import (
    HINDSIGHT_BASE_URL,
    HINDSIGHT_BANK_ID,
    HINDSIGHT_API_KEY,
)


class HindsightService:

    def __init__(self):
        if not HINDSIGHT_API_KEY:
            raise ValueError("HINDSIGHT_API_KEY is not configured")

        self.base_url = HINDSIGHT_BASE_URL.rstrip("/")
        self.bank_id = HINDSIGHT_BANK_ID

        self.headers = {
            "Authorization": f"Bearer {HINDSIGHT_API_KEY}",
            "Content-Type": "application/json",
        }

        self.timeout = 30

    def retain(self, content: str):
        """
        Store confirmed incident/recovery experience in Hindsight.

        This should be called only after the system has enough evidence
        to treat the outcome as a confirmed learning experience.
        """

        if not content or not content.strip():
            raise ValueError("Hindsight retain content cannot be empty")

        url = (
            f"{self.base_url}/v1/default/banks/"
            f"{self.bank_id}/memories"
        )

        payload = {
            "items": [
                {
                    "content": content.strip(),
                }
            ]
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Hindsight retain request failed: {exc}"
            ) from exc

    def recall(self, query: str):
        """
        Retrieve relevant historical incident/recovery experience
        from Hindsight before the AI makes a diagnosis.
        """

        if not query or not query.strip():
            raise ValueError("Hindsight recall query cannot be empty")

        url = (
            f"{self.base_url}/v1/default/banks/"
            f"{self.bank_id}/memories/recall"
        )

        payload = {
            "query": query.strip(),
        }

        try:
            response = requests.post(
                url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout,
            )

            response.raise_for_status()

            return response.json()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"Hindsight recall request failed: {exc}"
            ) from exc