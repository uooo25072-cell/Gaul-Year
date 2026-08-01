import random
import time

def generate_order_number() -> str:
    """Generate a unique human-readable order identifier."""
    timestamp = int(time.time()) % 1000000
    rand_part = random.randint(100, 999)
    return f"GZ-{timestamp}{rand_part}"

def generate_memo(order_number: str) -> str:
    """Generate unique TON payment memo for order matching."""
    clean_num = order_number.replace("GZ-", "")
    return f"GAMEZONE-ORDER-{clean_num}"
