"""In-memory mock data. It resets whenever the server restarts.

Non-existent ID for 404 demos: item_999
Resolved item for 409 demos:   item_104
"""
import copy
import itertools

SEED = [
    # ---- User A ----
    {"id": "item_101", "type": "lost", "title": "Black Sony headphones", "description": "Over-ear WH-1000XM4, small scratch on the left side.",
     "category": "electronics", "location": "Library, 2nd floor", "date": "2026-11-18", "status": "active",
     "secretDetail": None, "ownerId": "user-a", "createdAt": "2026-11-18T09:15:00Z", "updatedAt": "2026-11-18T09:15:00Z"},
    {"id": "item_102", "type": "found", "title": "Student ID card", "description": "Found next to the coffee machine.",
     "category": "documents", "location": "Cafeteria", "date": "2026-11-19", "status": "active",
     "secretDetail": "Photo of a cat on the back of the card", "ownerId": "user-a",
     "createdAt": "2026-11-19T12:40:00Z", "updatedAt": "2026-11-19T12:40:00Z"},
    {"id": "item_103", "type": "lost", "title": "Blue water bottle", "description": "Metal bottle with a university sticker.",
     "category": "other", "location": "Sports hall", "date": "2026-11-20", "status": "active",
     "secretDetail": None, "ownerId": "user-a", "createdAt": "2026-11-20T16:05:00Z", "updatedAt": "2026-11-20T16:05:00Z"},
    {"id": "item_104", "type": "found", "title": "Set of keys", "description": "Three keys on a red ring.",
     "category": "keys", "location": "Main entrance", "date": "2026-11-10", "status": "resolved",
     "secretDetail": "Keychain has a tiny silver bell", "ownerId": "user-a",
     "createdAt": "2026-11-10T08:30:00Z", "updatedAt": "2026-11-12T10:00:00Z"},
    # ---- User B ----
    {"id": "item_201", "type": "lost", "title": "Silver laptop charger", "description": "65W USB-C charger with a white cable.",
     "category": "electronics", "location": "Building B, room 204", "date": "2026-11-17", "status": "active",
     "secretDetail": None, "ownerId": "user-b", "createdAt": "2026-11-17T14:20:00Z", "updatedAt": "2026-11-17T14:20:00Z"},
    {"id": "item_202", "type": "found", "title": "Gray umbrella", "description": "Compact umbrella left on a bench.",
     "category": "accessories", "location": "Campus garden", "date": "2026-11-21", "status": "active",
     "secretDetail": "Initials “M.K.” on the handle", "ownerId": "user-b",
     "createdAt": "2026-11-21T11:10:00Z", "updatedAt": "2026-11-21T11:10:00Z"},
    {"id": "item_203", "type": "lost", "title": "Chemistry notebook", "description": "Green spiral notebook with lab notes.",
     "category": "other", "location": "Lecture hall A", "date": "2026-11-16", "status": "active",
     "secretDetail": None, "ownerId": "user-b", "createdAt": "2026-11-16T10:45:00Z", "updatedAt": "2026-11-16T10:45:00Z"},
]

ITEMS = copy.deepcopy(SEED)
_counter = itertools.count(301)


def next_id():
    return f"item_{next(_counter)}"


def reset():
    """Restore the seed data (used by the tests)."""
    global _counter
    ITEMS.clear()
    ITEMS.extend(copy.deepcopy(SEED))
    _counter = itertools.count(301)
