Implement `RateLimiter.allow` in `ratelimit.py` as a sliding-window rate limiter.

- A call for `key` at time `now` (seconds, a float) is allowed if fewer than `limit` calls for
  that key were allowed in the window `(now - window, now]`.
- Rejected calls do not count toward the limit.
- Keys are independent of each other.
- `__init__` must raise `ValueError` if `limit` or `window` is not positive.
- Memory per key must stay bounded by `limit`, however many calls are made.

Run the tests with `python -m pytest -q`.
