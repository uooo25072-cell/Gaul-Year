from typing import Dict

STATUS_ARABIC_MAP: Dict[str, str] = {
    "pending_payment": "⏳ في انتظار الدفع",
    "payment_review": "🔍 جاري مراجعة الدفع",
    "payment_confirmed": "💳 تم تأكيد الدفع",
    "processing": "⚙️ جاري التنفيذ",
    "completed": "✅ تم الشحن",
    "rejected": "❌ مرفوض",
    "cancelled": "🚫 ملغي",
    "expired": "⌛ انتهت مهلة الدفع",
}

STATUS_BADGE_MAP: Dict[str, str] = {
    "pending_payment": "🟡 في انتظار الدفع",
    "payment_review": "🔵 قيد المراجعة",
    "payment_confirmed": "🟢 تم التوثيق",
    "processing": "⚙️ جاري التنفيذ",
    "completed": "✅ مكتمل",
    "rejected": "🔴 مرفوض",
    "cancelled": "⚪ ملغي",
    "expired": "⌛ منتهي",
}

def get_arabic_status(status: str) -> str:
    """Return human-readable Arabic label for order status."""
    return STATUS_ARABIC_MAP.get(status, status)

def format_price(amount: float) -> str:
    """Format numeric price into clean string with EGP symbol."""
    if amount == int(amount):
        return f"{int(amount)} جنيه"
    return f"{amount:.2f} جنيه"

def format_order_summary(
    product_name: str,
    package_name: str,
    customer_data_label: str,
    customer_data_val: str,
    price_egp: float,
    notice: str = ""
) -> str:
    """Build standardized order review message string."""
    text = (
        "🧾 <b>مراجعة الطلب</b>\n\n"
        f"🎮 <b>المنتج:</b> {product_name}\n"
        f"💎 <b>الباقة:</b> {package_name}\n"
        f"🆔 <b>{customer_data_label}:</b> <code>{customer_data_val}</code>\n"
        f"💰 <b>السعر:</b> {format_price(price_egp)}\n\n"
    )
    if notice:
        text += f"{notice}\n\n"
    text += "⚠️ <b>تأكد من صحة البيانات قبل تأكيد الطلب.</b>"
    return text
