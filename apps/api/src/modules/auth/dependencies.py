import uuid
from typing import Annotated

import structlog
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.core.database import DBSession
from src.core.exceptions import InvalidTokenError, UnauthorizedError
from src.core.security import BEARER_CHALLENGE, decode_access_token
from src.modules.auth import repository as auth_repo
from src.modules.auth.models import User

security_scheme = HTTPBearer(auto_error=True)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security_scheme)],
    db: DBSession,
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenError(
                "Token is missing its subject", code="token_invalid", headers=BEARER_CHALLENGE
            )
        user_id = uuid.UUID(user_id_str)
    except ValueError as exc:
        # A token signed by us but carrying a non-uuid subject is invalid, not expired.
        raise InvalidTokenError(
            "Token is invalid", code="token_invalid", headers=BEARER_CHALLENGE
        ) from exc

    user = await auth_repo.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        # Raised as AppError like the rest of the module, with the RFC 6750 challenge.
        raise UnauthorizedError(
            "User not found or inactive", code="account_inactive", headers=BEARER_CHALLENGE
        )
    structlog.contextvars.bind_contextvars(user_id=str(user.id))
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
