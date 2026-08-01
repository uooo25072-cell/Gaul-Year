from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Main menu keyboard for users."""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🎮 PUBG Mobile", callback_data="prod:pubg"),
                InlineKeyboardButton(text="🔥 Free Fire", callback_data="prod:freefire"),
            ],
            [
                InlineKeyboardButton(text="🎁 Google Play", callback_data="prod:googleplay"),
                InlineKeyboardButton(text="🟢 Xbox", callback_data="prod:xbox"),
            ],
            [
                InlineKeyboardButton(text="📦 طلباتي", callback_data="user:my_orders"),
                InlineKeyboardButton(text="☎️ الدعم الفني", url="https://t.me/vcvui"),
            ]
        ]
    )
    return keyboard

def get_product_packages_keyboard(packages: List[Dict[str, Any]], product_key: str) -> InlineKeyboardMarkup:
    """Generate packages selection list keyboard."""
    buttons = []
    for pkg in packages:
        text = f"{pkg['name']} = {pkg['price_egp']} جنيه"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"pkg:{pkg['id']}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ القائمة الرئيسية", callback_data="nav:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_order_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Order review confirmation keyboard."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأكيد الطلب", callback_data="order:confirm"),
                InlineKeyboardButton(text="✏️ تعديل البيانات", callback_data="order:edit"),
            ],
            [
                InlineKeyboardButton(text="❌ إلغاء", callback_data="order:cancel")
            ]
        ]
    )

def get_payment_methods_keyboard(methods: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Select payment method keyboard."""
    buttons = []
    method_labels = {
        "vodafone": "📱 Vodafone Cash",
        "binance": "🟡 Binance ID",
        "ton": "🪙 TONKeeper"
    }
    for m in methods:
        key = m["key"]
        label = method_labels.get(key, m["name"])
        buttons.append([InlineKeyboardButton(text=label, callback_data=f"pay:{key}")])

    buttons.append([InlineKeyboardButton(text="❌ إلغاء الطلب", callback_data="order:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_manual_payment_keyboard() -> InlineKeyboardMarkup:
    """Keyboard shown for manual payments (Vodafone/Binance)."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ تم الدفع", callback_data="pay:submitted_proof")],
            [InlineKeyboardButton(text="❌ إلغاء الطلب", callback_data="order:cancel")]
        ]
    )

def get_ton_payment_keyboard(wallet_address: str = "", ton_amount: float = 0.0, memo: str = "") -> InlineKeyboardMarkup:
    """Keyboard for TON payment screen with direct wallet link, auto verification, and screenshot proof upload."""
    nanotons = int(round(ton_amount * 1_000_000_000)) if ton_amount > 0 else 0
    tonkeeper_url = f"https://app.tonkeeper.com/transfer/{wallet_address}?amount={nanotons}&text={memo}"
    
    buttons = []
    if wallet_address and memo:
        buttons.append([InlineKeyboardButton(text="💎 فتح محفظة TONKeeper للدفع", url=tonkeeper_url)])
    
    buttons.append([InlineKeyboardButton(text="⚡ التحقق التلقائي من الدفع (On-Chain)", callback_data="pay:check_ton")])
    buttons.append([InlineKeyboardButton(text="📸 إرسال صورة إثبات التحويل (Screenshot)", callback_data="pay:submitted_proof")])
    buttons.append([InlineKeyboardButton(text="❌ إلغاء الطلب", callback_data="order:cancel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_user_orders_keyboard(orders: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """List user orders with details trigger."""
    buttons = []
    for order in orders[:10]: # Limit top 10 recent
        text = f"📦 #{order['order_number']} - {order['product_name']} ({order['price_egp']} ج)"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"order_view:{order['order_number']}")])
    
    buttons.append([InlineKeyboardButton(text="⬅️ القائمة الرئيسية", callback_data="nav:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_rating_keyboard(order_number: str) -> InlineKeyboardMarkup:
    """Keyboard for rating completed order."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⭐ ⭐ ⭐ ⭐ ⭐ (ممتاز 5/5)", callback_data=f"rate:{order_number}:5")],
            [
                InlineKeyboardButton(text="⭐ ⭐ ⭐ ⭐ (جيد 4/5)", callback_data=f"rate:{order_number}:4"),
                InlineKeyboardButton(text="⭐ ⭐ ⭐ (مقبول 3/5)", callback_data=f"rate:{order_number}:3"),
            ],
            [
                InlineKeyboardButton(text="⭐ ⭐ (سيئ 2/5)", callback_data=f"rate:{order_number}:2"),
                InlineKeyboardButton(text="⭐ (سيئ جداً 1/5)", callback_data=f"rate:{order_number}:1"),
            ],
            [InlineKeyboardButton(text="⬅️ القائمة الرئيسية", callback_data="nav:main")]
        ]
    )

