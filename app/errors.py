"""Fixed error codes and the exception used to raise them."""

# code -> (HTTP status, default message). Documented in docs/API.md.
ERRORS = {
    "VALIDATION_ERROR": (400, "The request contains invalid or missing fields."),
    "INVALID_JSON": (400, "The request body is not valid JSON."),
    "UNAUTHORIZED": (401, "Authentication token is missing or invalid."),
    "FORBIDDEN": (403, "You do not have permission to perform this action."),
    "NOT_FOUND": (404, "The requested resource was not found."),
    "METHOD_NOT_ALLOWED": (405, "This HTTP method is not supported for this endpoint."),
    "CONFLICT": (409, "The request conflicts with existing data."),
    "PAYLOAD_TOO_LARGE": (413, "The request body is too large."),
    "INTERNAL_ERROR": (500, "An unexpected error occurred. Please try again later."),
}


class ApiError(Exception):
    def __init__(self, code, message=None, details=None):
        super().__init__(code)
        self.code = code
        self.status = ERRORS[code][0]
        self.message = message or ERRORS[code][1]
        self.details = details
