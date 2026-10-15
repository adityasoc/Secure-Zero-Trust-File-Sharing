from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from config import settings


password_hasher = PasswordHash.recommended()
ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expires_at,
        "iat": datetime.now(timezone.utc),
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[ALGORITHM],
    )
