"""Run with: pytest -v"""
import pytest
from fastapi.testclient import TestClient

from app import data
from app.main import app

client = TestClient(app, raise_server_exceptions=False)


def h(token):
    return {"Authorization": f"Bearer {token}"}


A, B, ADMIN = h("user-a-token"), h("user-b-token"), h("admin-token")

VALID = {"type": "lost", "title": "Red scarf", "category": "clothing", "location": "Library", "date": "2026-11-01"}


@pytest.fixture(autouse=True)
def fresh_data():
    data.reset()


def assert_error(resp, status, code):
    assert resp.status_code == status
    body = resp.json()
    assert body["success"] is False
    assert body["error"]["code"] == code
    assert "Traceback" not in resp.text
    return body["error"]


# ---------- Greeting ----------
def test_greeting_is_html():
    r = client.get("/api/v1/greeting")
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/html; charset=utf-8"
    assert "<!DOCTYPE html>" in r.text and "CampusFind" in r.text and "/api/v1/items" in r.text


# ---------- Authentication ----------
def test_missing_token_401():
    assert_error(client.get("/api/v1/items"), 401, "UNAUTHORIZED")


def test_invalid_token_401():
    assert_error(client.get("/api/v1/items", headers=h("nope")), 401, "UNAUTHORIZED")


def test_wrong_scheme_401():
    assert_error(client.get("/api/v1/items", headers={"Authorization": "Basic user-a-token"}), 401, "UNAUTHORIZED")


# ---------- Read ----------
def test_user_sees_only_own_items():
    r = client.get("/api/v1/items", headers=A)
    body = r.json()
    assert r.status_code == 200 and body["success"] is True
    assert {i["ownerId"] for i in body["data"]} == {"user-a"}
    assert body["meta"] == {"total": 4, "page": 1, "perPage": 10}


def test_admin_sees_all_items():
    assert client.get("/api/v1/items", headers=ADMIN).json()["meta"]["total"] == 7


def test_filters_and_paging():
    body = client.get("/api/v1/items?type=found&perPage=1&page=2", headers=ADMIN).json()
    assert body["meta"] == {"total": 3, "page": 2, "perPage": 1} and len(body["data"]) == 1


def test_invalid_query_400():
    err = assert_error(client.get("/api/v1/items?perPage=500&type=stolen", headers=A), 400, "VALIDATION_ERROR")
    assert {d["field"] for d in err["details"]} == {"perPage", "type"}


def test_get_own_item():
    r = client.get("/api/v1/items/item_101", headers=A)
    assert r.status_code == 200 and r.json()["data"]["id"] == "item_101"


def test_get_other_users_item_404():
    assert_error(client.get("/api/v1/items/item_201", headers=A), 404, "NOT_FOUND")
    assert_error(client.get("/api/v1/items/item_101", headers=B), 404, "NOT_FOUND")


def test_admin_reads_any_item():
    assert client.get("/api/v1/items/item_201", headers=ADMIN).status_code == 200


def test_nonexistent_item_404():
    assert_error(client.get("/api/v1/items/item_999", headers=A), 404, "NOT_FOUND")


# ---------- Create ----------
def test_create_201():
    r = client.post("/api/v1/items", json=VALID, headers=A)
    item = r.json()["data"]
    assert r.status_code == 201 and item["ownerId"] == "user-a" and item["status"] == "active"
    assert client.get(f"/api/v1/items/{item['id']}", headers=A).status_code == 200


def test_create_validation_400():
    r = client.post("/api/v1/items", json={"title": "ab", "category": "pets", "date": "2999-01-01", "extra": 1}, headers=A)
    err = assert_error(r, 400, "VALIDATION_ERROR")
    assert {"type", "title", "category", "location", "date", "extra"} <= {d["field"] for d in err["details"]}


def test_create_rejects_read_only_and_wrong_types():
    r = client.post("/api/v1/items", json={**VALID, "ownerId": "user-b", "title": 123}, headers=A)
    err = assert_error(r, 400, "VALIDATION_ERROR")
    assert {"ownerId", "title"} <= {d["field"] for d in err["details"]}


def test_secret_detail_only_on_found():
    assert_error(client.post("/api/v1/items", json={**VALID, "secretDetail": "x"}, headers=A), 400, "VALIDATION_ERROR")
    ok = client.post("/api/v1/items", json={**VALID, "type": "found", "secretDetail": "Has a name tag"}, headers=A)
    assert ok.status_code == 201


def test_invalid_json_400():
    r = client.post("/api/v1/items", content="{bad json", headers={**A, "Content-Type": "application/json"})
    assert_error(r, 400, "INVALID_JSON")


def test_empty_body_400():
    assert_error(client.post("/api/v1/items", headers=A), 400, "VALIDATION_ERROR")


def test_duplicate_active_item_409():
    assert client.post("/api/v1/items", json=VALID, headers=A).status_code == 201
    assert_error(client.post("/api/v1/items", json=VALID, headers=A), 409, "CONFLICT")


# ---------- Update ----------
def test_update_own_item():
    r = client.put("/api/v1/items/item_101", json={**VALID, "title": "Black Sony headphones (found!)", "status": "resolved"}, headers=A)
    assert r.status_code == 200 and r.json()["data"]["status"] == "resolved"


def test_update_other_users_item_404_and_unchanged():
    assert_error(client.put("/api/v1/items/item_201", json=VALID, headers=A), 404, "NOT_FOUND")
    assert data.ITEMS[4]["title"] == "Silver laptop charger"


def test_admin_updates_any_item():
    assert client.put("/api/v1/items/item_201", json=VALID, headers=ADMIN).status_code == 200


def test_update_validation_400():
    assert_error(client.put("/api/v1/items/item_101", json={"title": "x"}, headers=A), 400, "VALIDATION_ERROR")


def test_update_resolved_item_409_unless_reopened():
    assert_error(client.put("/api/v1/items/item_104", json={**VALID, "type": "found"}, headers=A), 409, "CONFLICT")
    reopened = client.put("/api/v1/items/item_104", json={**VALID, "type": "found", "status": "active"}, headers=A)
    assert reopened.status_code == 200


# ---------- Delete ----------
def test_delete_own_item():
    r = client.delete("/api/v1/items/item_103", headers=A)
    assert r.status_code == 200 and r.json()["data"] is None
    assert_error(client.get("/api/v1/items/item_103", headers=A), 404, "NOT_FOUND")


def test_delete_other_users_item_404():
    assert_error(client.delete("/api/v1/items/item_201", headers=A), 404, "NOT_FOUND")
    assert client.get("/api/v1/items/item_201", headers=B).status_code == 200


def test_admin_deletes_any_item():
    assert client.delete("/api/v1/items/item_201", headers=ADMIN).status_code == 200


# ---------- Routing errors ----------
def test_method_not_allowed_405():
    assert_error(client.patch("/api/v1/items/item_101", headers=A), 405, "METHOD_NOT_ALLOWED")


def test_unknown_path_404():
    assert_error(client.get("/api/v1/nothing", headers=A), 404, "NOT_FOUND")
