"""SQLite 조회 결과를 전달하는 최소 행 모델."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UserRow:
    """인증에 필요한 사용자 행을 나타냅니다."""

    id: int
    username: str
    hashed_password: str
    created_at: str


@dataclass(frozen=True, slots=True)
class ChatLogRow:
    """저장된 대화 한 건을 나타냅니다."""

    id: int
    user_id: int
    question: str
    response: str
    latency_ms: int
    created_at: str
