from typing import List, Optional, Dict, Any
from database import get_db

class ProductRepository:
    @staticmethod
    async def get_all_products(active_only: bool = True) -> List[Dict[str, Any]]:
        async with await get_db() as db:
            query = "SELECT * FROM products"
            if active_only:
                query += " WHERE is_active = 1"
            query += " ORDER BY id ASC;"
            cursor = await db.execute(query)
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def get_product_by_key(key: str) -> Optional[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM products WHERE key = ?;", (key,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def get_packages_by_product_key(product_key: str, active_only: bool = True) -> List[Dict[str, Any]]:
        async with await get_db() as db:
            query = "SELECT * FROM packages WHERE product_key = ?"
            if active_only:
                query += " AND is_active = 1"
            query += " ORDER BY price_egp ASC;"
            cursor = await db.execute(query, (product_key,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def get_package_by_id(package_id: int) -> Optional[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM packages WHERE id = ?;", (package_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def add_package(product_key: str, name: str, price_egp: float) -> int:
        async with await get_db() as db:
            cursor = await db.execute(
                "INSERT INTO packages (product_key, name, price_egp) VALUES (?, ?, ?);",
                (product_key, name, price_egp)
            )
            await db.commit()
            return cursor.lastrowid

    @staticmethod
    async def update_package(package_id: int, name: str, price_egp: float, is_active: int = 1) -> bool:
        async with await get_db() as db:
            await db.execute(
                "UPDATE packages SET name = ?, price_egp = ?, is_active = ? WHERE id = ?;",
                (name, price_egp, is_active, package_id)
            )
            await db.commit()
            return True

    @staticmethod
    async def delete_package(package_id: int) -> bool:
        async with await get_db() as db:
            await db.execute("DELETE FROM packages WHERE id = ?;", (package_id,))
            await db.commit()
            return True

    @staticmethod
    async def toggle_package_status(package_id: int) -> bool:
        async with await get_db() as db:
            cursor = await db.execute("SELECT is_active FROM packages WHERE id = ?;", (package_id,))
            row = await cursor.fetchone()
            if row:
                new_status = 0 if row["is_active"] else 1
                await db.execute("UPDATE packages SET is_active = ? WHERE id = ?;", (new_status, package_id))
                await db.commit()
                return True
            return False
