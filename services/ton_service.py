import logging
import json
import asyncio
import urllib.request
from typing import Optional, Dict, Any, Tuple
from repositories.settings import SettingsRepository
from database import get_db

logger = logging.getLogger(__name__)

COINGECKO_TON_URL = "https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=usd"
TONAPI_TX_URL = "https://tonapi.io/v2/blockchain/accounts/{address}/transactions"

def _fetch_url_json_sync(url: str, headers: dict = None, timeout: int = 10) -> Optional[dict]:
    req_headers = {"User-Agent": "Mozilla/5.0"}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.debug(f"HTTP request error for {url}: {e}")
    return None

class TonService:
    @staticmethod
    async def update_ton_rate() -> Dict[str, Any]:
        """Fetch current TON to EGP exchange rate from public API and update DB setting."""
        from datetime import datetime
        now_str = datetime.now().strftime("%Y-%m-%d %I:%M:%S %p")
        egp_rate = 0.0

        try:
            # 1. Fetch TON price in USD
            coingecko_data = await asyncio.to_thread(_fetch_url_json_sync, COINGECKO_TON_URL)
            ton_usd = 0.0
            if coingecko_data:
                ton_usd = coingecko_data.get("the-open-network", {}).get("usd", 0.0)

            # 2. Fetch USD to EGP rate
            er_data = await asyncio.to_thread(_fetch_url_json_sync, "https://open.er-api.com/v6/latest/USD")
            usd_egp = 51.0
            if er_data:
                usd_egp = er_data.get("rates", {}).get("EGP", 51.0)

            if ton_usd > 0:
                egp_rate = round(ton_usd * usd_egp, 2)
                await SettingsRepository.set_setting("ton_egp_rate", str(egp_rate))
                await SettingsRepository.set_setting("ton_rate_updated_at", now_str)
                logger.info(f"Updated TON/EGP rate: {egp_rate} at {now_str}")
                return {"rate": egp_rate, "updated_at": now_str, "success": True}
        except Exception as e:
            logger.warning(f"Could not fetch TON price from API: {e}")

        # Fallback to existing setting or default 120 EGP / TON
        saved_rate = await SettingsRepository.get_setting("ton_egp_rate", "120.0")
        saved_time = await SettingsRepository.get_setting("ton_rate_updated_at", "غير معروف")
        try:
            rate_val = float(saved_rate)
        except ValueError:
            rate_val = 120.0

        return {"rate": rate_val, "updated_at": saved_time, "success": False}

    @staticmethod
    async def get_ton_rate() -> float:
        saved_rate = await SettingsRepository.get_setting("ton_egp_rate", "120.0")
        try:
            return float(saved_rate)
        except ValueError:
            return 120.0

    @staticmethod
    async def calculate_ton_amount(price_egp: float) -> float:
        rate = await TonService.get_ton_rate()
        if rate <= 0:
            rate = 120.0
        amount = price_egp / rate
        return round(amount, 4)

    @staticmethod
    async def is_tx_hash_used(tx_hash: str) -> bool:
        async with await get_db() as db:
            cursor = await db.execute("SELECT id FROM transactions WHERE tx_hash = ?;", (tx_hash,))
            row = await cursor.fetchone()
            return row is not None

    @staticmethod
    async def register_transaction(order_id: int, tx_hash: str, amount_ton: float, sender_address: str = "") -> bool:
        async with await get_db() as db:
            try:
                await db.execute(
                    "INSERT INTO transactions (order_id, tx_hash, amount_ton, sender_address) VALUES (?, ?, ?, ?);",
                    (order_id, tx_hash, amount_ton, sender_address)
                )
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error registering transaction hash: {e}")
                return False

    @staticmethod
    async def check_onchain_payment(wallet_address: str, expected_memo: str, expected_ton: float) -> Tuple[bool, Optional[str]]:
        """
        Query TON RPC / API for incoming transactions matching the wallet address, memo, and TON amount.
        Returns (is_found, tx_hash)
        """
        url = TONAPI_TX_URL.format(address=wallet_address)
        try:
            data = await asyncio.to_thread(_fetch_url_json_sync, url, {"User-Agent": "Mozilla/5.0"}, 12)
            if data:
                transactions = data.get("transactions", [])
                for tx in transactions:
                    tx_hash = tx.get("hash", "")
                    if not tx_hash:
                        continue
                    
                    in_msg = tx.get("in_msg", {})
                    if not in_msg:
                        continue
                    
                    comment = ""
                    decoded_body = in_msg.get("decoded_body")
                    if isinstance(decoded_body, dict):
                        comment = decoded_body.get("text", "") or ""
                    if not comment:
                        comment = in_msg.get("message", "") or ""
                        
                    if expected_memo and expected_memo.strip().lower() in comment.strip().lower():
                        value_nanotons = int(in_msg.get("value", 0))
                        value_ton = value_nanotons / 1e9
                        
                        if abs(value_ton - expected_ton) <= 0.05 or value_ton >= expected_ton:
                            if not await TonService.is_tx_hash_used(tx_hash):
                                logger.info(f"Verified TON payment tx: {tx_hash} for memo: {expected_memo}")
                                return True, tx_hash
        except Exception as e:
            logger.error(f"TON on-chain check error: {e}")

        return False, None
