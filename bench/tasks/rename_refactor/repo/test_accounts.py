import pytest

from accounts import describe, get_usr, greeting, monthly_price


def test_lookup():
    assert get_usr(1)["name"] == "Ada"


def test_lookup_returns_copy():
    get_usr(1)["name"] = "changed"
    assert get_usr(1)["name"] == "Ada"


def test_unknown_user():
    with pytest.raises(KeyError):
        get_usr(99)


def test_helpers():
    assert monthly_price(1) == 12
    assert greeting(2) == "Hi Lin!"
    assert describe(1) == "Ada <ada@example.com> on pro"
