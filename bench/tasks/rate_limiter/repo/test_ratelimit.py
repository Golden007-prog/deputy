from ratelimit import RateLimiter


def test_allows_up_to_limit():
    limiter = RateLimiter(2, 10)
    assert limiter.allow("a", 0)
    assert limiter.allow("a", 1)
    assert not limiter.allow("a", 2)
