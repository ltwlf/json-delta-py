"""Internal utility functions for json-delta."""

from typing import Any


def json_equal(a: Any, b: Any) -> bool:
    """Compare two values using JSON value equality.

    JSON has a single "number" type, so int and float compare as numbers.
    Python's bool is a subclass of int, but JSON boolean and number are
    distinct types — True must NOT equal 1.

    Rules:
    - bool vs bool: normal comparison
    - bool vs anything else: False (even bool vs int)
    - number (int/float, excluding bool) vs number: numeric equality
    - all other types: exact type match + value equality
    - dicts: unordered key-value comparison (Python == handles this)
    - lists: ordered element-by-element comparison
    """
    # Handle bools first — bool is a subclass of int in Python,
    # but JSON treats boolean and number as distinct types.
    a_is_bool = isinstance(a, bool)
    b_is_bool = isinstance(b, bool)

    if a_is_bool or b_is_bool:
        # Both must be bool for equality
        if a_is_bool and b_is_bool:
            return a is b
        return False

    # Both numbers (int or float, but not bool — already handled above)
    a_is_num = isinstance(a, (int, float))
    b_is_num = isinstance(b, (int, float))

    if a_is_num and b_is_num:
        return a == b  # type: ignore[no-any-return]

    # One is a number and the other is not — different types
    if a_is_num != b_is_num:
        return False

    # For everything else (str, None, dict, list): require same type + value equality
    if type(a) is not type(b):
        return False

    return a == b  # type: ignore[no-any-return]


def json_type_of(value: Any) -> str:
    """Return the JSON type name of a Python value.

    Returns one of: "object", "array", "string", "number", "boolean", "null".
    Raises TypeError for non-JSON types.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    raise TypeError(f"Not a JSON type: {type(value).__name__}")
