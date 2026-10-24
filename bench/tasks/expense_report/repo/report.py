"""Expense report helpers."""
from decimal import Decimal


def summarize(path) -> dict[str, Decimal]:
    """Return {category: total} for the expenses CSV at `path`."""
    raise NotImplementedError
