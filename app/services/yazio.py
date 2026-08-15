import json
import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

import httpx

from app.config import settings
from app.db import YazioTokensRepository

logger = logging.getLogger(__name__)

# Official Yazio iOS client credentials (public, extractable from any Yazio app instance)
YAZIO_CLIENT_ID = "3_5rbw4kehpugw8ogsc8ck8oo4ogswgckcskc04gcg8kk8k48ssw"
YAZIO_CLIENT_SECRET = "25gdtt1hvdi8gwowoww4oo88sgsw0oo04o0og0kkgwwks8k0k"

# How early before actual expiry we consider the token "stale" and refresh preemptively
REFRESH_LEEWAY = timedelta(minutes=5)


class YazioService:
    def __init__(self) -> None:
        self._tokens_repo = YazioTokensRepository()

    def _headers(self, access_token: str, content_type: str) -> dict:
        h = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": content_type,
            "User-Agent": settings.yazio_user_agent,
        }
        if settings.yazio_notification_token:
            h["x-yazio-notification-token"] = settings.yazio_notification_token
        return h

    async def _get_access_token(self) -> str:
        """Get current access_token, refreshing if expired or near expiry."""
        tokens = await self._tokens_repo.get()

        if tokens is None:
            # Bootstrap: no tokens in DB yet, seed from .env
            logger.info("No tokens in DB — seeding from .env bearer token")
            # We don't have refresh_token from .env, so store access only.
            # On next 401 we'll be forced to reseed manually (which is current behavior anyway).
            seed_expires_at = datetime.now(UTC) + timedelta(hours=1)
            await self._tokens_repo.upsert(
                access_token=settings.yazio_bearer_token,
                refresh_token="",
                expires_at=seed_expires_at,
            )
            return settings.yazio_bearer_token

        now = datetime.now(UTC)
        if tokens["expires_at"] - REFRESH_LEEWAY <= now and tokens["refresh_token"]:
            logger.info("Access token near expiry — refreshing")
            return await self._refresh(tokens["refresh_token"])

        return tokens["access_token"]

    async def _refresh(self, refresh_token: str) -> str:
        """Call /oauth/token to get a fresh access_token + rotated refresh_token."""
        url = f"{settings.yazio_base_url}/oauth/token"
        payload = {
            "client_id": YAZIO_CLIENT_ID,
            "client_secret": YAZIO_CLIENT_SECRET,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": settings.yazio_user_agent,
        }

        async with httpx.AsyncClient(timeout=settings.request_timeout, http2=True) as client:
            resp = await client.post(url, headers=headers, json=payload)

        if resp.status_code >= 400:
            logger.error("Yazio refresh failed: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()

        data = resp.json()
        new_access = data["access_token"]
        new_refresh = data.get("refresh_token", refresh_token)
        expires_in = int(data.get("expires_in", 172800))
        new_expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        await self._tokens_repo.upsert(
            access_token=new_access,
            refresh_token=new_refresh,
            expires_at=new_expires_at,
        )
        logger.info("Yazio token refreshed, expires at %s", new_expires_at.isoformat())
        return new_access

    async def _request(
        self,
        method: str,
        url: str,
        *,
        content_type: str,
        body: Any = None,
    ) -> httpx.Response:
        """Make an authenticated request, transparently refreshing on 401."""
        access_token = await self._get_access_token()

        async with httpx.AsyncClient(timeout=settings.request_timeout, http2=True) as client:
            kwargs = {"headers": self._headers(access_token, content_type)}
            if content_type == "application/json" and body is not None:
                kwargs["json"] = body
            elif body is not None:
                kwargs["content"] = body

            resp = await client.request(method, url, **kwargs)

            # If unauthorized, try refresh once and retry
            if resp.status_code == 401:
                logger.warning("Got 401 — attempting token refresh and retry")
                tokens = await self._tokens_repo.get()
                if tokens and tokens["refresh_token"]:
                    new_access = await self._refresh(tokens["refresh_token"])
                    kwargs["headers"] = self._headers(new_access, content_type)
                    resp = await client.request(method, url, **kwargs)

        return resp

    async def create_consumed_item(self, meal: dict, daytime: str) -> tuple[str, dict]:
        remote_id = str(uuid4()).upper()
        payload = {
            "products": [],
            "recipe_portions": [],
            "simple_products": [
                {
                    "name": meal["description"],
                    "id": remote_id,
                    "date": meal["consumed_at"].strftime("%Y-%m-%d %H:%M:%S"),
                    "nutrients": {
                        "energy.energy": round(float(meal["calories"]), 1),
                        "nutrient.carb": round(float(meal["carbs"]), 1),
                        "nutrient.fat": round(float(meal["fat"]), 1),
                        "nutrient.protein": round(float(meal["protein"]), 1),
                    },
                    "daytime": daytime,
                    "is_ai_generated": False,
                }
            ],
        }

        logger.info("Yazio payload: %s", json.dumps(payload))
        resp = await self._request(
            "POST",
            f"{settings.yazio_base_url}/user/consumed-items",
            content_type="application/json",
            body=payload,
        )
        if resp.status_code >= 400:
            logger.error("Yazio create failed: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()

        return remote_id.lower(), payload

    async def delete_consumed_item(self, remote_id: str) -> None:
        resp = await self._request(
            "DELETE",
            f"{settings.yazio_base_url}/user/consumed-items",
            content_type="text/plain; charset=UTF-8",
            body=json.dumps([remote_id.lower()]),
        )
        if resp.status_code >= 400:
            logger.error("Yazio delete failed: %s %s", resp.status_code, resp.text)
            resp.raise_for_status()


yazio_service = YazioService()
