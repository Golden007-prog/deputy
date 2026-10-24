"""Messages sent to users."""
from . import users


def greeting(user_id):
    """Greeting line for the top of an email."""
    user = users.get_usr(user_id)
    return f"Hi {user['name']}!"
