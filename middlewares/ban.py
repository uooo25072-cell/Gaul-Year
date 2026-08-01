from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from repositories.users import UserRepository

class BanMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        user_id = None
        if isinstance(event, (Message, CallbackQuery)) and event.from_user:
            user_id = event.from_user.id

        if user_id:
            if await UserRepository.is_banned(user_id):
                if isinstance(event, Message):
                    await event.answer("🚫 <b>حسابك محظور من استخدام هذا البوت.</b>")
                elif isinstance(event, CallbackQuery):
                    await event.answer("🚫 حسابك محظور من استخدام البوت.", show_alert=True)
                return

        return await handler(event, data)
