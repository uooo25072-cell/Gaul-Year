import os
import sqlite3
import asyncio
import logging
from typing import AsyncGenerator, Optional, List, Dict, Any
from contextlib import asynccontextmanager
from config import config

logger = logging.getLogger(__name__)

class AsyncDbCursor:
    def __init__(self, cursor: sqlite3.Cursor):
        self._cursor = cursor

    async def fetchone(self) -> Optional[Dict[str, Any]]:
        row = await asyncio.to_thread(self._cursor.fetchone)
        return dict(row) if row else None

    async def fetchall(self) -> List[Dict[str, Any]]:
        rows = await asyncio.to_thread(self._cursor.fetchall)
        return [dict(r) for r in rows]

    @property
    def lastrowid(self) -> Optional[int]:
        return self._cursor.lastrowid

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

class AsyncDbConnection:
    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await asyncio.to_thread(self._conn.rollback)
        else:
            await asyncio.to_thread(self._conn.commit)
        await asyncio.to_thread(self._conn.close)

    async def execute(self, sql: str, parameters=()):
        cursor = await asyncio.to_thread(self._conn.execute, sql, parameters)
        return AsyncDbCursor(cursor)

    async def commit(self):
        await asyncio.to_thread(self._conn.commit)

    async def rollback(self):
        await asyncio.to_thread(self._conn.rollback)

    async def close(self):
        await asyncio.to_thread(self._conn.close)

async def get_db() -> AsyncDbConnection:
    """Get connected SQLite session."""
    db_path = config.DATABASE_PATH
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = await asyncio.to_thread(lambda: sqlite3.connect(db_path, check_same_thread=False))
    conn.row_factory = sqlite3.Row
    await asyncio.to_thread(conn.execute, "PRAGMA foreign_keys = ON;")
    return AsyncDbConnection(conn)

@asynccontextmanager
async def db_transaction() -> AsyncGenerator[AsyncDbConnection, None]:
    """Async context manager for DB transactions."""
    conn = await get_db()
    try:
        yield conn
        await conn.commit()
    except Exception as e:
        await conn.rollback()
        raise e
    finally:
        await conn.close()

async def init_db():
    """Create all required database tables and seed initial products and settings."""
    async with await get_db() as db:
        # 1. Users table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            is_banned INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Products table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            data_label TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        );
        """)

        # 3. Packages table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_key TEXT NOT NULL,
            name TEXT NOT NULL,
            price_egp REAL NOT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (product_key) REFERENCES products(key) ON DELETE CASCADE
        );
        """)

        # 4. Payment methods table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS payment_methods (
            key TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            is_active INTEGER DEFAULT 1
        );
        """)

        # 5. Settings table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """)

        # 6. Orders table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_number TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            package_id INTEGER NOT NULL,
            product_name TEXT NOT NULL,
            package_name TEXT NOT NULL,
            customer_data TEXT NOT NULL,
            price_egp REAL NOT NULL,
            payment_method TEXT NOT NULL,
            ton_amount REAL DEFAULT 0.0,
            memo TEXT,
            transaction_hash TEXT,
            receipt_file_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending_payment',
            rejection_reason TEXT,
            rating INTEGER,
            rating_comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            payment_deadline TIMESTAMP NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Add migration columns if database already exists
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN rating INTEGER;")
        except Exception:
            pass
        try:
            await db.execute("ALTER TABLE orders ADD COLUMN rating_comment TEXT;")
        except Exception:
            pass

        # 7. Transactions table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER NOT NULL,
            tx_hash TEXT UNIQUE NOT NULL,
            amount_ton REAL NOT NULL,
            sender_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 8. Admin Logs table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            order_number TEXT,
            details TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 9. Bans table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS bans (
            telegram_id INTEGER PRIMARY KEY,
            reason TEXT,
            banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        await db.commit()

        # Seed Default Products
        products_seed = [
            ("pubg", "PUBG Mobile", "Player ID"),
            ("freefire", "Free Fire", "Player ID"),
            ("googleplay", "Google Play US", "الإيميل"),
            ("xbox", "Xbox US", "الإيميل"),
        ]
        for p_key, p_name, p_label in products_seed:
            await db.execute(
                "INSERT OR IGNORE INTO products (key, name, data_label) VALUES (?, ?, ?);",
                (p_key, p_name, p_label)
            )

        # Seed Default Packages
        packages_seed = [
            # PUBG Mobile
            ("pubg", "60 UC", 50.0),
            ("pubg", "325 UC", 250.0),
            ("pubg", "660 UC", 500.0),
            ("pubg", "1800 UC", 1300.0),
            ("pubg", "3850 UC", 2500.0),
            # Free Fire
            ("freefire", "100 Diamonds", 75.0),
            ("freefire", "210 Diamonds", 130.0),
            ("freefire", "530 Diamonds", 295.0),
            ("freefire", "1080 Diamonds", 566.0),
            ("freefire", "2200 Diamonds", 1112.0),
            # Google Play US
            ("googleplay", "Google Play $5", 280.0),
            ("googleplay", "Google Play $15", 800.0),
            ("googleplay", "Google Play $50", 2620.0),
            ("googleplay", "Google Play $100", 5220.0),
            # Xbox US
            ("xbox", "Xbox $10", 503.60),
            ("xbox", "Xbox $15", 745.40),
            ("xbox", "Xbox $20", 987.20),
            ("xbox", "Xbox $25", 1229.0),
            ("xbox", "Xbox $50", 2438.0),
        ]
        for p_key, pkg_name, pkg_price in packages_seed:
            cursor = await db.execute(
                "SELECT id FROM packages WHERE product_key = ? AND name = ?;",
                (p_key, pkg_name)
            )
            row = await cursor.fetchone()
            if not row:
                await db.execute(
                    "INSERT INTO packages (product_key, name, price_egp) VALUES (?, ?, ?);",
                    (p_key, pkg_name, pkg_price)
                )

        # Seed Payment Methods
        payment_methods_seed = [
            ("vodafone", "Vodafone Cash"),
            ("binance", "Binance ID"),
            ("ton", "TONKeeper"),
        ]
        for pm_key, pm_name in payment_methods_seed:
            await db.execute(
                "INSERT OR IGNORE INTO payment_methods (key, name) VALUES (?, ?);",
                (pm_key, pm_name)
            )

        # Seed Settings
        settings_seed = [
            ("maintenance_mode", "0"),
            ("maintenance_message", "🛠️ المتجر تحت الصيانة حاليًا.\nنعمل على تحسين الخدمة وسيتم إعادة فتح المتجر قريبًا.\nشكرًا لصبرك ❤️"),
            ("vodafone_number", "01557535435"),
            ("vodafone_name", "Ahmed"),
            ("binance_id", "1097135483"),
            ("binance_name", "Ahmed10"),
            ("ton_wallet", config.TON_WALLET_ADDRESS),
            ("ton_egp_rate", "120.0"),
        ]
        for s_key, s_val in settings_seed:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?);",
                (s_key, s_val)
            )

        await db.commit()
        logger.info("Database initialized successfully with default seeds.")
