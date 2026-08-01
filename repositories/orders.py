from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from database import get_db

ACTIVE_STATUSES = ["pending_payment", "payment_review", "payment_confirmed", "processing"]

class OrderRepository:
    @staticmethod
    async def get_active_user_order(user_id: int) -> Optional[Dict[str, Any]]:
        async with await get_db() as db:
            placeholders = ",".join(["?"] * len(ACTIVE_STATUSES))
            query = f"SELECT * FROM orders WHERE user_id = ? AND status IN ({placeholders}) ORDER BY created_at DESC LIMIT 1;"
            cursor = await db.execute(query, [user_id] + ACTIVE_STATUSES)
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def create_order(
        order_number: str,
        user_id: int,
        product_id: int,
        package_id: int,
        product_name: str,
        package_name: str,
        customer_data: str,
        price_egp: float,
        payment_method: str,
        payment_deadline_minutes: int = 20,
        ton_amount: float = 0.0,
        memo: Optional[str] = None
    ) -> Dict[str, Any]:
        deadline = datetime.utcnow() + timedelta(minutes=payment_deadline_minutes)
        async with await get_db() as db:
            cursor = await db.execute(
                """
                INSERT INTO orders (
                    order_number, user_id, product_id, package_id,
                    product_name, package_name, customer_data, price_egp,
                    payment_method, ton_amount, memo, status, payment_deadline
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending_payment', ?);
                """,
                (
                    order_number, user_id, product_id, package_id,
                    product_name, package_name, customer_data, price_egp,
                    payment_method, ton_amount, memo, deadline
                )
            )
            await db.commit()
            order_id = cursor.lastrowid
            
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?;", (order_id,))
            row = await cursor.fetchone()
            return dict(row) if row else {}

    @staticmethod
    async def get_order_by_number(order_number: str) -> Optional[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM orders WHERE order_number = ?;", (order_number,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def get_order_by_id(order_id: int) -> Optional[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM orders WHERE id = ?;", (order_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    @staticmethod
    async def get_user_orders(user_id: int) -> List[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC;", (user_id,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def update_receipt(order_id: int, receipt_file_id: str) -> bool:
        async with await get_db() as db:
            await db.execute(
                "UPDATE orders SET receipt_file_id = ?, status = 'payment_review', updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (receipt_file_id, order_id)
            )
            await db.commit()
            return True

    @staticmethod
    async def update_status(order_id: int, status: str, rejection_reason: Optional[str] = None) -> bool:
        async with await get_db() as db:
            if rejection_reason is not None:
                await db.execute(
                    "UPDATE orders SET status = ?, rejection_reason = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                    (status, rejection_reason, order_id)
                )
            else:
                await db.execute(
                    "UPDATE orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                    (status, order_id)
                )
            await db.commit()
            return True

    @staticmethod
    async def attach_tx_hash(order_id: int, tx_hash: str) -> bool:
        async with await get_db() as db:
            await db.execute(
                "UPDATE orders SET transaction_hash = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;",
                (tx_hash, order_id)
            )
            await db.commit()
            return True

    @staticmethod
    async def get_pending_ton_orders() -> List[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute(
                "SELECT * FROM orders WHERE payment_method = 'ton' AND status = 'pending_payment';"
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def get_expired_orders() -> List[Dict[str, Any]]:
        async with await get_db() as db:
            now_str = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
            cursor = await db.execute(
                "SELECT * FROM orders WHERE status = 'pending_payment' AND payment_deadline <= ?;",
                (now_str,)
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def get_orders_by_status(status: str) -> List[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT * FROM orders WHERE status = ? ORDER BY created_at DESC;", (status,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def get_all_orders(limit: int = 50) -> List[Dict[str, Any]]:
        async with await get_db() as db:
            cursor = await db.execute("""
                SELECT o.*, u.username, u.full_name, u.is_banned
                FROM orders o
                LEFT JOIN users u ON o.user_id = u.telegram_id
                ORDER BY o.created_at DESC LIMIT ?;
            """, (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    @staticmethod
    async def rate_order(order_number: str, rating: int, comment: Optional[str] = None) -> bool:
        async with await get_db() as db:
            await db.execute(
                "UPDATE orders SET rating = ?, rating_comment = ?, updated_at = CURRENT_TIMESTAMP WHERE order_number = ?;",
                (rating, comment, order_number)
            )
            await db.commit()
            return True

    @staticmethod
    async def get_stats() -> Dict[str, Any]:
        async with await get_db() as db:
            cursor = await db.execute("SELECT COUNT(*) as cnt FROM orders;")
            total_orders = (await cursor.fetchone())["cnt"]

            cursor = await db.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'pending_payment';")
            pending_payment = (await cursor.fetchone())["cnt"]

            cursor = await db.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'payment_review';")
            payment_review = (await cursor.fetchone())["cnt"]

            cursor = await db.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'processing';")
            processing = (await cursor.fetchone())["cnt"]

            cursor = await db.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'completed';")
            completed = (await cursor.fetchone())["cnt"]

            cursor = await db.execute("SELECT COUNT(*) as cnt FROM orders WHERE status = 'rejected';")
            rejected = (await cursor.fetchone())["cnt"]

            cursor = await db.execute("SELECT SUM(price_egp) as total FROM orders WHERE status IN ('payment_confirmed', 'processing', 'completed');")
            sum_row = await cursor.fetchone()
            total_sales = sum_row["total"] if sum_row and sum_row["total"] else 0.0

            today_str = datetime.utcnow().strftime("%Y-%m-%d")
            cursor = await db.execute(
                "SELECT SUM(price_egp) as total FROM orders WHERE status IN ('payment_confirmed', 'processing', 'completed') AND created_at LIKE ?;",
                (f"{today_str}%",)
            )
            today_row = await cursor.fetchone()
            today_sales = today_row["total"] if today_row and today_row["total"] else 0.0

            # Ratings calculations
            cursor = await db.execute("SELECT COUNT(*) as cnt, AVG(rating) as avg_score FROM orders WHERE rating IS NOT NULL;")
            rating_row = await cursor.fetchone()
            total_ratings = rating_row["cnt"] if rating_row and rating_row["cnt"] else 0
            avg_rating = round(rating_row["avg_score"], 1) if rating_row and rating_row["avg_score"] is not None else 0.0

            ratings_breakdown = {}
            for star in range(1, 6):
                cursor = await db.execute("SELECT COUNT(*) as cnt FROM orders WHERE rating = ?;", (star,))
                s_row = await cursor.fetchone()
                ratings_breakdown[str(star)] = s_row["cnt"] if s_row else 0

            return {
                "total_orders": total_orders,
                "pending_payment": pending_payment,
                "payment_review": payment_review,
                "processing": processing,
                "completed": completed,
                "rejected": rejected,
                "total_sales": total_sales,
                "today_sales": today_sales,
                "total_ratings": total_ratings,
                "avg_rating": avg_rating,
                "ratings_breakdown": ratings_breakdown
            }
