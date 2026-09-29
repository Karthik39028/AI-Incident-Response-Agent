import requests

from app.config import (
    OPENROUTER_BASE_URL,
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)


class LLMService:

    def __init__(self):
        if not OPENROUTER_API_KEY:
            raise ValueError("OPENROUTER_API_KEY is not configured")

        self.url = f"{OPENROUTER_BASE_URL}/chat/completions"

        self.headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }

        self.model = OPENROUTER_MODEL

    def analyze(
        self,
        system_prompt: str,
        user_prompt: str,
    ):
        payload = {
            "model": self.model,

            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],

            "temperature": 0.1,

            # Ask the model/provider for structured JSON.
            "response_format": {
                "type": "json_object"
            },
        }

        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                timeout=60,
            )

            response.raise_for_status()

        except requests.RequestException as exc:
            raise RuntimeError(
                f"LLM request failed: {exc}"
            ) from exc

        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "LLM provider returned a non-JSON HTTP response."
            ) from exc

        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(
                f"LLM response did not contain the expected "
                f"choices[0].message.content field: {data}"
            ) from exc

        if content is None:
            raise RuntimeError(
                "LLM returned an empty message content."
            )

        return content