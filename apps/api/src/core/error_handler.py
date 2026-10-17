from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.core.exceptions import AppError, ConflictError


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    # ``code`` is the machine-readable half of the contract (#1164); ``message``
    # stays for humans and may change wording or language at any time.
    content: dict[str, object] = {"code": exc.code, "message": exc.message}
    if isinstance(exc, ConflictError) and exc.field:
        content["field"] = exc.field
    return JSONResponse(status_code=exc.status_code, content=content, headers=exc.headers)


# Fallback codes for errors raised by Starlette/FastAPI rather than by AppError.
_HTTP_ERROR_CODES = {
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    429: "rate_limited",
}


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _HTTP_ERROR_CODES.get(exc.status_code, "http_error")
    content: dict[str, object] = {"code": code, "message": str(exc.detail)}
    headers = getattr(exc, "headers", None)
    return JSONResponse(status_code=exc.status_code, content=content, headers=headers)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = [
        {"field": ".".join(str(loc) for loc in err["loc"] if loc != "body"), "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={"code": "validation_error", "message": "Validation error", "errors": errors},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    return JSONResponse(status_code=500, content={"code": "internal_error", "message": "Internal server error"})
