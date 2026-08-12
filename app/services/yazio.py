import json
from uuid import uuid4

import httpx

from app.config import settings


class YazioService:
    def _headers(self, content_type: str) -> dict:
        h = {"Authorization": f"Bearer {settings.yazio_bearer_token}", "Content-Type": content_type,
             "User-Agent": settings.yazio_user_agent}
        if settings.yazio_notification_token: h["x-yazio-notification-token"] = settings.yazio_notification_token
        return h

    async def create_consumed_item(self, meal: dict, daytime: str) -> tuple[str, dict]:
        remote_id = str(uuid4()).upper()
        payload = {
            "products": [], "recipe_portions": [],
            "simple_products": [{
                "name": meal["description"], "id": remote_id,
                "date": meal["consumed_at"].strftime("%Y-%m-%d %H:%M:%S"),
                "nutrients": {
                    "energy.energy": round(float(meal["calories"]), 1),
                    "nutrient.carb": round(float(meal["carbs"]), 1),
                    "nutrient.fat": round(float(meal["fat"]), 1),
                    "nutrient.protein": round(float(meal["protein"]), 1),
                },
                "daytime": daytime, "is_ai_generated": False
            }]
        }
        async with httpx.AsyncClient(timeout=settings.request_timeout, http2=True) as client:
            resp = await client.post(f"{settings.yazio_base_url}/user/consumed-items",
                                     headers=self._headers("application/json"), json=payload)
            resp.raise_for_status()
        return remote_id.lower(), payload

    async def delete_consumed_item(self, remote_id: str) -> None:
        async with httpx.AsyncClient(timeout=settings.request_timeout, http2=True) as client:
            resp = await client.request("DELETE", f"{settings.yazio_base_url}/user/consumed-items",
                                        headers=self._headers("text/plain; charset=UTF-8"),
                                        content=json.dumps([remote_id.lower()]))
            resp.raise_for_status()


yazio_service = YazioService()
