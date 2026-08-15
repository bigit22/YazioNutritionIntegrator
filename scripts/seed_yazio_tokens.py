"""
One-time script to seed Yazio tokens into the DB.

Usage:
    python scripts/seed_yazio_tokens.py <access_token> <refresh_token> [expires_in_seconds]

After running once, the bot will auto-refresh tokens indefinitely
(as long as the refresh_token doesn't get invalidated by Yazio).
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta

from app.db import YazioTokensRepository, close_db, init_db


async def main() -> None:
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)

    access_token = sys.argv[1]
    refresh_token = sys.argv[2]
    expires_in = int(sys.argv[3]) if len(sys.argv) > 3 else 172800  # default 48h

    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

    await init_db()
    try:
        repo = YazioTokensRepository()
        await repo.upsert(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        print(f"✅ Tokens seeded. Expires at: {expires_at.isoformat()}")
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
