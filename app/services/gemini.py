import base64
import json

import httpx

from app.config import settings
from app.models import NutritionResult

SYSTEM_PROMPT = """
You are a nutrition assistant.

Analyze the meal from the provided image and/or user text.
Return ONLY valid JSON, no markdown, no explanations.

Schema:
{
  "description": "short meal name",
  "calories": 0,
  "protein": 0,
  "fat": 0,
  "carbs": 0,
  "portion_grams": 0,
  "items": ["item 1", "item 2"]
}

Rules:
- Values are for the whole portion.
- If weight is unknown, estimate realistically.
- If only text is provided, estimate from text.
- description must be short and suitable for a meal log.
- items should contain visible or clearly mentioned components.
- If some value is uncertain, still provide your best estimate.
"""


class GeminiService:
    def __init__(self) -> None:
        self._api_key = settings.gemini_api_key
        self._model = settings.gemini_model
        self._timeout = settings.request_timeout

    async def analyze(
            self,
            *,
            user_text: str | None,
            image_bytes: bytes | None = None,
            mime_type: str = "image/jpeg",
    ) -> NutritionResult:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{self._model}:generateContent?key={self._api_key}"
        )

        parts: list[dict] = []

        prompt = "Analyze this food and return JSON."
        if user_text:
            prompt += f"\nUser description: {user_text}"
        else:
            prompt += "\nUser description: none"

        parts.append({"text": prompt})

        if image_bytes is not None:
            parts.append(
                {
                    "inline_data": {
                        "mime_type": mime_type,
                        "data": base64.b64encode(image_bytes).decode("utf-8"),
                    }
                }
            )

        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}],
            },
            "contents": [
                {
                    "role": "user",
                    "parts": parts,
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as exc:
            raise ValueError(f"Unexpected Gemini response: {data}") from exc

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:].strip()

        parsed = json.loads(cleaned)
        return NutritionResult.model_validate(parsed)


gemini_service = GeminiService()
