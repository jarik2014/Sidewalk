import re
import time
import uuid

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from src.core.config import Settings

logger = structlog.get_logger(__name__)


def setup_cors(app: FastAPI, settings: Settings) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, environment: str = "development"):
        super().__init__(app)
        self.environment = environment

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'"
        if self.environment == "production":
            response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
        return response


# A client may suggest a request id, but only within this shape: bounded length
# and no characters that could forge log lines (#1166).
_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9-]{1,64}$")


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Contextvars are per-task in theory but the middleware runs in the same
        # task across a request pipeline, so a value bound by an earlier request
        # (user_id, clinic_id, ...) can still be visible here. Start clean.
        structlog.contextvars.clear_contextvars()

        incoming = request.headers.get("X-Request-ID")
        request_id = incoming if incoming and _REQUEST_ID_RE.fullmatch(incoming) else str(uuid.uuid4())

        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        start_time = time.perf_counter()
        response = await call_next(request)
        duration_ms = round((time.perf_counter() - start_time) * 1000)
        logger.info(
            "http_request",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
        )
        return response
