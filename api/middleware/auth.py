"""
JWT authentication middleware and FastAPI dependency.
Every protected route receives a validated user_id via Depends(get_current_user).
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from cache.client import CacheClient, get_redis
from cache.keys import revoked_token_key
from core.exceptions import AuthenticationError, TokenExpiredError
from core.security import extract_user_id

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    redis: CacheClient = Depends(get_redis),
) -> str:
    """
    FastAPI dependency.
    Returns the user_id string extracted from the JWT.
    Raises HTTP 401 on any auth failure.
    """
    # Check revocation list
    cache = CacheClient(redis)
    revoked = await cache.get(revoked_token_key(token))
    if revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = extract_user_id(token)
        return user_id
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        )
