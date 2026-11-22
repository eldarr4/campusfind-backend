"""CRUD for the main resource: lost and found items."""
import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Request

from .. import data
from ..auth import current_user, is_admin
from ..errors import ApiError
from ..responses import success
from ..validation import validate_item_body, validate_list_query

router = APIRouter(prefix="/api/v1/items", tags=["items"])

MAX_BODY_BYTES = 10_000


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


async def _read_json(request: Request):
    raw = await request.body()
    if len(raw) > MAX_BODY_BYTES:
        raise ApiError("PAYLOAD_TOO_LARGE")
    if not raw.strip():
        raise ApiError("VALIDATION_ERROR", details=[{"field": "body", "message": "A JSON object body is required."}])
    try:
        return json.loads(raw)
    except ValueError:
        raise ApiError("INVALID_JSON")


def _find(item_id):
    return next((i for i in data.ITEMS if i["id"] == item_id), None)


def _get_accessible(item_id, user):
    """Return the item, or raise 404.

    Another student's item returns 404 (not 403) so the API never confirms
    that a private post exists. See docs/API.md, "403 vs 404".
    """
    item = _find(item_id)
    if item is None or (not is_admin(user) and item["ownerId"] != user["id"]):
        raise ApiError("NOT_FOUND", f"Item '{item_id}' was not found.")
    return item


def _clean(body, default_status="active"):
    """Normalize a validated body into the stored editable fields."""
    secret = body.get("secretDetail")
    description = body.get("description")
    return {
        "type": body["type"],
        "title": body["title"].strip(),
        "description": description.strip() if isinstance(description, str) else "",
        "category": body["category"],
        "location": body["location"].strip(),
        "date": body["date"],
        "status": body.get("status", default_status),
        "secretDetail": secret.strip() if isinstance(secret, str) else None,
    }


@router.get("")
def list_items(request: Request, user=Depends(current_user)):
    errors, f = validate_list_query(request.query_params)
    if errors:
        raise ApiError("VALIDATION_ERROR", details=errors)

    items = data.ITEMS
    if not is_admin(user):
        items = [i for i in items if i["ownerId"] == user["id"]]
    elif "ownerId" in f:
        items = [i for i in items if i["ownerId"] == f["ownerId"]]

    for key in ("type", "category", "status", "date"):
        if key in f:
            items = [i for i in items if i[key] == f[key]]
    if "location" in f:
        items = [i for i in items if f["location"] in i["location"].lower()]
    if "search" in f:
        items = [i for i in items if f["search"] in (i["title"] + " " + i["description"]).lower()]

    items = sorted(items, key=lambda i: i["createdAt"], reverse=True)
    total = len(items)
    start = (f["page"] - 1) * f["perPage"]
    page_items = items[start:start + f["perPage"]]
    return success(200, "Items retrieved successfully.", page_items,
                   {"total": total, "page": f["page"], "perPage": f["perPage"]})


@router.get("/{item_id}")
def get_item(item_id: str, user=Depends(current_user)):
    return success(200, "Item retrieved successfully.", _get_accessible(item_id, user))


@router.post("")
async def create_item(request: Request, user=Depends(current_user)):
    body = await _read_json(request)
    errors = validate_item_body(body)
    if errors:
        raise ApiError("VALIDATION_ERROR", details=errors)

    fields = _clean(body)
    duplicate = next((i for i in data.ITEMS
                      if i["ownerId"] == user["id"] and i["status"] == "active" and fields["status"] == "active"
                      and i["type"] == fields["type"] and i["title"].lower() == fields["title"].lower()), None)
    if duplicate:
        raise ApiError("CONFLICT", f"You already have an active {fields['type']} item titled '{duplicate['title']}' ({duplicate['id']}).")

    now = _now()
    item = {"id": data.next_id(), **fields, "ownerId": user["id"], "createdAt": now, "updatedAt": now}
    data.ITEMS.append(item)
    return success(201, "Item created successfully.", item)


@router.put("/{item_id}")
async def update_item(item_id: str, request: Request, user=Depends(current_user)):
    item = _get_accessible(item_id, user)
    body = await _read_json(request)
    errors = validate_item_body(body)
    if errors:
        raise ApiError("VALIDATION_ERROR", details=errors)

    fields = _clean(body, default_status=item["status"])
    if item["status"] == "resolved" and fields["status"] != "active":
        raise ApiError("CONFLICT", "This item is already resolved. Set status to 'active' to reopen it before editing.")

    item.update(fields)
    item["updatedAt"] = _now()
    return success(200, "Item updated successfully.", item)


@router.delete("/{item_id}")
def delete_item(item_id: str, user=Depends(current_user)):
    item = _get_accessible(item_id, user)
    data.ITEMS.remove(item)
    return success(200, "Item deleted successfully.", None)
