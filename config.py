import os
import logging
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    if os.path.exists(".env"):
        try:
            with open(".env", "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip())
        except Exception:
            pass

@dataclass
class Config:
    BOT_TOKEN: str
    ADMIN_ID: int
    TON_API_KEY: str
    TON_WALLET_ADDRESS: str
    TON_PRICE_UPDATE_INTERVAL: int
    PAYMENT_TIMEOUT_MINUTES: int
    PAYMENT_CHECK_INTERVAL: int
    DATABASE_PATH: str
    LOG_LEVEL: str

def load_config() -> Config:
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    admin_id_raw = os.getenv("ADMIN_ID", "0").strip()
    try:
        admin_id = int(admin_id_raw) if admin_id_raw else 0
    except ValueError:
        admin_id = 0

    return Config(
        BOT_TOKEN=bot_token,
        ADMIN_ID=admin_id,
        TON_API_KEY=os.getenv("TON_API_KEY", "").strip(),
        TON_WALLET_ADDRESS=os.getenv("TON_WALLET_ADDRESS", "UQAerMfM0XruMQmynNMjIuKP7zu4AeMrVlUBRJgtxARyLq_H").strip(),
        TON_PRICE_UPDATE_INTERVAL=int(os.getenv("TON_PRICE_UPDATE_INTERVAL", "3600")),
        PAYMENT_TIMEOUT_MINUTES=int(os.getenv("PAYMENT_TIMEOUT_MINUTES", "20")),
        PAYMENT_CHECK_INTERVAL=int(os.getenv("PAYMENT_CHECK_INTERVAL", "10")),
        DATABASE_PATH=os.getenv("DATABASE_PATH", "data/gamezone.db").strip(),
        LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO").strip()
    )

config = load_config()

def setup_logging():
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
