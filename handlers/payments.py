import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config
from repositories.orders import OrderRepository
from repositories.products import ProductRepository
from repositories.settings import SettingsRepository
from services.ton_service import TonService
from services.payment_service import PaymentService
from keyboards.user import (
    get_payment_methods_keyboard,
    get_manual_payment_keyboard,
    get_ton_payment_keyboard,
    get_main_menu_keyboard
)
from keyboards.admin import get_order_action_keyboard
from utils.order_id import generate_order_number, generate_memo
from utils.formatters import format_price

router = Router()
logger = logging.getLogger(__name__)

class PaymentState(StatesGroup):
    selecting_method = State()
    waiting_for_proof = State()
    resending_proof = State()

@router.callback_query(F.data == "order:confirm")
async def confirm_order_and_select_payment(callback: CallbackQuery, state: FSMContext):
    """User confirmed order details - prompt for payment method."""
    data = await state.get_data()
    if not data.get("product_id") or not data.get("package_id"):
        await callback.answer("حدث خطأ في جلب بيانات الطلب، يرجى إعادة المحاولة.", show_alert=True)
        return

    # Generate Order Number
    order_number = generate_order_number()
    memo = generate_memo(order_number)

    # Calculate TON amount
    ton_amount = await TonService.calculate_ton_amount(data["price_egp"])

    # Create Order in DB
    order = await OrderRepository.create_order(
        order_number=order_number,
        user_id=callback.from_user.id,
        product_id=data["product_id"],
        package_id=data["package_id"],
        product_name=data["product_name"],
        package_name=data["package_name"],
        customer_data=data["customer_data"],
        price_egp=data["price_egp"],
        payment_method="pending",
        payment_deadline_minutes=config.PAYMENT_TIMEOUT_MINUTES,
        ton_amount=ton_amount,
        memo=memo
    )

    await state.update_data(
        order_number=order_number,
        order_id=order["id"],
        memo=memo,
        ton_amount=ton_amount
    )

    text = (
        f"✅ <b>تم إنشاء طلبك برقم:</b> <code>{order_number}</code>\n\n"
        f"💳 <b>اختر طريقة الدفع المناسبة لك:</b>\n"
        f"⏱️ <b>مهلة الدفع:</b> {config.PAYMENT_TIMEOUT_MINUTES} دقيقة"
    )

    methods = [
        {"key": "vodafone", "name": "Vodafone Cash"},
        {"key": "binance", "name": "Binance ID"},
        {"key": "ton", "name": "TONKeeper"},
    ]

    await callback.message.edit_text(text, reply_markup=get_payment_methods_keyboard(methods), parse_mode="HTML")
    await state.set_state(PaymentState.selecting_method)
    await callback.answer()

