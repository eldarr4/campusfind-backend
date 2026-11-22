"""CampusFind API prototype (Assignment 2): mocked data, token auth, role-based access."""
import logging

from fastapi import FastAPI, Request
from starlette.exceptions import HTTPException as StarletteHTTPException

from .errors import ERRORS, ApiError
from .responses import error
from .routers import greeting, items

logger = logging.getLogger("campusfind")

app = FastAPI(
    title="CampusFind API",
    description="Prototype REST API with mocked data. Use the mock tokens user-a-token, user-b-token or admin-token.",
    version="1.0.0",
)
app.include_router(greeting.router)
app.include_router(items.router)


@app.exception_handler(ApiError)
async def api_error_handler(request: Request, exc: ApiError):
    return error(exc.status, exc.code, exc.message, exc.details)


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    # Unknown paths and unsupported methods raised by the router itself.
    code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(exc.status_code, "INTERNAL_ERROR")
    status = exc.status_code if code != "INTERNAL_ERROR" else 500
    message = ERRORS[code][1]
    if code == "NOT_FOUND":
        message = f"No endpoint exists at {request.url.path}."
    headers = {"Allow": exc.headers["Allow"]} if exc.headers and "Allow" in exc.headers else None
    response = error(status, code, message)
    if headers:
        response.headers.update(headers)
    return response


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    # Details go to the server log only, never to the client.
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return error(500, "INTERNAL_ERROR", ERRORS["INTERNAL_ERROR"][1])
