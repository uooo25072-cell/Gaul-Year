import logging
from typing import Tuple, Optional, Dict, Any
from aiogram import Bot
from repositories.orders import OrderRepository
from repositories.settings import SettingsRepository
from services.ton_service import TonService
from utils.formatters import get_arabic_status

logger = logging.getLogger(__name__)

class PaymentService:
    @staticmethod
    async def process_ton_verification(bot: Bot, order: Dict[str, Any], admin_id: int) -> Tuple[bool, str]:
        """Verify TON payment on-chain for a given order."""
        if order["status"] != "pending_payment":
            return False, "الطلب ليس في حالة انتظار الدفع."

        wallet_address = await SettingsRepository.get_setting("ton_wallet")
        memo = order.get("memo")
        expected_ton = order.get("ton_amount", 0.0)

        if not wallet_address or not memo:
            return False, "بيانات المحفظة أو الميمو غير متوفرة."

        is_found, tx_hash = await TonService.check_onchain_payment(wallet_address, memo, expected_ton)

        if is_found and tx_hash:
            # Save tx hash and update status
            await TonService.register_transaction(order["id"], tx_hash, expected_ton)
            await OrderRepository.attach_tx_hash(order["id"], tx_hash)
            await OrderRepository.update_status(order["id"], "payment_confirmed")

            # Notify User
            try:
                await bot.send_message(
                    chat_id=order["user_id"],
                    text=(
                        f"✅ <b>تم التحقق من وصول دفعتك بنجاح!</b>\n\n"
                        f"🧾 <b>رقم الطلب:</b> <code>{order['order_number']}</code>\n"
                        f"📦 طلبك الآن قيد التنفيذ وسيتم شحنه يدويًا."
                    )
                )
            except Exception as e:
                logger.error(f"Failed to send confirmation to user: {e}")

            # Notify Admin
            if admin_id:
                try:
                    from keyboards.admin import get_order_action_keyboard
                    admin_text = (
                        f"🪙 <b>دفع جديد مؤكد تلقائيًا عبر TONKeeper!</b>\n\n"
                        f"🧾 <b>رقم الطلب:</b> <code>{order['order_number']}</code>\n"
                        f"🎮 <b>المنتج:</b> {order['product_name']}\n"
                        f"💎 <b>الباقة:</b> {order['package_name']}\n"
                        f"🆔 <b>البيانات:</b> <code>{order['customer_data']}</code>\n"
                        f"💰 <b>السعر:</b> {order['price_egp']} جنيه ({order['ton_amount']} TON)\n"
                        f"🔗 <b>Tx Hash:</b> <code>{tx_hash}</code>"
                    )
                    await bot.send_message(
                        chat_id=admin_id,
                        text=admin_text,
                        reply_markup=get_order_action_keyboard(order["order_number"], "payment_confirmed")
                    )
                except Exception as e:
                    logger.error(f"Failed to notify admin about TON payment: {e}")

            return True, "تم العثور على الدفع وتأكيد الطلب."
        
        return False, "لم يتم العثور على عملية دفع مطابقة على الشبكة حتى الآن."
