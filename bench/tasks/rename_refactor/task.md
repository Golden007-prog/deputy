Rename the function `get_usr` to `get_user` everywhere in the `accounts` package and in the
tests.

- Export `get_user` from the `accounts` package instead of `get_usr`.
- Keep `get_usr` importable from `accounts.users` as a deprecated alias: calling it emits a
  `DeprecationWarning` and returns the same result as `get_user`.
- No other code should call `get_usr` any more.
- Don't change any other behavior.

Run the tests with `python -m pytest -q`.
