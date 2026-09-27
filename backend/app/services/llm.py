import requests

from app.config import (
    OPENROUTER_BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL
)


class LLMService:

    def __init__(self):

        if not OPENROUTER_API_KEY:
            raise ValueError(
                "OPENROUTER_API_KEY is not configured"
            )

        self.url = (
            f"{OPENROUTER_BASE_URL}/chat/completions"
        )

        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }

        self.model = OPENROUTER_MODEL

    def analyze(self, system_prompt: str, user_prompt: str):

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            "temperature": 0.2
        }

        response = requests.post(
            self.url,
            headers=self.headers,
            json=payload,
            timeout=60
        )

        response.raise_for_status()

        data = response.json()

        return data["choices"][0]["message"]["content"]