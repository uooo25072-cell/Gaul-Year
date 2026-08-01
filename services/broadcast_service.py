import asyncio
import logging
from typing import Tuple
from aiogram import Bot
from repositories.users import UserRepository

logger = logging.getLogger(__name__)

class BroadcastService:
    @staticmethod
    async def send_broadcast(
        bot: Bot,
        message_type: str,
        content: str, # Text or File ID
        caption: str = ""
    ) -> Tuple[int, int]:
        """Send broadcast message to all non-banned users. Returns (success_count, fail_count)."""
        users = await UserRepository.get_all_users()
        success = 0
        failed = 0

        for user in users:
            if user.get("is_banned"):
                continue

            user_id = user["telegram_id"]
            try:
                if message_type == "text":
                    await bot.send_message(chat_id=user_id, text=content, parse_mode="HTML")
                elif message_type == "photo":
                    await bot.send_photo(chat_id=user_id, photo=content, caption=caption, parse_mode="HTML")
                elif message_type == "video":
                    await bot.send_video(chat_id=user_id, video=content, caption=caption, parse_mode="HTML")
                
                success += 1
                await asyncio.sleep(0.05) # Rate limiting prevention
            except Exception as e:
                logger.warning(f"Failed to send broadcast to {user_id}: {e}")
                failed += 1

        return success, failed
