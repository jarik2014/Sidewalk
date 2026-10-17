"""Expired and invalid tokens are distinguishable, and 401s carry a challenge (#1159)."""

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import AsyncClient

from src.core.config import get_settings


def _token(expires_in: timedelta, subject: str = "00000000-0000-0000-0000-000000000001") -> str:
    settings = get_settings()
    payload = {"sub": subject, "exp": datetime.now(UTC) + expires_in}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


@pytest.mark.anyio
async def test_expired_token_reports_token_expired(client: AsyncClient):
    response = await client.get(
        "/api/users/me", headers={"Authorization": f"Bearer {_token(timedelta(minutes=-5))}"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "token_expired"


@pytest.mark.anyio
async def test_forged_token_reports_token_invalid(client: AsyncClient):
    settings = get_settings()
    forged = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000001", "exp": datetime.now(UTC) + timedelta(hours=1)},
        "not-our-secret-key-at-all",
        algorithm=settings.JWT_ALGORITHM,
    )
    response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401
    assert response.json()["code"] == "token_invalid"


@pytest.mark.anyio
async def test_unauthorized_responses_carry_www_authenticate(client: AsyncClient):
    settings = get_settings()
    tokens = [
        _token(timedelta(minutes=-5)),
        jwt.encode(
            {"sub": "00000000-0000-0000-0000-000000000001", "exp": datetime.now(UTC) + timedelta(hours=1)},
            "wrong-secret",
            algorithm=settings.JWT_ALGORITHM,
        ),
    ]
    for token in tokens:
        response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 401
        assert response.headers.get("www-authenticate", "").lower().startswith("bearer")


@pytest.mark.anyio
async def test_token_error_body_does_not_leak_library_detail(client: AsyncClient):
    settings = get_settings()
    forged = jwt.encode({"sub": "x"}, "nope", algorithm=settings.JWT_ALGORITHM)
    response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {forged}"})
    text = response.text.lower()
    for leak in ("signature", "decodeerror", "invalidtoken", "traceback"):
        assert leak not in text
    assert response.json()["message"] == "Token is invalid"


def test_decode_access_token_maps_both_failure_modes():
    """Unit level: the exception type is what carries the distinction."""
    from src.core.exceptions import InvalidTokenError
    from src.core.security import decode_access_token

    with pytest.raises(InvalidTokenError) as expired:
        decode_access_token(_token(timedelta(minutes=-1)))
    assert expired.value.code == "token_expired"
    assert expired.value.headers == {"WWW-Authenticate": "Bearer"}

    with pytest.raises(InvalidTokenError) as invalid:
        decode_access_token("definitely-not-a-jwt")
    assert invalid.value.code == "token_invalid"
