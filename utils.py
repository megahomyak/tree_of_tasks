from typing import Any


def is_convertible_to_int(some_value: Any) -> bool:
    try:
        int(some_value)
    except (ValueError, TypeError):
        return False
    return True