@router.callback_query(PaymentState.selecting_method, F.data == "pay:vodafone")
async def pay_vodafone_cash(callback: CallbackQuery, state: FSMContext):
    """Display Vodafone Cash payment instructions."""
    data = await state.get_data()
    order_number = data.get("order_number")

    number = await SettingsRepository.get_setting("vodafone_number", "01557535435")
    name = await SettingsRepository.get_setting("vodafone_name", "Ahmed")

    # Update order payment method
    order = await OrderRepository.get_order_by_number(order_number)
    if order:
        async with await OrderRepository.get_db() as db:
            await db.execute("UPDATE orders SET payment_method = 'vodafone' WHERE id = ?;", (order["id"],))
            await db.commit()

    text = (
        "📱 <b>الدفع عبر Vodafone Cash</b>\n\n"
        f"💰 <b>المبلغ المطلوب:</b> {format_price(data['price_egp'])}\n\n"
        f"📞 <b>رقم التحويل:</b>\n<code>{number}</code>\n\n"
        f"👤 <b>الاسم المسجل:</b>\n<b>{name}</b>\n\n"
        "⚠️ <b>حوّل المبلغ المطلوب بدقة.</b>\n\n"
        "بعد إتمام التحويل، اضغط على <b>✅ تم الدفع</b> لإرسال صورة الإثبات."
    )

    await callback.message.edit_text(text, reply_markup=get_manual_payment_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(PaymentState.selecting_method, F.data == "pay:binance")
async def pay_binance(callback: CallbackQuery, state: FSMContext):
    """Display Binance ID payment instructions."""
    data = await state.get_data()
    order_number = data.get("order_number")

    binance_id = await SettingsRepository.get_setting("binance_id", "1097135483")
    binance_name = await SettingsRepository.get_setting("binance_name", "Ahmed10")

    order = await OrderRepository.get_order_by_number(order_number)
    if order:
        async with await OrderRepository.get_db() as db:
            await db.execute("UPDATE orders SET payment_method = 'binance' WHERE id = ?;", (order["id"],))
            await db.commit()

    text = (
        "🟡 <b>الدفع عبر Binance Pay / ID</b>\n\n"
        f"💰 <b>المبلغ المطلوب:</b> {format_price(data['price_egp'])}\n\n"
        f"🆔 <b>Binance Pay ID:</b>\n<code>{binance_id}</code>\n\n"
        f"👤 <b>الاسم المسجل:</b>\n<b>{binance_name}</b>\n\n"
        "⚠️ <b>حوّل المبلغ المطلوب بدقة.</b>\n\n"
        "بعد إتمام التحويل، اضغط على <b>✅ تم الدفع</b> لإرسال صورة الإثبات."
    )

    await callback.message.edit_text(text, reply_markup=get_manual_payment_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(PaymentState.selecting_method, F.data == "pay:ton")
async def pay_tonkeeper(callback: CallbackQuery, state: FSMContext):
    """Display TONKeeper automated verification payment screen."""
    data = await state.get_data()
    order_number = data.get("order_number")
    memo = data.get("memo")
    ton_amount = data.get("ton_amount", 0.0)

    wallet_address = await SettingsRepository.get_setting("ton_wallet", config.TON_WALLET_ADDRESS)

    order = await OrderRepository.get_order_by_number(order_number)
    if order:
        async with await OrderRepository.get_db() as db:
            await db.execute("UPDATE orders SET payment_method = 'ton' WHERE id = ?;", (order["id"],))
            await db.commit()

    text = (
        "🪙 <b>الدفع عبر شبكة TON (من أي محفظة)</b>\n\n"
        f"💰 <b>المبلغ المطلوب:</b>\n<code>{ton_amount} TON</code>\n\n"
        f"👛 <b>عنوان المحفظة (Address):</b>\n<code>{wallet_address}</code>\n\n"
        f"📝 <b>Memo (ملاحظة التحويل):</b>\n<code>{memo}</code>\n\n"
        "ℹ️ <b>تعليمات التحويل:</b>\n"
        "• يمكنك التحويل من <b>أي محفظة TON</b> (مثل: TONKeeper, Telegram Wallet, OKX, MyTonWallet, Tonhub وغيرها).\n"
        "• قم بنسخ <b>عنوان المحفظة</b> و <b>المبلغ</b> و <b>Memo</b> بدقة إلى أي محفظة تستخدمها.\n"
        "⚠️ <b>تنبيه هام:</b> يرجى عدم نسيان إدخال الـ <b>Memo</b> أثناء التحويل لضمان التعرف التلقائي على الدفعة.\n\n"
        "بعد إتمام التحويل:\n"
        "• يمكنك الضغط على <b>⚡ التحقق التلقائي</b> للتحقق الفوري من الشبكة.\n"
        "• أو اضغط على <b>📸 إرسال صورة إثبات التحويل</b> لإرسال السكرين شوت."
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_ton_payment_keyboard(wallet_address, ton_amount, memo),
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(PaymentState.selecting_method, F.data == "pay:submitted_proof")
async def prompt_proof_photo(callback: CallbackQuery, state: FSMContext):
    """Prompt user to upload payment proof photo."""
    await callback.message.edit_text(
        "📸 <b>يرجى إرسال صورة إثبات التحويل (Screenshot/Receipt):</b>\n\n"
        "تأكد من وضوح قيمة المبلغ ورقم العملية بالصورة.",
        parse_mode="HTML"
    )
    await state.set_state(PaymentState.waiting_for_proof)
    await callback.answer()

@router.message(PaymentState.waiting_for_proof, F.photo)
async def process_proof_photo(message: Message, state: FSMContext, bot: Bot):
    """Handle upload of payment proof screenshot for manual payment."""
    photo = message.photo[-1] # Highest resolution photo
    file_id = photo.file_id

    data = await state.get_data()
    order_number = data.get("order_number")
    order = await OrderRepository.get_order_by_number(order_number)

    if not order:
        await message.answer("عذرًا، لم يتم العثور على الطلب.")
        await state.clear()
        return

    # Update receipt file ID and status
    await OrderRepository.update_receipt(order["id"], file_id)
    await state.clear()

    await message.answer(
        f"🔍 <b>جاري مراجعة الدفع لطلبك #{order_number}</b>\n\n"
        "تم استلام إثبات التحويل بنجاح وسيقوم فريق الدعم بمراجعته وتأكيده في أسرع وقت ممكن.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

    # Notify Admin
    if config.ADMIN_ID:
        try:
            admin_caption = (
                f"📥 <b>إثبات دفع جديد للطلب:</b> <code>{order['order_number']}</code>\n\n"
                f"👤 <b>المستخدم:</b> {message.from_user.full_name} (@{message.from_user.username or 'بدون'})\n"
                f"🆔 <b>Telegram ID:</b> <code>{message.from_user.id}</code>\n"
                f"🎮 <b>المنتج:</b> {order['product_name']}\n"
                f"💎 <b>الباقة:</b> {order['package_name']}\n"
                f"🔑 <b>البيانات:</b> <code>{order['customer_data']}</code>\n"
                f"💰 <b>السعر:</b> {order['price_egp']} جنيه\n"
                f"💳 <b>الطريقة:</b> {order['payment_method'].upper()}"
            )
            await bot.send_photo(
                chat_id=config.ADMIN_ID,
                photo=file_id,
                caption=admin_caption,
                reply_markup=get_order_action_keyboard(order["order_number"], "payment_review"),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to send admin payment review notification: {e}")

@router.callback_query(PaymentState.selecting_method, F.data == "pay:check_ton")
async def manual_check_ton_trigger(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Trigger on-demand check for TON payment."""
    data = await state.get_data()
    order_number = data.get("order_number")
    order = await OrderRepository.get_order_by_number(order_number)

    if not order:
        await callback.answer("الطلب غير موجود.", show_alert=True)
        return

    is_paid, msg = await PaymentService.process_ton_verification(bot, order, config.ADMIN_ID)

    if is_paid:
        await state.clear()
        await callback.message.edit_text(
            f"✅ <b>تم التحقق من وصول دفعتك بنجاح!</b>\n\n"
            f"🧾 <b>رقم الطلب:</b> <code>{order_number}</code>\n"
            f"📦 طلبك الآن قيد التنفيذ وسيتم شحنه يدويًا.",
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    else:
        await callback.answer("لم تصل الفلوس بعد، يرجى الانتظار والمحاولة مرة أخرى.", show_alert=True)
        wallet_address = await SettingsRepository.get_setting("ton_wallet", config.TON_WALLET_ADDRESS)
        memo = order.get("memo", "")
        ton_amount = order.get("ton_amount", 0.0)
        
        await callback.message.edit_text(
            f"❌ <b>لم تصل الفلوس إلى المحفظة بعد.</b>\n\n"
            f"يرجى التأكد من إتمام التحويل عبر TONKeeper:\n"
            f"▪️ <b>عنوان المحفظة:</b> <code>{wallet_address}</code>\n"
            f"▪️ <b>الـ Memo المطلوب:</b> <code>{memo}</code>\n"
            f"▪️ <b>المبلغ المطلوب:</b> <code>{ton_amount} TON</code>\n\n"
            f"⏳ بعد إتمام التحويل، يرجى الانتظار لعدة ثوانٍ ثم الضغط على <b>✅ تم الدفع (التحقق من الدفع)</b> مرة أخرى.",
            reply_markup=get_ton_payment_keyboard(wallet_address, ton_amount, memo),
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("resend_proof:"))
async def prompt_resend_proof(callback: CallbackQuery, state: FSMContext):
    """Prompt user to resend a new payment proof for a previously rejected order."""
    order_number = callback.data.split(":")[1]
    order = await OrderRepository.get_order_by_number(order_number)

    if not order or order["user_id"] != callback.from_user.id:
        await callback.answer("الطلب غير موجود.", show_alert=True)
        return

    await state.update_data(order_number=order_number, order_id=order["id"])
    await callback.message.edit_text(
        f"📸 <b>أرسل صورة إثبات التحويل الجديد للطلب #{order_number}:</b>",
        parse_mode="HTML"
    )
    await state.set_state(PaymentState.resending_proof)
    await callback.answer()

@router.message(PaymentState.resending_proof, F.photo)
async def process_resend_proof_photo(message: Message, state: FSMContext, bot: Bot):
    """Handle new photo proof for rejected order."""
    photo = message.photo[-1]
    file_id = photo.file_id

    data = await state.get_data()
    order_number = data.get("order_number")
    order = await OrderRepository.get_order_by_number(order_number)

    if not order:
        await message.answer("الطلب غير موجود.")
        await state.clear()
        return

    await OrderRepository.update_receipt(order["id"], file_id)
    await state.clear()

    await message.answer(
        f"🔍 <b>تم إعادة إرسال إثبات الدفع للطلب #{order_number} بنجاح!</b>\n\n"
        "جاري مراجعته من قبل إدارة المتجر.",
        reply_markup=get_main_menu_keyboard(),
        parse_mode="HTML"
    )

    if config.ADMIN_ID:
        try:
            admin_caption = (
                f"🔄 <b>إعادة إرسال إثبات دفع للطلب المرفوض سابقًا:</b> <code>{order['order_number']}</code>\n\n"
                f"👤 <b>المستخدم:</b> {message.from_user.full_name} (@{message.from_user.username or 'بدون'})\n"
                f"💰 <b>السعر:</b> {order['price_egp']} جنيه"
            )
            await bot.send_photo(
                chat_id=config.ADMIN_ID,
                photo=file_id,
                caption=admin_caption,
                reply_markup=get_order_action_keyboard(order["order_number"], "payment_review"),
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error notifying admin of resent proof: {e}")
