"""Client-supplied X-Request-ID is bounded, and log context does not leak (#1166)."""

import structlog
from httpx import AsyncClient


async def test_well_formed_request_id_is_echoed(client: AsyncClient):
    response = await client.get("/api/health", headers={"X-Request-ID": "abc-123-XY"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == "abc-123-XY"


async def test_oversized_request_id_is_replaced(client: AsyncClient):
    oversized = "a" * 500
    response = await client.get("/api/health", headers={"X-Request-ID": oversized})
    assert response.status_code == 200
    returned = response.headers["x-request-id"]
    assert returned != oversized
    assert len(returned) <= 64


async def test_malformed_request_id_is_replaced(client: AsyncClient):
    # Newlines and quotes are the log-injection payload: they must never reach
    # the logs or come back in a header.
    for hostile in ('id\n{"event": "admin_login"}', "id with spaces", 'quote"d', "semi;colon"):
        response = await client.get("/api/health", headers={"X-Request-ID": hostile})
        assert response.status_code == 200
        returned = response.headers["x-request-id"]
        assert returned != hostile
        assert "\n" not in returned and '"' not in returned and " " not in returned


async def test_request_context_is_cleared_between_requests(client: AsyncClient):
    # Bind something that looks like it came from a previous request, then make
    # two requests and confirm the bound value is gone for both.
    structlog.contextvars.bind_contextvars(user_id="user-from-previous-request")

    first = await client.get("/api/health", headers={"X-Request-ID": "first-request"})
    assert first.headers["x-request-id"] == "first-request"
    assert "user_id" not in structlog.contextvars.get_contextvars()

    second = await client.get("/api/health", headers={"X-Request-ID": "second-request"})
    assert second.headers["x-request-id"] == "second-request"
    context = structlog.contextvars.get_contextvars()
    assert "user_id" not in context
    assert context.get("request_id") == "second-request"
