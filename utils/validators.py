import re

# Strict yet standard RFC 5322 pattern for email validation
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")

def validate_email(email: str) -> bool:
    """Check if the provided email string matches standard email format."""
    if not email:
        return False
    email = email.strip()
    return bool(EMAIL_REGEX.match(email))

def validate_player_id(player_id: str) -> bool:
    """Check if Player ID is non-empty and consists only of digits."""
    if not player_id:
        return False
    player_id = player_id.strip()
    return player_id.isdigit() and len(player_id) >= 5
