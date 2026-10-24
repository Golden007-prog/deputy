"""Plan prices."""
from .users import get_usr

PRICES = {"free": 0, "pro": 12}


def monthly_price(user_id):
    """Monthly price in dollars for the user's plan."""
    return PRICES[get_usr(user_id)["plan"]]
