import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from repositories.orders import OrderRepository
from repositories.products import ProductRepository
from keyboards.user import get_product_packages_keyboard, get_order_confirmation_keyboard, get_main_menu_keyboard
from utils.validators import validate_player_id, validate_email
from utils.formatters import format_order_summary

router = Router()
logger = logging.getLogger(__name__)

class OrderState(StatesGroup):
    selecting_package = State()
    entering_customer_data = State()
    confirming_order = State()

@router.callback_query(F.data.startswith("prod:"))
async def select_product(callback: CallbackQuery, state: FSMContext):
    """Product selected - verify active order check and display packages."""
    user_id = callback.from_user.id

    # Check for active order
    active_order = await OrderRepository.get_active_user_order(user_id)
    if active_order:
        await callback.answer(
            "⚠️ لديك طلب نشط بالفعل.\nيمكنك متابعة حالة طلبك من زر: 📦 طلباتي",
            show_alert=True
        )
        return

    product_key = callback.data.split(":")[1]
    product = await ProductRepository.get_product_by_key(product_key)

    if not product or not product["is_active"]:
        await callback.answer("عذرًا، هذه الخدمة غير متوفرة حاليًا.", show_alert=True)
        return

    packages = await ProductRepository.get_packages_by_product_key(product_key, active_only=True)

    if not packages:
        await callback.answer("لا توجد باقات متوفرة لهذا المنتج حاليًا.", show_alert=True)
        return

    await state.update_data(
        product_key=product["key"],
        product_id=product["id"],
        product_name=product["name"],
        data_label=product["data_label"]
    )

    text = f"🎮 <b>اختر الباقة المناسبة لشحن {product['name']}:</b>"
    await callback.message.edit_text(text, reply_markup=get_product_packages_keyboard(packages, product_key), parse_mode="HTML")
    await state.set_state(OrderState.selecting_package)
    await callback.answer()

@router.callback_query(OrderState.selecting_package, F.data.startswith("pkg:"))
async def select_package(callback: CallbackQuery, state: FSMContext):
    """Package selected - prompt for Player ID or Email depending on product."""
    package_id = int(callback.data.split(":")[1])
    package = await ProductRepository.get_package_by_id(package_id)

    if not package or not package["is_active"]:
        await callback.answer("عذرًا، هذه الباقة غير متوفرة.", show_alert=True)
        return

    data = await state.get_data()
    product_key = data.get("product_key")
    data_label = data.get("data_label", "Player ID")

    await state.update_data(
        package_id=package["id"],
        package_name=package["name"],
        price_egp=package["price_egp"]
    )

    if product_key in ["pubg", "freefire"]:
        prompt_text = (
            f"📥 <b>يرجى إرسال الـ {data_label} الخاص بك:</b>\n\n"
            f"💡 مثال: <code>123456789</code>"
        )
    elif product_key == "googleplay":
        prompt_text = (
            "📥 <b>يرجى إرسال الإيميل المرتبط بحساب Google Play:</b>\n\n"
            "💡 مثال: <code>example@gmail.com</code>\n\n"
            "⚠️ <b>ملاحظة:</b> تحقق من صحة الإيميل، لأن التحقق الحالي يتأكد من صيغة الإيميل فقط، ويتم التأكد من الحساب أثناء تنفيذ الطلب."
        )
    elif product_key == "xbox":
        prompt_text = (
            "📥 <b>يرجى إرسال الإيميل المرتبط بحساب Xbox:</b>\n\n"
            "💡 مثال: <code>example@outlook.com</code>\n\n"
            "⚠️ <b>تنبيه هام:</b> بطاقات Xbox هي بطاقات أمريكية (US) وتحتاج حسابًا أو متجرًا مضبوطًا على الولايات المتحدة."
        )
    else:
        prompt_text = f"📥 <b>يرجى إرسال {data_label}:</b>"

    await callback.message.edit_text(prompt_text, parse_mode="HTML")
    await state.set_state(OrderState.entering_customer_data)
    await callback.answer()

@router.message(OrderState.entering_customer_data)
async def process_customer_data_input(message: Message, state: FSMContext):
    """Validate and receive customer input data (Player ID or Email)."""
    input_text = message.text.strip() if message.text else ""
    data = await state.get_data()
    product_key = data.get("product_key")
    data_label = data.get("data_label", "Player ID")

    if product_key in ["pubg", "freefire"]:
        if not validate_player_id(input_text):
            await message.answer(
                f"❌ <b>الـ {data_label} غير صحيح.</b>\n\n"
                f"يرجى إرسال {data_label} صحيح يحتوي على أرقام فقط (مثال: <code>123456789</code>).",
                parse_mode="HTML"
            )
            return
    elif product_key in ["googleplay", "xbox"]:
        if not validate_email(input_text):
            await message.answer(
                "❌ <b>صيغة الإيميل غير صحيحة.</b>\n\n"
                "يرجى إرسال إيميل صحيح، مثال:\n"
                "<code>example@gmail.com</code>",
                parse_mode="HTML"
            )
            return

    await state.update_data(customer_data=input_text)

    # Prepare order review notice
    notice = ""
    if product_key == "googleplay":
        notice = "⚠️ <i>يرجى التأكد من صحة الإيميل، لأن التحقق الحالي يتأكد من صيغة الإيميل فقط، ويتم التأكد من الحساب أثناء تنفيذ الطلب.</i>"
    elif product_key == "xbox":
        notice = "⚠️ <i>بطاقات Xbox هي بطاقات أمريكية (US) وتحتاج حسابًا أو متجرًا مضبوطًا على الولايات المتحدة.</i>"

    summary_text = format_order_summary(
        product_name=data["product_name"],
        package_name=data["package_name"],
        customer_data_label=data_label,
        customer_data_val=input_text,
        price_egp=data["price_egp"],
        notice=notice
    )

    await message.answer(summary_text, reply_markup=get_order_confirmation_keyboard(), parse_mode="HTML")
    await state.set_state(OrderState.confirming_order)

@router.callback_query(OrderState.confirming_order, F.data == "order:edit")
async def edit_customer_data(callback: CallbackQuery, state: FSMContext):
    """Re-prompt user for customer data input."""
    data = await state.get_data()
    data_label = data.get("data_label", "Player ID")
    await callback.message.edit_text(f"✏️ <b>أعد إدخال الـ {data_label}:</b>", parse_mode="HTML")
    await state.set_state(OrderState.entering_customer_data)
    await callback.answer()

@router.callback_query(F.data == "order:cancel")
async def cancel_order_flow(callback: CallbackQuery, state: FSMContext):
    """Cancel order creation process."""
    await state.clear()
    await callback.message.edit_text("❌ <b>تم إلغاء الطلب.</b>", reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
    await callback.answer()
