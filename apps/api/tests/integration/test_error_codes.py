"""Stable machine-readable error codes (#1164).

Clients branch on ``code``; ``message`` is human-facing text that may be
reworded or localised at any time.
"""

import inspect

from src.core.exceptions import (
    AppError,
    ConflictError,
    ForbiddenError,
    InvalidTokenError,
    InvalidTransitionError,
    NotFoundError,
    TooManyRequestsError,
    UnauthorizedError,
    UserNotFoundError,
    ValidationError,
)


async def test_not_found_returns_not_found_code(client):
    import uuid

    response = await client.get(f"/api/reports/{uuid.uuid4()}")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert body["message"] == "Report not found"


async def test_duplicate_registration_returns_email_taken(client):
    import uuid

    payload = {"email": f"codes_{uuid.uuid4().hex[:6]}@example.com", "password": "password123"}
    assert (await client.post("/api/auth/register", json=payload)).status_code == 201

    second = await client.post("/api/auth/register", json=payload)
    assert second.status_code == 409
    body = second.json()
    assert body["code"] == "email_taken"
    assert body["field"] == "email"


async def test_wrong_password_returns_invalid_credentials(client):
    import uuid

    email = f"codes_{uuid.uuid4().hex[:6]}@example.com"
    await client.post("/api/auth/register", json={"email": email, "password": "password123"})

    response = await client.post("/api/auth/login", json={"email": email, "password": "wrong-password"})
    assert response.status_code == 401
    assert response.json()["code"] == "invalid_credentials"


async def test_validation_error_carries_code_and_field_errors(client):
    response = await client.post("/api/auth/register", json={"email": "not-an-email"})
    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "validation_error"
    assert body["errors"]


async def test_unhandled_exception_returns_internal_error_code(client):
    # The default client fixture raises app exceptions; this assertion only
    # covers the shape of the handler's body, exercised through a real 500.
    from httpx import ASGITransport, AsyncClient
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/boom")
    async def boom():
        raise RuntimeError("kaboom")

    from src.core.error_handler import unhandled_exception_handler

    app.add_exception_handler(Exception, unhandled_exception_handler)
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as test_client:
        response = await test_client.get("/boom")
    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"


def test_every_app_error_subclass_defines_a_code():
    """Acceptance criterion: no AppError subclass may inherit the 500 default."""

    for _, member in inspect.getmembers(
        __import__("src.core.exceptions", fromlist=["*"]),
        inspect.isclass,
    ):
        if not issubclass(member, AppError) or member is AppError:
            continue
        assert "code" in member.__dict__, f"{member.__name__} must declare a code"
        assert member.__dict__["code"], f"{member.__name__} declares an empty code"


def test_codes_are_unique():
    codes = [
        cls.__dict__["code"]
        for _, cls in inspect.getmembers(
            __import__("src.core.exceptions", fromlist=["*"]), inspect.isclass
        )
        if issubclass(cls, AppError) and cls is not AppError and "code" in cls.__dict__
    ]
    assert len(codes) == len(set(codes)), f"duplicate error codes: {codes}"


def test_known_classes_have_expected_codes():
    assert NotFoundError.code == "not_found"
    assert ConflictError.code == "conflict"
    assert UnauthorizedError.code == "unauthorized"
    assert ForbiddenError.code == "forbidden"
    assert TooManyRequestsError.code == "rate_limited"
    assert InvalidTokenError.code == "token_invalid"
    assert UserNotFoundError.code == "user_not_found"
    assert ValidationError.code == "validation_error"
    assert InvalidTransitionError.code == "invalid_transition"


def test_code_can_be_overridden_at_the_raise_site():
    error = ConflictError("taken", field="email", code="email_taken")
    assert error.code == "email_taken"
    assert error.field == "email"
    assert error.status_code == 409
