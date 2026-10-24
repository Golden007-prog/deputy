from decimal import Decimal

import pytest

from report import summarize


def write(tmp_path, text, encoding="utf-8"):
    path = tmp_path / "expenses.csv"
    path.write_text(text, encoding=encoding)
    return path


def test_quoted_thousands_and_dollar(tmp_path):
    path = write(tmp_path, 'category,amount\nrent,"$1,234.50"\nrent,$10\n')
    assert summarize(path) == {"rent": Decimal("1244.50")}


def test_column_order_and_extra_columns(tmp_path):
    path = write(tmp_path, "date,amount,note,category\n2026-01-01,5,lunch,food\n")
    assert summarize(path) == {"food": Decimal("5.00")}


def test_categories_case_insensitive_and_stripped(tmp_path):
    path = write(tmp_path, "category,amount\n Food ,1\nFOOD,2\nfood,3\n")
    assert summarize(path) == {"food": Decimal("6.00")}


def test_empty_amount_skipped(tmp_path):
    path = write(tmp_path, "category,amount\nfood,\nfood,4\ntravel,\n")
    assert summarize(path) == {"food": Decimal("4.00")}


def test_round_half_up(tmp_path):
    path = write(tmp_path, "category,amount\nfood,0.125\nbooks,2.675\n")
    result = summarize(path)
    assert result == {"food": Decimal("0.13"), "books": Decimal("2.68")}
    assert all(isinstance(value, Decimal) for value in result.values())


def test_byte_order_mark(tmp_path):
    path = write(tmp_path, "category,amount\nfood,1\n", encoding="utf-8-sig")
    assert summarize(path) == {"food": Decimal("1.00")}


def test_bad_amount_reports_line(tmp_path):
    path = write(tmp_path, "category,amount\nfood,1\nfood,abc\n")
    with pytest.raises(ValueError, match="3"):
        summarize(path)
