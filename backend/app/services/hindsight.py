import requests

from app.config import (
    HINDSIGHT_BASE_URL,
    HINDSIGHT_BANK_ID,
    HINDSIGHT_API_KEY
)


class HindsightService:

    def __init__(self):
        if not HINDSIGHT_API_KEY:
            raise ValueError("HINDSIGHT_API_KEY is not configured")

        self.base_url = HINDSIGHT_BASE_URL
        self.bank_id = HINDSIGHT_BANK_ID

        self.headers = {
            "Authorization": f"Bearer {HINDSIGHT_API_KEY}",
            "Content-Type": "application/json"
        }

    def retain(self, content: str):

        url = (
            f"{self.base_url}/v1/default/banks/"
            f"{self.bank_id}/memories"
        )

        payload = {
            "items": [
                {
                    "content": content
                }
            ]
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload
        )

        response.raise_for_status()

        return response.json()

    def recall(self, query: str):

        url = (
            f"{self.base_url}/v1/default/banks/"
            f"{self.bank_id}/memories/recall"
        )

        payload = {
            "query": query
        }

        response = requests.post(
            url,
            headers=self.headers,
            json=payload
        )

        response.raise_for_status()

        return response.json()