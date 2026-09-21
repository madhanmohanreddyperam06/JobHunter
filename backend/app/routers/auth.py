from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
import jwt

from app.database.database import get_db
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, LoginRequest, Token
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# HTTP Bearer token security scheme for FastAPI Swagger UI integration
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Reusable dependency extracting and validating the JWT bearer token.
    Loads and returns the authenticated User entity from MySQL.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if not auth or not auth.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing",
            headers={"WWW-Authenticate": "Bearer"}
        )

    token = auth.credentials

    try:
        payload = decode_access_token(token)
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"}
        )
    except jwt.PyJWTError:
        raise credentials_exception

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )

    return user


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="User Registration"
)
def register(user_in: UserCreate, db: Session = Depends(get_db)) -> UserResponse:
    """
    Registers a new candidate user with securely hashed password.
    Rejects duplicate email addresses with HTTP 409 Conflict.
    """
    normalized_email = user_in.email.strip().lower()

    # Check database uniqueness constraint
    existing_user = db.query(User).filter(User.email == normalized_email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists."
        )

    # Securely hash password with bcrypt
    hashed = hash_password(user_in.password)

    new_user = User(
        name=user_in.name.strip(),
        email=normalized_email,
        password_hash=hashed
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=Token,
    summary="User Login"
)
def login(credentials: LoginRequest, db: Session = Depends(get_db)) -> Token:
    """
    Authenticates user credentials and issues a signed JWT access token.
    Returns HTTP 401 on incorrect email or password.
    """
    normalized_email = credentials.email.strip().lower()

    user = db.query(User).filter(User.email == normalized_email).first()
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Generate JWT token with user id in subject claim
    access_token = create_access_token(data={"sub": str(user.id)})

    return Token(
        access_token=access_token,
        token_type="bearer"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Current Authenticated User"
)
def get_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """
    Retrieves the identity profile of the currently authenticated user.
    """
    return current_user


@router.get(
    "/protected-test",
    summary="Protected Test Endpoint"
)
def protected_test(current_user: User = Depends(get_current_user)) -> dict:
    """
    Diagnostic endpoint to verify protected route authentication.
    """
    return {
        "message": "Authentication successful",
        "user_id": current_user.id
    }
