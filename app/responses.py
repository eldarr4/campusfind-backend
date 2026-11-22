"""Envelope helpers. Every JSON response uses one of these two shapes."""
from fastapi.responses import JSONResponse


def success(status, message, data=None, meta=None):
    body = {"success": True, "message": message, "data": data}
    if meta is not None:
        body["meta"] = meta
    return JSONResponse(status_code=status, content=body)


def error(status, code, message, details=None):
    err = {"code": code, "message": message}
    if details:
        err["details"] = details
    return JSONResponse(status_code=status, content={"success": False, "error": err})
