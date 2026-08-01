from typing import Dict, Optional
from database import get_db

class SettingsRepository:
    @staticmethod
    async def get_setting(key: str, default: str = "") -> str:
        async with await get_db() as db:
            cursor = await db.execute("SELECT value FROM settings WHERE key = ?;", (key,))
            row = await cursor.fetchone()
            return row["value"] if row else default

    @staticmethod
    async def set_setting(key: str, value: str) -> bool:
        async with await get_db() as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);",
                (key, value)
            )
            await db.commit()
            return True

    @staticmethod
    async def get_all_settings() -> Dict[str, str]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT key, value FROM settings;")
            rows = await cursor.fetchall()
            return {r["key"]: r["value"] for r in rows}
