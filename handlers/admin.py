import logging
import os
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import config
from filters.admin import IsAdminFilter
from repositories.orders import OrderRepository
from repositories.users import UserRepository
from repositories.products import ProductRepository
from repositories.settings import SettingsRepository
from repositories.admin_logs import AdminLogRepository
from services.backup_service import BackupService
from services.broadcast_service import BroadcastService
from keyboards.admin import (
    get_admin_main_keyboard,
    get_order_action_keyboard,
    get_rejection_reasons_keyboard,
    get_orders_filter_keyboard,
    get_admin_packages_keyboard,
    get_package_edit_actions_keyboard,
    get_payment_edit_keyboard,
    get_broadcast_type_keyboard,
    get_confirm_broadcast_keyboard,
    get_restore_confirm_keyboard
)
from keyboards.user import get_main_menu_keyboard
from utils.formatters import get_arabic_status, format_price

router = Router()
router.message.filter(IsAdminFilter())
router.callback_query.filter(IsAdminFilter())
logger = logging.getLogger(__name__)

class AdminState(StatesGroup):
    entering_search_order = State()
    entering_search_user = State()
    entering_rejection_reason = State()
    adding_pkg_name = State()
    adding_pkg_price = State()
    editing_pkg_name = State()
    editing_pkg_price = State()
    editing_vodafone_number = State()
    editing_vodafone_name = State()
    editing_binance_id = State()
    editing_binance_name = State()
    editing_ton_wallet = State()
    broadcasting_content = State()
    uploading_backup_file = State()

# ----------------- Main Admin Dashboard -----------------

@router.message(Command("admin"))
async def cmd_admin_dashboard(message: Message, state: FSMContext):
    """Open Admin Control Panel."""
    await state.clear()
    text = (
        "🛠️ <b>لوحة تحكم GameZone</b>\n\n"
        "مرحبًا بك في لوحة تحكم المتجر. يمكنك إدارة جميع العمليات والباقات والطلبات والمستخدمين من الأزرار أدناه:"
    )
    await message.answer(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "adm:main")
