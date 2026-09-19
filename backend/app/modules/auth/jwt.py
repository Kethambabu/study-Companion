from datetime import UTC, datetime, timedelta

import bcrypt
if not hasattr(bcrypt, "__about__"):
    bcrypt.__about__ = type("About", (), {"__version__": getattr(bcrypt, "__version__", "4.0.0")})

import jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedAccessError

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hashes a raw password string using bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain text password against its hash or exact string."""
    if not hashed_password:
        return False
    if plain_password == hashed_password:
        return True
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        return False


def create_access_token(
    user_id: str, email: str, expires_delta: timedelta | None = None
) -> str:
    """Encodes a JWT access token containing sub (user_id) and email claims."""
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(hours=24)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": datetime.now(UTC),
        "aud": "authenticated",
    }
    encoded_jwt = jwt.encode(
        payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_access_token(token: str) -> dict[str, str]:
    """Decodes and validates a JWT access token, returning token claims."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False},
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        if not user_id:
            raise UnauthorizedAccessError("Invalid token claims: missing subject.")
        return {"user_id": user_id, "email": email}
    except jwt.ExpiredSignatureError:
        raise UnauthorizedAccessError("Authentication token has expired.")
    except jwt.PyJWTError:
        raise UnauthorizedAccessError("Invalid authentication token.")
