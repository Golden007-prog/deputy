Implement `summarize(path)` in `report.py`.

The file is a UTF-8 CSV (files exported from Excel may start with a byte order mark) with a
header row. The header contains at least `category` and `amount` columns, in any order, possibly
with other columns. Return a dict that maps each category to its total amount as a `Decimal`
rounded to 2 places with `ROUND_HALF_UP`.

- Strip whitespace around category names. Categories are case-insensitive and are returned in
  lower case.
- Skip rows whose amount is empty.
- Amounts may have a leading `$` and thousands separators, such as `"$1,234.50"` (quoted in the
  CSV, since it contains a comma).
- Raise `ValueError` for any other amount that can't be parsed. The message must include the
  line number in the file (the header is line 1).

Run the tests with `python -m pytest -q`.