async def nav_admin_main(callback: CallbackQuery, state: FSMContext):
    """Return to Admin main menu."""
    await state.clear()
    text = (
        "🛠️ <b>لوحة تحكم GameZone</b>\n\n"
        "اختر القسم المطلوبة إدارته:"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")
    await callback.answer()

# ----------------- Statistics -----------------

@router.callback_query(F.data == "adm:stats")
async def show_admin_stats(callback: CallbackQuery):
    """Display store statistics summary."""
    stats = await OrderRepository.get_stats()
    user_count = await UserRepository.count_users()

    text = (
        "📊 <b>إحصائيات متجر GameZone</b>\n\n"
        f"👥 <b>إجمالي المستخدمين:</b> {user_count}\n"
        f"📦 <b>إجمالي الطلبات:</b> {stats['total_orders']}\n\n"
        f"⏳ <b>في انتظار الدفع:</b> {stats['pending_payment']}\n"
        f"🔍 <b>قيد المراجعة:</b> {stats['payment_review']}\n"
        f"⚙️ <b>قيد التنفيذ:</b> {stats['processing']}\n"
        f"✅ <b>الطلبات المكتملة:</b> {stats['completed']}\n"
        f"❌ <b>الطلبات المرفوضة:</b> {stats['rejected']}\n\n"
        f"💰 <b>إجمالي المبيعات:</b> {format_price(stats['total_sales'])}\n"
        f"📈 <b>مبيعات اليوم:</b> {format_price(stats['today_sales'])}\n"
    )
    await callback.message.edit_text(text, reply_markup=get_admin_main_keyboard(), parse_mode="HTML")
    await callback.answer()

# ----------------- Orders Management -----------------

@router.callback_query(F.data == "adm:orders_menu")
async def show_orders_menu(callback: CallbackQuery):
    """Orders management main sub-menu."""
    text = "📦 <b>إدارة الطلبات</b>\n\nاختر الحالة أو نوع البحث الذي تريده:"
    await callback.message.edit_text(text, reply_markup=get_orders_filter_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_filter:"))
async def filter_orders_by_status(callback: CallbackQuery):
    """List orders matching status filter."""
    status = callback.data.split(":")[1]
    orders = await OrderRepository.get_orders_by_status(status)

    if not orders:
        await callback.answer(f"لا توجد طلبات بحالة: {get_arabic_status(status)}", show_alert=True)
        return

    text = f"📦 <b>الطلبات بحالة: ({get_arabic_status(status)})</b>\n\nاضغط على أي طلب لمعاينته:"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for ord_item in orders[:15]:
        b_text = f"#{ord_item['order_number']} | {ord_item['product_name']} ({ord_item['price_egp']}ج)"
        buttons.append([InlineKeyboardButton(text=b_text, callback_data=f"adm_view_order:{ord_item['order_number']}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ إدارة الطلبات", callback_data="adm:orders_menu")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_view_order:"))
async def admin_view_order_details(callback: CallbackQuery, bot: Bot):
    """View full order detail & actions for admin."""
    order_number = callback.data.split(":")[1]
    order = await OrderRepository.get_order_by_number(order_number)

    if not order:
        await callback.answer("الطلب غير موجود.", show_alert=True)
        return

    status_arabic = get_arabic_status(order["status"])
    user = await UserRepository.get_user(order["user_id"])
    user_name = user["full_name"] if user else "مجهول"
    user_uname = f"@{user['username']}" if user and user.get("username") else "بدون"

    text = (
        f"📑 <b>تفاصيل الطلب:</b> <code>{order['order_number']}</code>\n\n"
        f"👤 <b>المستخدم:</b> {user_name} ({user_uname})\n"
        f"🆔 <b>Telegram ID:</b> <code>{order['user_id']}</code>\n"
        f"🎮 <b>المنتج:</b> {order['product_name']}\n"
        f"💎 <b>الباقة:</b> {order['package_name']}\n"
        f"🔑 <b>بيانات العميل:</b> <code>{order['customer_data']}</code>\n"
        f"💰 <b>السعر:</b> {order['price_egp']} جنيه ({order['ton_amount']} TON)\n"
        f"💳 <b>طريقة الدفع:</b> {order['payment_method'].upper()}\n"
        f"📌 <b>الحالة:</b> {status_arabic}\n"
        f"📅 <b>تاريخ الطلب:</b> {order['created_at']}\n"
    )

    if order.get("receipt_file_id"):
        try:
            await bot.send_photo(
                chat_id=callback.from_user.id,
                photo=order["receipt_file_id"],
                caption=text,
                reply_markup=get_order_action_keyboard(order["order_number"], order["status"]),
                parse_mode="HTML"
            )
            await callback.answer()
            return
        except Exception:
            pass

    await callback.message.edit_text(text, reply_markup=get_order_action_keyboard(order["order_number"], order["status"]), parse_mode="HTML")
    await callback.answer()

# ----------------- Order Actions (Approve / Reject / Process / Complete) -----------------

@router.callback_query(F.data.startswith("adm_act:approve:"))
async def admin_approve_payment(callback: CallbackQuery, bot: Bot):
    """Admin approves payment for order."""
    order_number = callback.data.split(":")[2]
    order = await OrderRepository.get_order_by_number(order_number)

    if not order:
        await callback.answer("الطلب غير موجود.", show_alert=True)
        return

    await OrderRepository.update_status(order["id"], "payment_confirmed")
    await AdminLogRepository.log_action(callback.from_user.id, "approve_payment", order_number, "Approved payment")

    await callback.answer("✅ تم قبول الدفع بنجاح!")
    
    # Notify User
    try:
        await bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"✅ <b>تم تأكيد دفعتك بنجاح للطلب #{order_number}.</b>\n\n"
                "📦 طلبك الآن قيد التنفيذ وسيتم شحنه يدويًا."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send approve alert to user: {e}")

    await admin_view_order_details(callback, bot)

@router.callback_query(F.data.startswith("adm_act:process:"))
async def admin_process_order(callback: CallbackQuery, bot: Bot):
    """Admin sets order status to processing."""
    order_number = callback.data.split(":")[2]
    order = await OrderRepository.get_order_by_number(order_number)

    if not order:
        await callback.answer("الطلب غير موجود.", show_alert=True)
        return

    await OrderRepository.update_status(order["id"], "processing")
    await AdminLogRepository.log_action(callback.from_user.id, "process_order", order_number, "Set status to processing")

    await callback.answer("⚙️ تم تحويل الطلب لـ جاري التنفيذ.")
    
    # Notify User
    try:
        await bot.send_message(
            chat_id=order["user_id"],
            text=f"⚙️ <b>جاري تنفيذ طلبك #{order_number} الآن بواسطة الفريق...</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send processing alert to user: {e}")

    await admin_view_order_details(callback, bot)

@router.callback_query(F.data.startswith("adm_act:complete:"))
async def admin_complete_order(callback: CallbackQuery, bot: Bot):
    """Admin marks order as completed/shipped."""
    order_number = callback.data.split(":")[2]
    order = await OrderRepository.get_order_by_number(order_number)

    if not order:
        await callback.answer("الطلب غير موجود.", show_alert=True)
        return

    await OrderRepository.update_status(order["id"], "completed")
    await AdminLogRepository.log_action(callback.from_user.id, "complete_order", order_number, "Marked as completed")

    await callback.answer("📦 تم الشحن بنجاح!")

    # Notify User
    try:
        await bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"🎉 <b>تم شحن طلبك بنجاح!</b>\n\n"
                f"🧾 <b>رقم الطلب:</b> <code>{order['order_number']}</code>\n"
                f"🎮 <b>المنتج:</b> {order['product_name']} ({order['package_name']})\n\n"
                "شكرًا لاستخدام GameZone ❤️"
            ),
            reply_markup=get_main_menu_keyboard(),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send completed alert to user: {e}")

    await admin_view_order_details(callback, bot)

@router.callback_query(F.data.startswith("adm_act:reject:"))
async def admin_reject_order_prompt(callback: CallbackQuery):
    """Prompt admin for rejection reason."""
    order_number = callback.data.split(":")[2]
    text = f"❌ <b>اختر سبب رفض الطلب #{order_number}:</b>"
    await callback.message.edit_text(text, reply_markup=get_rejection_reasons_keyboard(order_number), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_rej_reason:"))
async def admin_apply_rejection_reason(callback: CallbackQuery, state: FSMContext, bot: Bot):
    """Apply rejection reason to order."""
    parts = callback.data.split(":")
    order_number = parts[1]
    reason_code = parts[2]

    reasons_map = {
        "fake": "إيصال غير واضح أو مزور",
        "incomplete": "المبلغ المحول غير مكتمل",
        "not_received": "لم يصل التحويل لحسابنا حتى الآن",
        "bad_data": "بيانات الحساب أو الـ ID المقدم غير صحيحة",
    }

    if reason_code == "custom":
        await state.update_data(reject_order_number=order_number)
        await callback.message.edit_text("✍️ <b>يرجى كتابة سبب الرفض في رسالة:</b>", parse_mode="HTML")
        await state.set_state(AdminState.entering_rejection_reason)
        await callback.answer()
        return

    reason = reasons_map.get(reason_code, "تم رفض الطلب")
    await finalize_rejection(order_number, reason, callback, bot)

@router.message(AdminState.entering_rejection_reason)
async def process_custom_rejection_reason(message: Message, state: FSMContext, bot: Bot):
    """Process custom rejection text entered by admin."""
    reason = message.text.strip() if message.text else "تم رفض الطلب"
    data = await state.get_data()
    order_number = data.get("reject_order_number")
    await state.clear()

    order = await OrderRepository.get_order_by_number(order_number)
    if not order:
        await message.answer("الطلب غير موجود.")
        return

    await OrderRepository.update_status(order["id"], "rejected", rejection_reason=reason)
    await AdminLogRepository.log_action(message.from_user.id, "reject_order", order_number, f"Reason: {reason}")

    await message.answer(f"❌ تم رفض الطلب #{order_number} بنجاح وإرسال السبب للمستخدم.")

    # Notify User
    try:
        await bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"❌ <b>تم رفض طلبك رقم #{order_number}</b>\n\n"
                f"📝 <b>سبب الرفض:</b> {reason}\n\n"
                "💡 يمكنك إرسال إثبات جديد بنفس الطلب من صفحة <b>📦 طلباتي</b>."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send rejection to user: {e}")

async def finalize_rejection(order_number: str, reason: str, callback: CallbackQuery, bot: Bot):
    order = await OrderRepository.get_order_by_number(order_number)
    if not order:
        await callback.answer("الطلب غير موجود.", show_alert=True)
        return

    await OrderRepository.update_status(order["id"], "rejected", rejection_reason=reason)
    await AdminLogRepository.log_action(callback.from_user.id, "reject_order", order_number, f"Reason: {reason}")

    await callback.answer("❌ تم رفض الطلب بنجاح.")

    # Notify User
    try:
        await bot.send_message(
            chat_id=order["user_id"],
            text=(
                f"❌ <b>تم رفض طلبك رقم #{order_number}</b>\n\n"
                f"📝 <b>سبب الرفض:</b> {reason}\n\n"
                "💡 يمكنك إعادة إرسال إثبات جديد لنفس الطلب من قائمة <b>📦 طلباتي</b> دون الحاجة لإلغائه."
            ),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Failed to send rejection to user: {e}")

    await admin_view_order_details(callback, bot)

# ----------------- Products & Packages Management -----------------

@router.callback_query(F.data == "adm:products_menu")
async def show_products_menu(callback: CallbackQuery):
    """Display product list to edit packages."""
    products = await ProductRepository.get_all_products(active_only=False)

    text = "🛒 <b>إدارة المنتجات والباقات</b>\n\nاختر المنتج لمشاهدة وتعديل باقاته:"
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    for p in products:
        buttons.append([InlineKeyboardButton(text=f"🎮 {p['name']}", callback_data=f"adm_pkgs_view:{p['key']}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ لوحة تحكم الأدمن", callback_data="adm:main")])
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_pkgs_view:"))
async def view_product_packages_admin(callback: CallbackQuery):
    """View package items of selected product."""
    product_key = callback.data.split(":")[1]
    product = await ProductRepository.get_product_by_key(product_key)
    packages = await ProductRepository.get_packages_by_product_key(product_key, active_only=False)

    text = f"📦 <b>إدارة باقات {product['name']}:</b>\n\nاضغط على أي باقة للتعديل أو الحذف:"
    await callback.message.edit_text(text, reply_markup=get_admin_packages_keyboard(packages, product_key), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_pkg_edit:"))
async def edit_package_options(callback: CallbackQuery):
    """Package options menu (edit name, edit price, toggle status, delete)."""
    package_id = int(callback.data.split(":")[1])
    package = await ProductRepository.get_package_by_id(package_id)

    if not package:
        await callback.answer("الباقة غير موجودة.", show_alert=True)
        return

    status_str = "🟢 مفعلة" if package["is_active"] else "🔴 معطلة"
    text = (
        f"⚙️ <b>تعديل الباقة:</b> {package['name']}\n\n"
        f"💰 <b>السعر الحالي:</b> {package['price_egp']} جنيه\n"
        f"📌 <b>الحالة:</b> {status_str}"
    )
    await callback.message.edit_text(text, reply_markup=get_package_edit_actions_keyboard(package_id), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_pkg_act:toggle:"))
async def toggle_package_status_admin(callback: CallbackQuery):
    """Toggle package active state."""
    package_id = int(callback.data.split(":")[2])
    await ProductRepository.toggle_package_status(package_id)
    await AdminLogRepository.log_action(callback.from_user.id, "toggle_package", details=f"Package ID {package_id}")
    await edit_package_options(callback)

@router.callback_query(F.data.startswith("adm_pkg_act:delete:"))
async def delete_package_admin(callback: CallbackQuery):
    """Delete package."""
    package_id = int(callback.data.split(":")[2])
    await ProductRepository.delete_package(package_id)
    await AdminLogRepository.log_action(callback.from_user.id, "delete_package", details=f"Package ID {package_id}")
    await callback.answer("🗑️ تم حذف الباقة بنجاح.")
    await show_products_menu(callback)

@router.callback_query(F.data.startswith("adm_pkg_add:"))
async def add_package_start(callback: CallbackQuery, state: FSMContext):
    """Start FSM for adding new package."""
    product_key = callback.data.split(":")[1]
    await state.update_data(add_pkg_product_key=product_key)
    await callback.message.edit_text("📝 <b>أدخل اسم الباقة الجديدة:</b> (مثال: <code>500 UC</code>)", parse_mode="HTML")
    await state.set_state(AdminState.adding_pkg_name)
    await callback.answer()

@router.message(AdminState.adding_pkg_name)
async def add_package_name_input(message: Message, state: FSMContext):
    """Receive new package name."""
    await state.update_data(add_pkg_name=message.text.strip())
    await message.answer("💰 <b>أدخل سعر الباقة بالجنيه:</b> (مثال: <code>450</code>)", parse_mode="HTML")
    await state.set_state(AdminState.adding_pkg_price)

@router.message(AdminState.adding_pkg_price)
async def add_package_price_input(message: Message, state: FSMContext):
    """Receive new package price and create in DB."""
    try:
        price = float(message.text.strip())
    except ValueError:
        await message.answer("❌ سعر غير صحيح، أدخل رقمًا فقط:")
        return

    data = await state.get_data()
    product_key = data.get("add_pkg_product_key")
    pkg_name = data.get("add_pkg_name")
    await state.clear()

    await ProductRepository.add_package(product_key, pkg_name, price)
    await AdminLogRepository.log_action(message.from_user.id, "add_package", details=f"{pkg_name} - {price} EGP")
    await message.answer(f"✅ تم إضافة الباقة الجديدة: <b>{pkg_name}</b> بسعر <b>{price} جنيه</b> بنجاح!", parse_mode="HTML")

# ----------------- Payment Methods Settings -----------------

@router.callback_query(F.data == "adm:payments_menu")
async def show_payments_menu(callback: CallbackQuery):
    """Display payment method edit options."""
    rate = await SettingsRepository.get_setting("ton_egp_rate", "120.0")
    updated_at = await SettingsRepository.get_setting("ton_rate_updated_at", "غير محدد")
    text = (
        "💳 <b>إدارة بيانات وطرق الدفع</b>\n\n"
        f"📊 <b>سعر صرف TON الحالي:</b> <code>{rate} EGP</code>\n"
        f"🕒 <b>آخر تحديث للسعر:</b> <code>{updated_at}</code>\n\n"
        "اختر وسيلة الدفع لتعديل بياناتها أو اضغط تحديث السعر لجلب سعر السوق المباشر:"
    )
    await callback.message.edit_text(text, reply_markup=get_payment_edit_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "adm_pay_edit:refresh_ton")
async def refresh_ton_rate_handler(callback: CallbackQuery):
    from services.ton_service import TonService
    result = await TonService.update_ton_rate()
    rate = result.get("rate")
    updated_at = result.get("updated_at")
    await callback.answer(f"✅ تم تحديث السعر: {rate} EGP", show_alert=True)
    text = (
        "💳 <b>إدارة بيانات وطرق الدفع</b>\n\n"
        f"📊 <b>سعر صرف TON الحالي:</b> <code>{rate} EGP</code>\n"
        f"🕒 <b>آخر تحديث للسعر:</b> <code>{updated_at}</code>\n\n"
        "✅ تم تحديث سعر صرف TON تلقائيًا من الـ API بنجاح!"
    )
    await callback.message.edit_text(text, reply_markup=get_payment_edit_keyboard(), parse_mode="HTML")

@router.callback_query(F.data == "adm_pay_edit:vodafone")
async def edit_vodafone_start(callback: CallbackQuery, state: FSMContext):
    """Start edit Vodafone Cash."""
    await callback.message.edit_text("📱 <b>أدخل رقم Vodafone Cash الجديد:</b>", parse_mode="HTML")
    await state.set_state(AdminState.editing_vodafone_number)
    await callback.answer()

@router.message(AdminState.editing_vodafone_number)
async def process_vodafone_number(message: Message, state: FSMContext):
    num = message.text.strip()
    await SettingsRepository.set_setting("vodafone_number", num)
    await message.answer("👤 <b>أدخل الاسم المسجل لرقم Vodafone Cash:</b>", parse_mode="HTML")
    await state.set_state(AdminState.editing_vodafone_name)

@router.message(AdminState.editing_vodafone_name)
async def process_vodafone_name(message: Message, state: FSMContext):
    name = message.text.strip()
    await SettingsRepository.set_setting("vodafone_name", name)
    await state.clear()
    await AdminLogRepository.log_action(message.from_user.id, "update_vodafone", details=f"Name: {name}")
    await message.answer("✅ <b>تم تحديث بيانات Vodafone Cash بنجاح!</b>", parse_mode="HTML")

@router.callback_query(F.data == "adm_pay_edit:binance")
async def edit_binance_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🟡 <b>أدخل Binance ID الجديد:</b>", parse_mode="HTML")
    await state.set_state(AdminState.editing_binance_id)
    await callback.answer()

@router.message(AdminState.editing_binance_id)
async def process_binance_id(message: Message, state: FSMContext):
    b_id = message.text.strip()
    await SettingsRepository.set_setting("binance_id", b_id)
    await message.answer("👤 <b>أدخل الاسم المسجل لـ Binance:</b>", parse_mode="HTML")
    await state.set_state(AdminState.editing_binance_name)

@router.message(AdminState.editing_binance_name)
async def process_binance_name(message: Message, state: FSMContext):
    b_name = message.text.strip()
    await SettingsRepository.set_setting("binance_name", b_name)
    await state.clear()
    await AdminLogRepository.log_action(message.from_user.id, "update_binance", details=f"ID: {b_name}")
    await message.answer("✅ <b>تم تحديث بيانات Binance ID بنجاح!</b>", parse_mode="HTML")

@router.callback_query(F.data == "adm_pay_edit:ton")
async def edit_ton_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("🪙 <b>أدخل عنوان محفظة TONKeeper الجديد:</b>", parse_mode="HTML")
    await state.set_state(AdminState.editing_ton_wallet)
    await callback.answer()

@router.message(AdminState.editing_ton_wallet)
async def process_ton_wallet(message: Message, state: FSMContext):
    w_addr = message.text.strip()
    await SettingsRepository.set_setting("ton_wallet", w_addr)
    await state.clear()
    await AdminLogRepository.log_action(message.from_user.id, "update_ton_wallet", details=w_addr)
    await message.answer("✅ <b>تم تحديث عنوان محفظة TON بنجاح!</b>", parse_mode="HTML")

# ----------------- User Management & Banning -----------------

@router.callback_query(F.data == "adm:users_menu")
async def show_users_menu(callback: CallbackQuery, state: FSMContext):
    """User management sub-menu."""
    users = await UserRepository.get_all_users()
    text = f"👥 <b>إدارة المستخدمين ({len(users)} مستخدم)</b>\n\nأرسل Telegram ID للمستخدم للبحث عنه أو التعديل عليه:"
    await callback.message.edit_text(text, parse_mode="HTML")
    await state.set_state(AdminState.entering_search_user)
    await callback.answer()

@router.message(AdminState.entering_search_user)
async def process_search_user(message: Message, state: FSMContext):
    try:
        target_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ يرجى إدخال Telegram ID رقمي صحبح:")
        return

    user = await UserRepository.get_user(target_id)
    if not user:
        await message.answer("❌ لم يتم العثور على مستخدم بهذا الـ ID.")
        return

    orders = await OrderRepository.get_user_orders(target_id)
    is_b = await UserRepository.is_banned(target_id)
    ban_status = "🔴 محظور" if is_b else "🟢 نشط"

    text = (
        f"👤 <b>بيانات المستخدم:</b>\n\n"
        f"<b>الاسم:</b> {user['full_name']}\n"
        f"<b>Username:</b> @{user['username'] or 'لا يوجد'}\n"
        f"<b>Telegram ID:</b> <code>{user['telegram_id']}</code>\n"
        f"<b>حالة الحساب:</b> {ban_status}\n"
        f"<b>عدد الطلبات:</b> {len(orders)}\n"
        f"<b>تاريخ الانضمام:</b> {user['created_at']}\n"
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    buttons = []
    if is_b:
        buttons.append([InlineKeyboardButton(text="🟢 فك الحظر", callback_data=f"adm_unban:{target_id}")])
    else:
        buttons.append([InlineKeyboardButton(text="🔴 حظر المستخدم", callback_data=f"adm_ban:{target_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ لوحة تحكم الأدمن", callback_data="adm:main")])

    await message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), parse_mode="HTML")
    await state.clear()

@router.callback_query(F.data.startswith("adm_ban:"))
async def ban_user_action(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    await UserRepository.ban_user(target_id, "Banned by Admin")
    await AdminLogRepository.log_action(callback.from_user.id, "ban_user", details=f"Banned user {target_id}")
    await callback.answer("🔴 تم حظر المستخدم بنجاح.", show_alert=True)
    await nav_admin_main(callback, FSMContext)

@router.callback_query(F.data.startswith("adm_unban:"))
async def unban_user_action(callback: CallbackQuery):
    target_id = int(callback.data.split(":")[1])
    await UserRepository.unban_user(target_id)
    await AdminLogRepository.log_action(callback.from_user.id, "unban_user", details=f"Unbanned user {target_id}")
    await callback.answer("🟢 تم فك الحظر عن المستخدم.", show_alert=True)
    await nav_admin_main(callback, FSMContext)

# ----------------- Maintenance Mode -----------------

@router.callback_query(F.data == "adm:maintenance_toggle")
async def toggle_maintenance(callback: CallbackQuery):
    current = await SettingsRepository.get_setting("maintenance_mode", "0")
    new_val = "1" if current == "0" else "0"
    await SettingsRepository.set_setting("maintenance_mode", new_val)
    await AdminLogRepository.log_action(callback.from_user.id, "toggle_maintenance", details=f"Set to {new_val}")
    
    status_text = "🟢 تم إيقاف الصيانة والخدمة تعمل الآن." if new_val == "0" else "🔴 تم تفعيل وضع الصيانة، المتجر مغلق مؤقتًا للمستخدمين."
    await callback.answer(status_text, show_alert=True)
    await nav_admin_main(callback, FSMContext)

# ----------------- Broadcast -----------------

@router.callback_query(F.data == "adm:broadcast_menu")
async def show_broadcast_menu(callback: CallbackQuery):
    text = "📢 <b>إرسال إذاعة عامة لجميع المستخدمين</b>\n\nاختر نوع الرسالة:"
    await callback.message.edit_text(text, reply_markup=get_broadcast_type_keyboard(), parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data.startswith("adm_bcast:"))
async def handle_broadcast_type_select(callback: CallbackQuery, state: FSMContext):
    action = callback.data.split(":")[1]
    if action == "text":
        await state.update_data(bcast_type="text")
        await callback.message.edit_text("📝 <b>أرسل نص الرسالة الإذاعية:</b>", parse_mode="HTML")
    elif action == "photo":
        await state.update_data(bcast_type="photo")
        await callback.message.edit_text("🖼️ <b>أرسل الصورة مع الشرح نصًا (Caption):</b>", parse_mode="HTML")
    elif action == "video":
        await state.update_data(bcast_type="video")
        await callback.message.edit_text("🎥 <b>أرسل الفيديو مع الشرح نصًا (Caption):</b>", parse_mode="HTML")
    elif action == "confirm_start":
        data = await state.get_data()
        b_type = data.get("bcast_type")
        content = data.get("bcast_content")
        caption = data.get("bcast_caption", "")
        await callback.message.edit_text("⏳ <b>جاري إرسال الإذاعة لجميع المستخدمين...</b>", parse_mode="HTML")
        
        bot = callback.bot
        succ, fail = await BroadcastService.send_broadcast(bot, b_type, content, caption)
        await state.clear()
        
        await callback.message.answer(
            f"✅ <b>تم الانتهاء من الإذاعة!</b>\n\n"
            f"🟢 <b>الرسائل الناجحة:</b> {succ}\n"
            f"🔴 <b>الرسائل الفاشلة:</b> {fail}",
            reply_markup=get_admin_main_keyboard(),
            parse_mode="HTML"
        )
        return

    await state.set_state(AdminState.broadcasting_content)
    await callback.answer()

@router.message(AdminState.broadcasting_content)
async def receive_broadcast_content(message: Message, state: FSMContext):
    data = await state.get_data()
    b_type = data.get("bcast_type")

    if b_type == "text":
        await state.update_data(bcast_content=message.text, bcast_caption="")
    elif b_type == "photo" and message.photo:
        await state.update_data(bcast_content=message.photo[-1].file_id, bcast_caption=message.caption or "")
    elif b_type == "video" and message.video:
        await state.update_data(bcast_content=message.video.file_id, bcast_caption=message.caption or "")
    else:
        await message.answer("❌ محتوى غير متوافق مع النوع المختار.")
        return

    await message.answer(
        "⚠️ <b>هل أنت متأكد من إرسال هذه الإذاعة لجميع المستخدمين؟</b>",
        reply_markup=get_confirm_broadcast_keyboard(),
        parse_mode="HTML"
    )

# ----------------- Backup & Restore -----------------

@router.callback_query(F.data == "adm:backup_menu")
async def show_backup_menu(callback: CallbackQuery):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💾 إنشاء وتحميل نسخة احتياطية", callback_data="adm_backup:create"),
            ],
            [
                InlineKeyboardButton(text="📂 استعادة نسخة احتياطية", callback_data="adm_backup:restore_start"),
            ],
            [
                InlineKeyboardButton(text="⬅️ لوحة تحكم الأدمن", callback_data="adm:main")
            ]
        ]
    )
    text = "💾 <b>إدارة النسخ الاحتياطي لقاعدة البيانات</b>"
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()

@router.callback_query(F.data == "adm_backup:create")
async def create_backup_download(callback: CallbackQuery):
    try:
        file_path = BackupService.create_backup()
        file_input = FSInputFile(file_path)
        await callback.message.answer_document(
            document=file_input,
            caption="💾 <b>نسخة احتياطية من قاعدة البيانات: GameZone</b>"
        )
        await callback.answer("✅ تم تصدير النسخة بنجاح.")
    except Exception as e:
        logger.error(f"Backup creation error: {e}")
        await callback.answer("❌ حدث خطأ أثناء إنشاء النسخة الاحتياطية.", show_alert=True)

@router.callback_query(F.data == "adm_backup:restore_start")
async def restore_backup_prompt(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "📂 <b>قم بإرسال ملف النسخة الاحتياطية (.db):</b>\n\n"
        "⚠️ <b>تنبيه:</b> استعادة النسخة ستستبدل قاعدة البيانات الحالية بالكامل.",
        parse_mode="HTML"
    )
    await state.set_state(AdminState.uploading_backup_file)
    await callback.answer()

@router.message(AdminState.uploading_backup_file, F.document)
async def receive_backup_file(message: Message, state: FSMContext, bot: Bot):
    doc = message.document
    if not doc.file_name or not doc.file_name.endswith(".db"):
        await message.answer("❌ يرجى إرسال ملف بصيغة .db فقط.")
        return

    target_dir = os.path.join(os.path.dirname(config.DATABASE_PATH), "temp")
    os.makedirs(target_dir, exist_ok=True)
    temp_path = os.path.join(target_dir, doc.file_name)
    
    await bot.download(doc, destination=temp_path)
    await state.update_data(temp_backup_path=temp_path)

    await message.answer(
        f"⚠️ <b>هل أنت متأكد من استعادة النسخة الاحتياطية ({doc.file_name})؟</b>\n\n"
        "سيتم استبدال جميع البيانات الحالية بالبيانات الموجودة في الملف.",
        reply_markup=get_restore_confirm_keyboard(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "adm_backup:confirm_restore")
async def execute_restore_backup(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    temp_path = data.get("temp_backup_path")

    if temp_path and os.path.exists(temp_path):
        try:
            BackupService.restore_backup(temp_path)
            await state.clear()
            await callback.message.edit_text("✅ <b>تمت استعادة قاعدة البيانات بنجاح!</b>", parse_mode="HTML")
            await AdminLogRepository.log_action(callback.from_user.id, "restore_backup", details="Restored DB backup")
        except Exception as e:
            logger.error(f"Restore error: {e}")
            await callback.answer("❌ فشل استعادة النسخة.", show_alert=True)
    else:
        await callback.answer("ملف النسخة الاحتياطية غير متاح.", show_alert=True)

# ----------------- Admin Logs -----------------

@router.callback_query(F.data == "adm:logs")
async def show_admin_logs(callback: CallbackQuery):
    logs = await AdminLogRepository.get_recent_logs(20)
    if not logs:
        await callback.answer("سجل الأدمن فارغ.", show_alert=True)
        return

    text = "📜 <b>سجل آخر عمليات الأدمن:</b>\n\n"
    for l in logs:
        text += f"• <b>{l['action']}</b> | {l['details'] or ''} ({l['created_at']})\n"

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await callback.message.edit_text(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ رجوع", callback_data="adm:main")]]), parse_mode="HTML")
    await callback.answer()
