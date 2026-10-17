from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
import structlog

from src.core.config import get_settings
from src.core.exceptions import InvalidTokenError

log = structlog.get_logger(__name__)

# RFC 6750: a 401 from a bearer-token protected endpoint says how to authenticate.
BEARER_CHALLENGE = {"WWW-Authenticate": "Bearer"}


def hash_password(plain: str) -> str:
    pwd_bytes = plain.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False


def create_access_token(data: dict[str, Any], expires_minutes: int | None = None) -> str:
    settings = get_settings()
    minutes = expires_minutes if expires_minutes is not None else settings.JWT_EXPIRES_MINUTES
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decode an access token, distinguishing "expired" from "forged".

    Clients need the difference: an expired token means "refresh", an invalid one
    means "sign in again". The underlying JWT error text is logged server-side and
    never returned — it can describe our key material and is useless to clients
    (#1159).
    """

    settings = get_settings()
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        log.info("auth.token.expired", reason=str(exc))
        raise InvalidTokenError(
            "Token has expired", code="token_expired", headers=BEARER_CHALLENGE
        ) from exc
    except jwt.PyJWTError as exc:
        log.warning("auth.token.invalid", reason=str(exc), reason_type=type(exc).__name__)
        raise InvalidTokenError(
            "Token is invalid", code="token_invalid", headers=BEARER_CHALLENGE
        ) from exc
