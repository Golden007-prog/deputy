A user reports that `free_slots` in `ranges.py` sometimes returns slots that overlap existing
bookings. Find and fix the bugs in `ranges.py`.

- Ranges are half-open `[start, end)` pairs of integers.
- `merge_ranges` must accept ranges in any order. Overlapping or touching ranges, such as
  `(1, 3)` and `(3, 5)`, merge into one. Ignore empty ranges (`start == end`) and raise
  `ValueError` when `start > end`.
- `free_slots` must only return gaps inside `[day_start, day_end)`, even when bookings start
  before the day or end after it.
- Keep the function signatures.

Run the tests with `python -m pytest -q`.
