"""Admin panel helpers."""
from .users import get_usr


def describe(user_id):
    """One-line description used in the admin panel (looked up with get_usr)."""
    user = get_usr(user_id)
    return f"{user['name']} <{user['email']}> on {user['plan']}"
