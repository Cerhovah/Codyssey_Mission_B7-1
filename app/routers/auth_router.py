"""회원가입과 로그인 API 라우터."""

import aiosqlite
from fastapi import APIRouter, HTTPException, Request, status

from app.auth import hash_password
from app.config import Settings
from app.database import DuplicateUsernameError, create_user
from app.schemas import ErrorDetailResponse, UserRegisterRequest, UserRegisterResponse


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
