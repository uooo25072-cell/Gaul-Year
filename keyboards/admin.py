from typing import List, Dict, Any
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    """Admin Panel Dashboard main menu."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 الإحصائيات", callback_data="adm:stats"),
                InlineKeyboardButton(text="📦 إدارة الطلبات", callback_data="adm:orders_menu"),
            ],
            [
                InlineKeyboardButton(text="🛒 المنتجات والباقات", callback_data="adm:products_menu"),
                InlineKeyboardButton(text="💳 طرق الدفع", callback_data="adm:payments_menu"),
            ],
            [
                InlineKeyboardButton(text="👥 إدارة المستخدمين", callback_data="adm:users_menu"),
                InlineKeyboardButton(text="📢 إرسال إذاعة", callback_data="adm:broadcast_menu"),
            ],
            [
                InlineKeyboardButton(text="📜 سجل الأدمن", callback_data="adm:logs"),
                InlineKeyboardButton(text="🛠️ وضع الصيانة", callback_data="adm:maintenance_toggle"),
            ],
            [
                InlineKeyboardButton(text="💾 النسخ الاحتياطي", callback_data="adm:backup_menu"),
                InlineKeyboardButton(text="⚙️ الإعدادات", callback_data="adm:settings_menu"),
            ],
            [
                InlineKeyboardButton(text="⬅️ القائمة الرئيسية للمتجر", callback_data="nav:main")
            ]
        ]
    )

def get_order_action_keyboard(order_number: str, current_status: str) -> InlineKeyboardMarkup:
    """Keyboard for admin actions on an order."""
    buttons = []
    
    if current_status == "payment_review" or current_status == "pending_payment":
        buttons.append([
            InlineKeyboardButton(text="✅ قبول الدفع", callback_data=f"adm_act:approve:{order_number}"),
            InlineKeyboardButton(text="❌ رفض الدفع", callback_data=f"adm_act:reject:{order_number}")
        ])
    elif current_status == "payment_confirmed":
        buttons.append([
            InlineKeyboardButton(text="⚙️ جاري التنفيذ", callback_data=f"adm_act:process:{order_number}")
        ])
        buttons.append([
            InlineKeyboardButton(text="❌ رفض الطلب", callback_data=f"adm_act:reject:{order_number}")
        ])
    elif current_status == "processing":
        buttons.append([
            InlineKeyboardButton(text="📦 تم الشحن", callback_data=f"adm_act:complete:{order_number}")
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ إدارة الطلبات", callback_data="adm:orders_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_rejection_reasons_keyboard(order_number: str) -> InlineKeyboardMarkup:
    """Predefined rejection reasons for admin."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="إيصال غير واضح أو مزور", callback_data=f"adm_rej_reason:{order_number}:fake")],
            [InlineKeyboardButton(text="المبلغ المحول غير مكتمل", callback_data=f"adm_rej_reason:{order_number}:incomplete")],
            [InlineKeyboardButton(text="لم يصل التحويل للحساب", callback_data=f"adm_rej_reason:{order_number}:not_received")],
            [InlineKeyboardButton(text="بيانات الحساب غير صحيحة", callback_data=f"adm_rej_reason:{order_number}:bad_data")],
            [InlineKeyboardButton(text="✍️ كتابة سبب آخر", callback_data=f"adm_rej_reason:{order_number}:custom")],
            [InlineKeyboardButton(text="❌ إلغاء", callback_data="adm:orders_menu")]
        ]
    )

