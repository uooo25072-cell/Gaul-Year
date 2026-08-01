import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from repositories.users import UserRepository
from repositories.orders import OrderRepository
from keyboards.user import get_main_menu_keyboard, get_user_orders_keyboard
from utils.formatters import get_arabic_status

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command - welcome user and present main store menu."""
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name or "المستخدم"

    # Register user in DB
    await UserRepository.add_or_update_user(user_id, username, full_name)

    welcome_text = (
        "🏪 <b>مرحبًا بك في GameZone</b>\n\n"
        "المتجر الأفضل لشحن الألعاب والبطاقات الرقمية بسرعة وأمان! ⚡️\n\n"
        "اختر الخدمة التي تريدها من الأزرار أدناه:"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "nav:main")
async def nav_main_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main menu."""
    await state.clear()
    welcome_text = (
        "🏪 <b>مرحبًا بك في GameZone</b>\n\n"
        "اختر الخدمة التي تريدها:"
    )
    if callback.message:
        try:
            await callback.message.edit_text(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
        except Exception:
            await callback.message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "user:my_orders")
async def show_my_orders(callback: CallbackQuery):
    """Display user order history."""
    user_id = callback.from_user.id
    orders = await OrderRepository.get_user_orders(user_id)

    if not orders:
        await callback.answer("لا توجد لديك طلبات سابقة حتى الآن.", show_alert=True)
        return

    text = "📦 <b>قائمة طلباتك السابقة:</b>\n\nاضغط على أي طلب لعرض تفاصيله الكاملة."
    await callback.message.edit_text(text, reply_markup=get_user_orders_keyboard(orders), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("order_view:"))
async def view_order_detail(callback: CallbackQuery):
    """View details of a specific order."""
    order_number = callback.data.split(":")[1]
    order = await OrderRepository.get_order_by_number(order_number)

    if not order or order["user_id"] != callback.from_user.id:
        await callback.answer("عذرًا، لم يتم العثور على هذا الطلب.", show_alert=True)
        return

    status_arabic = get_arabic_status(order["status"])
    text = (
        f"📄 <b>تفاصيل الطلب:</b> <code>{order['order_number']}</code>\n\n"
        f"🎮 <b>المنتج:</b> {order['product_name']}\n"
        f"💎 <b>الباقة:</b> {order['package_name']}\n"
        f"🆔 <b>البيانات:</b> <code>{order['customer_data']}</code>\n"
        f"💰 <b>السعر:</b> {order['price_egp']} جنيه\n"
        f"💳 <b>طريقة الدفع:</b> {order['payment_method'].upper()}\n"
        f"📌 <b>حالة الطلب:</b> {status_arabic}\n"
        f"📅 <b>تاريخ الطلب:</b> {order['created_at']}\n"
    )

    if order.get("rejection_reason"):
        text += f"\n❌ <b>سبب الرفض:</b> {order['rejection_reason']}\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    if order["status"] == "rejected":
        # Allow resending proof for rejected order
        buttons.append([InlineKeyboardButton(text="📸 إرسال إثبات دفع جديد", callback_data=f"resend_proof:{order['order_number']}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ قائمة طلباتي", callback_data="user:my_orders")])
    buttons.append([InlineKeyboardButton(text="⬅️ القائمة الرئيسية", callback_data="nav:main")])

    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()
