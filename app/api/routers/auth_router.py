from typing import Annotated

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.schemas import UserResponse, UserRegisterRequest, Token
from app.core.database import get_db
from app.core.models import UserModel
from app.api.dependencies import CurrentUser
from app.core.auth import create_access_token, hash_password, verify_password
from app.utils.exceptions import AuthenticationException, ValidationException


router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post(
    "/register", status_code=status.HTTP_201_CREATED, response_model=UserResponse
)
async def create_user(
    user: UserRegisterRequest, db: Annotated[AsyncSession, Depends(get_db)]
):
    stmt = select(UserModel).where(func.lower(UserModel.email) == user.email.lower())
    result = await db.execute(stmt)
    if result.scalars().first():
        raise ValidationException(
            user_message="Email already exists",
            internal_detail=f"Registration attempt failed: email {user.email} already in use.",
        )
    hashed_password = hash_password(user.password)
    new_user = UserModel(
        username=user.username,
        email=user.email.lower(),
        hashed_password=hashed_password,
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


@router.post("/login", response_model=Token)
async def login(
    user: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    stmt = select(UserModel).where(func.lower(UserModel.email) == user.username.lower())
    result = await db.execute(stmt)
    existing_user = result.scalars().first()

    if not existing_user or not verify_password(
        user.password, existing_user.hashed_password
    ):
        raise AuthenticationException(
            internal_detail=f"Login failed for email: {user.username}"
        )

    access_token = create_access_token(
        data={"sub": str(existing_user.id), "username": existing_user.username}
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserResponse)
async def get_current_user(current_user: CurrentUser):
    return current_user