def get_orders_filter_keyboard() -> InlineKeyboardMarkup:
    """Filter orders list by status."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 قيد المراجعة", callback_data="adm_filter:payment_review"),
                InlineKeyboardButton(text="⚙️ قيد التنفيذ", callback_data="adm_filter:processing"),
            ],
            [
                InlineKeyboardButton(text="⏳ في انتظار الدفع", callback_data="adm_filter:pending_payment"),
                InlineKeyboardButton(text="💳 تم توثيق الدفع", callback_data="adm_filter:payment_confirmed"),
            ],
            [
                InlineKeyboardButton(text="✅ الطلبات المكتملة", callback_data="adm_filter:completed"),
                InlineKeyboardButton(text="❌ الطلبات المرفوضة", callback_data="adm_filter:rejected"),
            ],
            [
                InlineKeyboardButton(text="🔍 بحث برقم الطلب", callback_data="adm_search:order"),
                InlineKeyboardButton(text="👤 بحث بـ Telegram ID", callback_data="adm_search:user"),
            ],
            [
                InlineKeyboardButton(text="⬅️ لوحة تحكم الأدمن", callback_data="adm:main")
            ]
        ]
    )

def get_admin_packages_keyboard(packages: List[Dict[str, Any]], product_key: str) -> InlineKeyboardMarkup:
    """Manage packages list keyboard."""
    buttons = []
    for pkg in packages:
        status = "🟢" if pkg["is_active"] else "🔴"
        text = f"{status} {pkg['name']} ({pkg['price_egp']} ج)"
        buttons.append([InlineKeyboardButton(text=text, callback_data=f"adm_pkg_edit:{pkg['id']}")])
    
    buttons.append([InlineKeyboardButton(text="➕ إضافة باقة جديدة", callback_data=f"adm_pkg_add:{product_key}")])
    buttons.append([InlineKeyboardButton(text="⬅️ قائمة المنتجات", callback_data="adm:products_menu")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_package_edit_actions_keyboard(package_id: int) -> InlineKeyboardMarkup:
    """Actions menu for modifying a specific package."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✏️ تعديل الاسم", callback_data=f"adm_pkg_act:name:{package_id}"),
                InlineKeyboardButton(text="💰 تعديل السعر", callback_data=f"adm_pkg_act:price:{package_id}"),
            ],
            [
                InlineKeyboardButton(text="🔄 تفعيل/تعطيل", callback_data=f"adm_pkg_act:toggle:{package_id}"),
                InlineKeyboardButton(text="🗑️ حذف الباقة", callback_data=f"adm_pkg_act:delete:{package_id}"),
            ],
            [
                InlineKeyboardButton(text="⬅️ رجوع للمنتجات", callback_data="adm:products_menu")
            ]
        ]
    )

def get_payment_edit_keyboard() -> InlineKeyboardMarkup:
    """Select payment configuration to edit."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📱 تعديل Vodafone Cash", callback_data="adm_pay_edit:vodafone"),
            ],
            [
                InlineKeyboardButton(text="🟡 تعديل Binance ID", callback_data="adm_pay_edit:binance"),
            ],
            [
                InlineKeyboardButton(text="🪙 تعديل عنوان TONKeeper", callback_data="adm_pay_edit:ton"),
            ],
            [
                InlineKeyboardButton(text="🔄 تحديث سعر TON/EGP فورًا", callback_data="adm_pay_edit:refresh_ton"),
            ],
            [
                InlineKeyboardButton(text="⬅️ لوحة تحكم الأدمن", callback_data="adm:main")
            ]
        ]
    )

def get_broadcast_type_keyboard() -> InlineKeyboardMarkup:
    """Select broadcast content type."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 رسالة نصية", callback_data="adm_bcast:text"),
                InlineKeyboardButton(text="🖼️ صورة مع نص", callback_data="adm_bcast:photo"),
            ],
            [
                InlineKeyboardButton(text="🎥 فيديو مع نص", callback_data="adm_bcast:video"),
            ],
            [
                InlineKeyboardButton(text="❌ إلغاء", callback_data="adm:main")
            ]
        ]
    )

def get_confirm_broadcast_keyboard() -> InlineKeyboardMarkup:
    """Confirm broadcast before sending."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🚀 تأكيد وبدء الإذاعة", callback_data="adm_bcast:confirm_start"),
                InlineKeyboardButton(text="❌ إلغاء الإذاعة", callback_data="adm:main")
            ]
        ]
    )

def get_restore_confirm_keyboard() -> InlineKeyboardMarkup:
    """Backup restoration confirmation."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأكيد الاستعادة", callback_data="adm_backup:confirm_restore"),
                InlineKeyboardButton(text="❌ إلغاء", callback_data="adm:main")
            ]
        ]
    )
