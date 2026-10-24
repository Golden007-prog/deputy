from decimal import Decimal

from report import summarize


def test_simple(tmp_path):
    path = tmp_path / "expenses.csv"
    path.write_text("category,amount\nfood,10.50\nfood,2.25\ntravel,100\n", encoding="utf-8")
    assert summarize(path) == {"food": Decimal("12.75"), "travel": Decimal("100.00")}
