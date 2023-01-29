from .exceptions import MisconfiguredException
from .types import Edge


def validate_user_id(value: str):
    if not value.isdigit():
        raise MisconfiguredException("User ID must be be a string of integers.")
    return value


def validate_edge(value: str):
    if value not in Edge.__args__:
        raise MisconfiguredException(f"Edge type must be one of {Edge.__args__}.")
    return value
