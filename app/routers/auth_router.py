"""회원가입과 로그인 API 라우터."""

import aiosqlite
from fastapi import APIRouter, HTTPException, Request, status

from app.auth import (
    DUMMY_PASSWORD_HASH,
    PasswordHashError,
    create_access_token,
    hash_password,
    verify_password,
)
from app.config import Settings
from app.database import DuplicateUsernameError, create_user, get_user_by_username
from app.schemas import (
    ErrorDetailResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserRegisterResponse,
)


router = APIRouter(prefix="/api/auth", tags=["인증"])


@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=UserRegisterResponse,
    responses={
        400: {"model": ErrorDetailResponse},
        422: {"model": ErrorDetailResponse},
        500: {"model": ErrorDetailResponse},
    },
)
async def register_user(
    payload: UserRegisterRequest,
    request: Request,
) -> UserRegisterResponse:
    """검증된 아이디와 단방향 해시로 새 사용자를 등록합니다."""

    settings: Settings = request.app.state.settings
    hashed_password = await hash_password(payload.password)
    try:
        user = await create_user(settings, payload.username, hashed_password)
    except DuplicateUsernameError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 존재하는 아이디입니다.",
        ) from exc
    except aiosqlite.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc

    return UserRegisterResponse(username=user.username)


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {"model": ErrorDetailResponse},
        422: {"model": ErrorDetailResponse},
        500: {"model": ErrorDetailResponse},
    },
)
async def login_user(
    payload: UserLoginRequest,
    request: Request,
) -> TokenResponse:
    """아이디와 비밀번호를 검증하고 24시간 JWT를 발급합니다."""

    settings: Settings = request.app.state.settings
    try:
        user = await get_user_by_username(settings, payload.username)
    except aiosqlite.Error as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="로그인을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
        ) from exc

    password_matches = False
    if len(payload.password) <= 100:
        candidate_hash = user.hashed_password if user is not None else DUMMY_PASSWORD_HASH
        try:
            password_matches = await verify_password(payload.password, candidate_hash)
        except PasswordHashError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="로그인을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요.",
            ) from exc

    if user is None or not password_matches:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="아이디 또는 비밀번호가 올바르지 않습니다.",
        )

    return TokenResponse(access_token=create_access_token(user.username, settings))
