import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config, setup_logging
from database import init_db
from middlewares.ban import BanMiddleware
from middlewares.maintenance import MaintenanceMiddleware
from services.scheduler_service import setup_scheduler
from handlers import user, orders, payments, admin

logger = logging.getLogger(__name__)

async def main():
    # Setup structured logging
    setup_logging()
    logger.info("Initializing GameZone Telegram Bot...")

    if not config.BOT_TOKEN:
        logger.error("BOT_TOKEN is not defined in .env! Please set BOT_TOKEN to run the bot.")
        print("\n❌ Error: BOT_TOKEN is missing from .env file!")
        print("Please edit .env and set BOT_TOKEN=your_telegram_bot_token before running main.py\n")

    # Initialize SQLite database schema and initial data
    await init_db()

    # Create Bot & Dispatcher instances
    bot = Bot(token=config.BOT_TOKEN if config.BOT_TOKEN else "7891234567:AAFxExampleTokenHere12345")
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register Middlewares
    dp.update.middleware(BanMiddleware())
    dp.update.middleware(MaintenanceMiddleware())

    # Register Handler Routers in order
    dp.include_router(admin.router)    # Admin commands & callbacks first
    dp.include_router(user.router)     # Start command & navigation
    dp.include_router(orders.router)   # Order creation FSM
    dp.include_router(payments.router) # Payment selection & proof uploading

    # Initialize Background Scheduler (TON Price updates & payment timeouts check)
    setup_scheduler(bot)

    logger.info("GameZone Bot is ready and listening for updates...")

    # Start Polling
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.critical(f"Bot execution stopped due to error: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("GameZone Bot stopped.")
