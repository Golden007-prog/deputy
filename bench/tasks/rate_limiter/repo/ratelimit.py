"""Rate limiting for the API gateway."""


class RateLimiter:
    """Allow at most `limit` calls per `window` seconds for each key."""

    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window

    def allow(self, key: str, now: float) -> bool:
        raise NotImplementedError
