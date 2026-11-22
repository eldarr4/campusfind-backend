"""Mock token authentication. No login, no passwords, no user storage."""
import re
from fastapi import Request
from .errors import ApiError

USERS = {
    "user-a-token": {"id": "user-a", "name": "User A", "role": "user"},
    "user-b-token": {"id": "user-b", "name": "User B", "role": "user"},
    "admin-token": {"id": "admin", "name": "Administrator", "role": "admin"},
}

_BEARER = re.compile(r"^Bearer\s+(\S+)$", re.IGNORECASE)


def current_user(request: Request):
    """FastAPI dependency: returns the user or raises 401."""
    header = request.headers.get("authorization", "").strip()
    match = _BEARER.match(header)
    user = USERS.get(match.group(1)) if match else None
    if user is None:
        raise ApiError("UNAUTHORIZED")
    return user


def is_admin(user):
    return user["role"] == "admin"
