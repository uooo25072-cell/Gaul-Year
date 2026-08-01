from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from config import config
from repositories.settings import SettingsRepository

class MaintenanceMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        # Allow admin through regardless of maintenance state
        if user_id == config.ADMIN_ID:
            return await handler(event, data)

        maintenance_mode = await SettingsRepository.get_setting("maintenance_mode", "0")
        if maintenance_mode == "1":
            msg = await SettingsRepository.get_setting(
                "maintenance_message",
                "🛠️ المتجر تحت الصيانة حاليًا.\nنعمل على تحسين الخدمة وسيتم إعادة فتح المتجر قريبًا.\nشكرًا لصبرك ❤️"
            )
            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)
            return

        return await handler(event, data)
