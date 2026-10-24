import pytest

from ratelimit import RateLimiter


def test_window_is_half_open():
    limiter = RateLimiter(1, 10)
    assert limiter.allow("a", 0)
    assert not limiter.allow("a", 9.999)
    assert limiter.allow("a", 10)


def test_rejected_calls_do_not_count():
    limiter = RateLimiter(1, 10)
    assert limiter.allow("a", 0)
    assert not limiter.allow("a", 5)
    assert limiter.allow("a", 10)


def test_keys_are_independent():
    limiter = RateLimiter(1, 10)
    assert limiter.allow("a", 0)
    assert limiter.allow("b", 0)
    assert not limiter.allow("a", 1)


def test_same_timestamp():
    limiter = RateLimiter(3, 1)
    assert [limiter.allow("a", 5) for _ in range(4)] == [True, True, True, False]


def test_sliding_not_fixed_window():
    limiter = RateLimiter(2, 10)
    assert limiter.allow("a", 8)
    assert limiter.allow("a", 9)
    assert not limiter.allow("a", 11)
    assert limiter.allow("a", 18.5)


@pytest.mark.parametrize("limit, window", [(0, 10), (-1, 10), (1, 0), (1, -5)])
def test_rejects_bad_config(limit, window):
    with pytest.raises(ValueError):
        RateLimiter(limit, window)


def test_many_calls_stay_fast():
    limiter = RateLimiter(5, 1)
    allowed = sum(limiter.allow("a", i * 0.01) for i in range(200_000))
    assert allowed == 200_000 * 5 // 100
