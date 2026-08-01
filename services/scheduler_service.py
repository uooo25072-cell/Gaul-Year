import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from config import config
from repositories.orders import OrderRepository
from repositories.settings import SettingsRepository
from services.ton_service import TonService
from services.payment_service import PaymentService

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()

async def check_expired_orders(bot: Bot):
    """Check for orders past their 20-minute payment deadline."""
    try:
        expired_orders = await OrderRepository.get_expired_orders()
        for order in expired_orders:
            # Skip if status is not pending_payment
            if order["status"] != "pending_payment":
                continue

            order_number = order["order_number"]
            payment_method = order["payment_method"]

            if payment_method == "ton":
                # Final automated verification check for TON
                is_paid, msg = await PaymentService.process_ton_verification(bot, order, config.ADMIN_ID)
                if is_paid:
                    logger.info(f"Order {order_number} was paid just in time during expiration check!")
                    continue

            # Mark order as expired
            await OrderRepository.update_status(order["id"], "expired")
            logger.info(f"Order {order_number} expired automatically.")

            # Send Notification to User
            try:
                await bot.send_message(
                    chat_id=order["user_id"],
                    text=(
                        f"❌ <b>انتهت مهلة الدفع (20 دقيقة) للطلب {order_number}</b>\n\n"
                        f"لم يتم العثور على عملية دفع مطابقة قبل انتهاء الوقت.\n"
                        f"تم إلغاء الطلب تلقائيًا. يمكنك إنشاء طلب جديد في أي وقت."
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send expiration message to user {order['user_id']}: {e}")

            # Send Notification to Admin
            if config.ADMIN_ID:
                try:
                    await bot.send_message(
                        chat_id=config.ADMIN_ID,
                        text=(
                            f"⌛ <b>انتهت مهلة الدفع للطلب:</b> <code>{order_number}</code>\n"
                            f"👤 <b>المستخدم ID:</b> <code>{order['user_id']}</code>\n"
                            f"💰 <b>المبلغ:</b> {order['price_egp']} جنيه ({payment_method})"
                        )
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin of expired order {order_number}: {e}")

    except Exception as e:
        logger.error(f"Error checking expired orders: {e}")

async def update_ton_price_job():
    """Periodically update TON price in EGP."""
    try:
        await TonService.update_ton_rate()
    except Exception as e:
        logger.error(f"Error in update_ton_price_job: {e}")

def setup_scheduler(bot: Bot):
    """Register all scheduled tasks."""
    scheduler.add_job(
        check_expired_orders,
        "interval",
        seconds=config.PAYMENT_CHECK_INTERVAL,
        args=[bot],
        id="check_expired_orders_job",
        replace_existing=True
    )

    scheduler.add_job(
        update_ton_price_job,
        "interval",
        seconds=config.TON_PRICE_UPDATE_INTERVAL,
        id="update_ton_price_job",
        replace_existing=True
    )

    scheduler.start()
    logger.info("APScheduler initialized and started successfully.")
