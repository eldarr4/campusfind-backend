"""Manual validation so every failure maps to the same structured error."""
import re
from datetime import date, datetime

TYPES = ["lost", "found"]
CATEGORIES = ["electronics", "documents", "keys", "bags", "clothing", "accessories", "other"]
STATUSES = ["active", "resolved"]
EDITABLE_FIELDS = ["type", "title", "description", "category", "location", "date", "status", "secretDetail"]
READ_ONLY_FIELDS = ["id", "ownerId", "createdAt", "updatedAt"]

_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _parse_date(value):
    if not isinstance(value, str) or not _DATE.match(value):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _one_of(allowed):
    return ", ".join(allowed)


def validate_item_body(body):
    """Validate a POST/PUT body. Returns a list of {field, message}; empty means valid.

    PUT replaces the editable fields, so POST and PUT share the same rules.
    """
    if not isinstance(body, dict):
        return [{"field": "body", "message": "Request body must be a JSON object."}]

    errors = []
    for key in body:
        if key in READ_ONLY_FIELDS:
            errors.append({"field": key, "message": "This field is read-only and cannot be set."})
        elif key not in EDITABLE_FIELDS:
            errors.append({"field": key, "message": f"Unknown field. Allowed fields: {_one_of(EDITABLE_FIELDS)}."})

    item_type = body.get("type")
    if item_type not in TYPES:
        errors.append({"field": "type", "message": f"Type is required and must be one of: {_one_of(TYPES)}."})

    title = body.get("title")
    if not isinstance(title, str) or not 3 <= len(title.strip()) <= 100:
        errors.append({"field": "title", "message": "Title is required and must be a string of 3 to 100 characters."})

    description = body.get("description")
    if description is not None and (not isinstance(description, str) or len(description) > 500):
        errors.append({"field": "description", "message": "Description must be a string of at most 500 characters."})

    if body.get("category") not in CATEGORIES:
        errors.append({"field": "category", "message": f"Category is required and must be one of: {_one_of(CATEGORIES)}."})

    location = body.get("location")
    if not isinstance(location, str) or not 2 <= len(location.strip()) <= 100:
        errors.append({"field": "location", "message": "Location is required and must be a string of 2 to 100 characters."})

    parsed = _parse_date(body.get("date"))
    if parsed is None:
        errors.append({"field": "date", "message": "Date is required and must be a valid date in YYYY-MM-DD format."})
    elif parsed > date.today():
        errors.append({"field": "date", "message": "Date cannot be in the future."})

    status = body.get("status")
    if status is not None and status not in STATUSES:
        errors.append({"field": "status", "message": f"Status must be one of: {_one_of(STATUSES)}."})

    secret = body.get("secretDetail")
    if secret is not None:
        if not isinstance(secret, str) or not 1 <= len(secret.strip()) <= 200:
            errors.append({"field": "secretDetail", "message": "Secret detail must be a string of 1 to 200 characters."})
        elif item_type == "lost":
            errors.append({"field": "secretDetail", "message": "Secret detail can only be set on found items."})

    return errors


def validate_list_query(params):
    """Validate GET /items query parameters. Returns (errors, filters)."""
    errors, filters = [], {"page": 1, "perPage": 10}

    for name, low, high in (("page", 1, 100000), ("perPage", 1, 100)):
        raw = params.get(name)
        if raw is None:
            continue
        if raw.isdigit() and low <= int(raw) <= high:
            filters[name] = int(raw)
        else:
            errors.append({"field": name, "message": f"{name} must be an integer between {low} and {high}."})

    for name, allowed in (("type", TYPES), ("category", CATEGORIES), ("status", STATUSES)):
        raw = params.get(name)
        if raw is None:
            continue
        if raw in allowed:
            filters[name] = raw
        else:
            errors.append({"field": name, "message": f"{name} must be one of: {_one_of(allowed)}."})

    raw = params.get("date")
    if raw is not None:
        if _parse_date(raw) is None:
            errors.append({"field": "date", "message": "date must be a valid date in YYYY-MM-DD format."})
        else:
            filters["date"] = raw

    for name in ("location", "search", "ownerId"):
        raw = params.get(name)
        if raw is not None:
            filters[name] = raw.strip().lower() if name != "ownerId" else raw.strip()

    return errors, filters
