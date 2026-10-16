import jwt

from fastapi import Depends, FastAPI, HTTPException, Request, status
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from database import Base, engine, get_db
from models import User
from schemas import TokenResponse, UserLogin, UserRegister, UserResponse
from security_logger import log_security_event

Base.metadata.create_all(bind=engine)

limiter = Limiter(key_func=get_remote_address, default_limits=[])

app = FastAPI(
    title="Secure Zero-Trust File Sharing Platform",
    description="Secure file sharing and threat detection API",
    version="1.0.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

bearer_scheme = HTTPBearer()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)



@app.get("/")
def root():
    return {
        "message": "Zero-Trust File Sharing API is running",
        "status": "active",
    }


@app.get("/health")
def health_check():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection unavailable",
        )


@app.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    email = str(user_data.email).lower()

    existing_user = db.scalar(
        select(User).where(User.email == email)
    )

    if existing_user:
        log_security_event(
            "REGISTRATION_REJECTED",
            detail="Duplicate account registration attempted",
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists",
        )

    user = User(
        email=email,
        password_hash=hash_password(user_data.password),
    )

    db.add(user)

    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        log_security_event(
            "REGISTRATION_ERROR",
            detail="Database error while creating account",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to create account",
        )

    log_security_event(
        "REGISTRATION_SUCCESS",
        user_id=user.id,
        detail="Account registered",
    )

    return user


@app.post("/auth/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login_user(
    request: Request,
    user_data: UserLogin,
    db: Session = Depends(get_db),
):
    email = str(user_data.email).lower()

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if (
        user is None
        or not verify_password(user_data.password, user.password_hash)
        or not user.is_active
    ):
        log_security_event(
            "LOGIN_FAILED",
            detail="Invalid credentials or inactive account",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(str(user.id))

    log_security_event(
        "LOGIN_SUCCESS",
        user_id=user.id,
        detail="User authenticated",
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


@app.get("/auth/me", response_model=UserResponse)
def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = decode_access_token(credentials.credentials)
        subject = payload.get("sub")

        if not isinstance(subject, str):
            raise ValueError("Invalid token subject")

        user_id = int(subject)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        log_security_event(
            "AUTHENTICATION_FAILED",
            detail="Invalid or expired token at /auth/me",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, user_id)

    if user is None or not user.is_active:
        log_security_event(
            "AUTHENTICATION_FAILED",
            user_id=user_id,
            detail="User missing or inactive at /auth/me",
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    return user


from file_routes import router as file_router

app.include_router(file_router)


