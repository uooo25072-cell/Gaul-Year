import sys
import json
import asyncio
from database import init_db, get_db
from repositories.products import ProductRepository
from repositories.settings import SettingsRepository
from repositories.orders import OrderRepository
from repositories.users import UserRepository
from repositories.admin_logs import AdminLogRepository

async def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No action specified"}))
        return

    action = sys.argv[1]

    if action == "init":
        await init_db()
        print(json.dumps({"status": "ok", "message": "DB Initialized"}))

    elif action == "get_products":
        products = await ProductRepository.get_all_products(active_only=False)
        result = []
        for p in products:
            pkgs = await ProductRepository.get_packages_by_product_key(p["key"], active_only=False)
            result.append({
                "key": p["key"],
                "name": p["name"],
                "data_label": p["data_label"],
                "is_active": p["is_active"],
                "packages": pkgs
            })
        print(json.dumps(result, ensure_ascii=False))

    elif action == "get_settings":
        settings = await SettingsRepository.get_all_settings()
        print(json.dumps(settings, ensure_ascii=False))

    elif action == "set_setting":
        key = sys.argv[2]
        val = sys.argv[3]
        await SettingsRepository.set_setting(key, val)
        print(json.dumps({"status": "ok", "key": key, "value": val}))

    elif action == "get_stats":
        stats = await OrderRepository.get_stats()
        user_count = await UserRepository.count_users()
        stats["total_users"] = user_count
        print(json.dumps(stats, ensure_ascii=False))

    elif action == "create_order":
        # args: user_id, product_key, package_id, customer_data, payment_method
        user_id = int(sys.argv[2])
        product_key = sys.argv[3]
        package_id = int(sys.argv[4])
        customer_data = sys.argv[5]
        payment_method = sys.argv[6]

        product = await ProductRepository.get_product_by_key(product_key)
        package = await ProductRepository.get_package_by_id(package_id)

        if not product or not package:
            print(json.dumps({"error": "Product or package not found"}))
            return

        # Ensure user exists in DB
        await UserRepository.add_or_update_user(user_id, "user", "Simulator User")

        import random
        from datetime import datetime
        now = datetime.utcnow()
        order_number = f"GZ-{now.strftime('%y%m%d')}-{random.randint(1000, 9999)}"

        ton_rate_str = await SettingsRepository.get_setting("ton_egp_rate", "120.0")
        try:
            ton_rate = float(ton_rate_str)
        except ValueError:
            ton_rate = 120.0
        ton_amount = round(package["price_egp"] / ton_rate, 4) if ton_rate > 0 else 0.0

        memo = f"GZ{random.randint(100000, 999999)}" if payment_method == "ton" else None

        order = await OrderRepository.create_order(
            order_number=order_number,
            user_id=user_id,
            product_id=product["id"],
            package_id=package["id"],
            product_name=product["name"],
            package_name=package["name"],
            customer_data=customer_data,
            price_egp=package["price_egp"],
            payment_method=payment_method,
            ton_amount=ton_amount,
            memo=memo
        )
        print(json.dumps(order, ensure_ascii=False))

    elif action == "get_user_orders":
        user_id = int(sys.argv[2])
        orders = await OrderRepository.get_user_orders(user_id)
        print(json.dumps(orders, ensure_ascii=False))

    elif action == "get_all_orders":
        orders = await OrderRepository.get_all_orders(100)
        print(json.dumps(orders, ensure_ascii=False))

    elif action == "update_order_status":
        order_number = sys.argv[2]
        status = sys.argv[3]
        reason = sys.argv[4] if len(sys.argv) > 4 else None

        order = await OrderRepository.get_order_by_number(order_number)
        if not order:
            print(json.dumps({"error": "Order not found"}))
            return

        await OrderRepository.update_status(order["id"], status, reason)
        await AdminLogRepository.log_action(12345678, f"update_status_{status}", order_number, reason or "")
        print(json.dumps({"status": "ok", "order_number": order_number, "new_status": status}))

    elif action == "update_order_receipt":
        order_number = sys.argv[2]
        receipt_file_id = sys.argv[3]

        order = await OrderRepository.get_order_by_number(order_number)
        if not order:
            print(json.dumps({"error": "Order not found"}))
            return

        await OrderRepository.update_receipt(order["id"], receipt_file_id)
        print(json.dumps({"status": "ok", "order_number": order_number}))

    elif action == "add_package":
        product_key = sys.argv[2]
        name = sys.argv[3]
        price_egp = float(sys.argv[4])
        pkg = await ProductRepository.add_package(product_key, name, price_egp)
        print(json.dumps(pkg, ensure_ascii=False))

    elif action == "toggle_package":
        package_id = int(sys.argv[2])
        res = await ProductRepository.toggle_package_status(package_id)
        print(json.dumps({"status": "ok", "package_id": package_id}))

    elif action == "delete_package":
        package_id = int(sys.argv[2])
        res = await ProductRepository.delete_package(package_id)
        print(json.dumps({"status": "ok", "package_id": package_id}))

    elif action == "get_users":
        users = await UserRepository.get_all_users()
        print(json.dumps(users, ensure_ascii=False))

    elif action == "toggle_ban":
        telegram_id = int(sys.argv[2])
        is_banned = await UserRepository.is_banned(telegram_id)
        if is_banned:
            await UserRepository.unban_user(telegram_id)
            print(json.dumps({"status": "ok", "telegram_id": telegram_id, "is_banned": False}))
        else:
            reason = sys.argv[3] if len(sys.argv) > 3 else "Banned via Admin"
            await UserRepository.ban_user(telegram_id, reason)
            print(json.dumps({"status": "ok", "telegram_id": telegram_id, "is_banned": True}))

    elif action == "get_logs":
        logs = await AdminLogRepository.get_recent_logs(50)
        print(json.dumps(logs, ensure_ascii=False))

    elif action == "check_ton_payment":
        order_number = sys.argv[2]
        order = await OrderRepository.get_order_by_number(order_number)
        if not order:
            print(json.dumps({"success": False, "message": "الطلب غير موجود."}, ensure_ascii=False))
            return
        
        from services.ton_service import TonService
        wallet_address = await SettingsRepository.get_setting("ton_wallet")
        memo = order.get("memo")
        expected_ton = order.get("ton_amount", 0.0)

        if not wallet_address or not memo:
            print(json.dumps({"success": False, "message": "بيانات المحفظة أو الميمو غير مكتملة."}, ensure_ascii=False))
            return

        is_found, tx_hash = await TonService.check_onchain_payment(wallet_address, memo, expected_ton)

        if is_found and tx_hash:
            await TonService.register_transaction(order["id"], tx_hash, expected_ton)
            await OrderRepository.attach_tx_hash(order["id"], tx_hash)
            await OrderRepository.update_status(order["id"], "payment_confirmed")
            print(json.dumps({
                "success": True,
                "message": "✅ تم التحقق من وصول الدفع بنجاح عبر شبكة TON!",
                "tx_hash": tx_hash,
                "order_number": order_number
            }, ensure_ascii=False))
        else:
            print(json.dumps({
                "success": False,
                "message": "❌ لم تصل الفلوس إلى المحفظة بعد.\n\nيرجى التأكد من إتمام التحويل مع إضافة الـ Memo المطلوب، ثم الانتظار لعدة ثوانٍ والمحاولة مرة أخرى.",
                "order_number": order_number
            }, ensure_ascii=False))

    elif action == "refresh_ton_rate":
        from services.ton_service import TonService
        res = await TonService.update_ton_rate()
        print(json.dumps(res, ensure_ascii=False))

    elif action == "rate_order":
        order_number = sys.argv[2]
        rating = int(sys.argv[3])
        comment = sys.argv[4] if len(sys.argv) > 4 else None
        await OrderRepository.rate_order(order_number, rating, comment)
        print(json.dumps({"status": "ok", "order_number": order_number, "rating": rating}, ensure_ascii=False))

    else:
        print(json.dumps({"error": f"Unknown action {action}"}))

if __name__ == "__main__":
    asyncio.run(main())
