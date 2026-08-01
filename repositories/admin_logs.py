from typing import List, Dict, Any, Optional
from database import get_db

class AdminLogRepository:
    @staticmethod
    async def log_action(admin_id: int, action: str, order_number: Optional[str] = None, details: Optional[str] = None) -> bool:
        async with await get_db() as db:
            await db.execute(
                "INSERT INTO admin_logs (admin_id, action, order_number, details) VALUES (?, ?, ?, ?);",
                (admin_id, action, order_number, details)
            )
            await db.commit()
            return True

    @staticmethod
    async def get_recent_logs(limit: int = 50) -> List[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM admin_logs ORDER BY created_at DESC LIMIT ?;", (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
