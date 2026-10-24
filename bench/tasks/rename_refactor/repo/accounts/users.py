"""User lookups."""

_USERS = {
    1: {"id": 1, "name": "Ada", "email": "ada@example.com", "plan": "pro"},
    2: {"id": 2, "name": "Lin", "email": "lin@example.com", "plan": "free"},
}


def get_usr(user_id):
    """Return a copy of the user record for `user_id`, or raise KeyError."""
    return dict(_USERS[user_id])
