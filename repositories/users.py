from typing import Optional, List, Dict, Any
from database import get_db

class UserRepository:
    @staticmethod
    async def add_or_update_user(telegram_id: int, username: Optional[str], full_name: str) -> Dict[str, Any]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?;", (telegram_id,))
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    "INSERT INTO users (telegram_id, username, full_name) VALUES (?, ?, ?);",
                    (telegram_id, username, full_name)
                )
            else:
                await db.execute(
                    "UPDATE users SET username = ?, full_name = ? WHERE telegram_id = ?;",
                    (username, full_name, telegram_id)
                )
            await db.commit()
            
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?;", (telegram_id,))
            user_row = await cursor.fetchone()
            return dict(user_row) if user_row else {}

    @staticmethod
    async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM users WHERE telegram_id = ?;", (telegram_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def is_banned(telegram_id: int) -> bool:
        async with await get_db() as db:
            cursor = await db.execute("SELECT is_banned FROM users WHERE telegram_id = ?;", (telegram_id,))
            row = await cursor.fetchone()
            return bool(row["is_banned"]) if row else False

    @staticmethod
    async def ban_user(telegram_id: int, reason: str = "") -> bool:
        async with await get_db() as db:
            await db.execute("UPDATE users SET is_banned = 1 WHERE telegram_id = ?;", (telegram_id,))
            await db.execute(
                "INSERT OR REPLACE INTO bans (telegram_id, reason) VALUES (?, ?);",
                (telegram_id, reason)
            )
            await db.commit()
            return True

    @staticmethod
    async def unban_user(telegram_id: int) -> bool:
        async with await get_db() as db:
            await db.execute("UPDATE users SET is_banned = 0 WHERE telegram_id = ?;", (telegram_id,))
            await db.execute("DELETE FROM bans WHERE telegram_id = ?;", (telegram_id,))
            await db.commit()
            return True

    @staticmethod
    async def get_all_users() -> List[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM users ORDER BY created_at DESC;")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def count_users() -> int:
        async with await get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) as count FROM users;")
            row = await cursor.fetchone()
            return row["count"] if row else 0
