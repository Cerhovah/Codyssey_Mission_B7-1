"""로그인 JWT 발급과 보호 API 인증 경계 검증."""

import asyncio
from collections.abc import Iterator
from datetime import datetime, timedelta, timezone

import aiosqlite
import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jose import jwt
from pydantic import BaseModel

from app.auth import create_access_token, get_current_user
from app.config import Settings
from app.database import database_connection
from app.main import create_app
from app.models import UserRow


class ProtectedPayload(BaseModel):
    """인증과 body 검증 순서를 확인하는 테스트 전용 입력."""

    value: str


def add_protected_probe(application: FastAPI) -> None:
    """운영 계약을 바꾸지 않는 테스트 전용 보호 경로를 추가합니다."""

    @application.post("/api/test/protected")
    async def protected_probe(
        payload: ProtectedPayload,
        current_user: UserRow = Depends(get_current_user),
    ) -> dict[str, object]:
        return {"user_id": current_user.id, "value": payload.value}


@pytest.fixture
def auth_client(test_settings: Settings) -> Iterator[TestClient]:
    """보호 probe가 있는 임시 앱과 등록 사용자를 제공합니다."""

    application = create_app(test_settings)
    add_protected_probe(application)
    with TestClient(application, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/auth/register",
            json={"username": "loginuser", "password": "pass1234"},
        )
        assert response.status_code == 201
        yield client


def login(auth_client: TestClient) -> str:
    """테스트 사용자의 유효한 JWT를 반환합니다."""

    response = auth_client.post(
        "/api/auth/login",
        json={"username": "loginuser", "password": "pass1234"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def test_login_returns_token_with_required_claims(
    auth_client: TestClient,
    test_settings: Settings,
) -> None:
    """로그인 응답과 sub/iat/exp/1440분 수명을 확인합니다."""

    response = auth_client.post(
        "/api/auth/login",
        json={"username": " loginuser ", "password": "pass1234"},
    )
    body = response.json()
    claims = jwt.decode(body["access_token"], test_settings.secret_key, algorithms=["HS256"])

    assert response.status_code == 200
    assert set(body) == {"access_token", "token_type"}
    assert body["token_type"] == "bearer"
    assert claims["sub"] == "loginuser"
    assert claims["exp"] - claims["iat"] == 1440 * 60


@pytest.mark.parametrize(
    ("username", "password"),
    [("missing", "pass1234"), ("loginuser", "wrong-password"), ("LoginUser", "pass1234")],
)
def test_login_credential_failures_share_same_401(
    auth_client: TestClient,
    username: str,
    password: str,
) -> None:
    """계정 존재와 비밀번호 불일치를 동일한 응답으로 처리합니다."""

    response = auth_client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "아이디 또는 비밀번호가 올바르지 않습니다."}


@pytest.mark.parametrize(
    "payload",
    [
        {"username": "", "password": "pass1234"},
        {"username": "loginuser", "password": "    "},
        {"username": None, "password": "pass1234"},
    ],
)
def test_login_validation_returns_string_detail(
    auth_client: TestClient,
    payload: dict[str, object],
) -> None:
    """공백과 자료형 오류를 배열형 상세 없이 422로 반환합니다."""

    response = auth_client.post("/api/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "아이디와 비밀번호를 확인해 주세요."}


def test_login_rejects_form_body(auth_client: TestClient) -> None:
    """OAuth form이 아닌 팀 계약의 JSON 로그인만 허용합니다."""

    response = auth_client.post(
        "/api/auth/login",
        data={"username": "loginuser", "password": "pass1234"},
    )

    assert response.status_code == 422
    assert isinstance(response.json()["detail"], str)


def test_login_over_100_char_password_skips_hash_work(
    auth_client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """가입 불가능한 긴 입력을 자르거나 bcrypt에 전달하지 않습니다."""

    async def forbidden_verify(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("긴 입력은 해시 검증을 호출하면 안 됩니다.")

    monkeypatch.setattr("app.routers.auth_router.verify_password", forbidden_verify)
    response = auth_client.post(
        "/api/auth/login",
        json={"username": "loginuser", "password": "x" * 101},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "아이디 또는 비밀번호가 올바르지 않습니다."}


def test_valid_bearer_token_allows_protected_request(auth_client: TestClient) -> None:
    """유효 토큰과 실제 DB 사용자가 있을 때만 보호 API를 통과합니다."""

    token = login(auth_client)
    response = auth_client.post(
        "/api/test/protected",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": "ok"},
    )

    assert response.status_code == 200
    assert response.json()["value"] == "ok"


@pytest.mark.parametrize("authorization", [None, "Basic abc", "Bearer", "Bearer invalid.token"])
def test_missing_or_malformed_token_returns_exact_401(
    auth_client: TestClient,
    authorization: str | None,
) -> None:
    """누락·형식 오류가 기본 403이 아닌 동일한 401을 반환합니다."""

    headers = {"Authorization": authorization} if authorization else {}
    response = auth_client.post(
        "/api/test/protected",
        headers=headers,
        json={"value": "blocked"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "인증 토큰이 유효하지 않거나 만료되었습니다."}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_unauthenticated_request_precedes_invalid_body(auth_client: TestClient) -> None:
    """보호 API는 잘못된 body보다 인증 실패를 먼저 반환합니다."""

    response = auth_client.post("/api/test/protected", json={})

    assert response.status_code == 401


def _signed_token(settings: Settings, claims: dict[str, object], algorithm: str = "HS256") -> str:
    """특정 JWT 실패 조건을 만드는 테스트 보조 함수."""

    return jwt.encode(claims, settings.secret_key, algorithm=algorithm)


@pytest.mark.parametrize("missing_claim", ["sub", "iat", "exp"])
def test_missing_required_claim_returns_401(
    auth_client: TestClient,
    test_settings: Settings,
    missing_claim: str,
) -> None:
    """sub/iat/exp 중 하나라도 없으면 인증을 거부합니다."""

    now = int(datetime.now(timezone.utc).timestamp())
    claims: dict[str, object] = {"sub": "loginuser", "iat": now, "exp": now + 3600}
    claims.pop(missing_claim)
    token = _signed_token(test_settings, claims)
    response = auth_client.post(
        "/api/test/protected",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": "blocked"},
    )

    assert response.status_code == 401


def test_tampered_wrong_algorithm_expired_and_future_tokens_return_401(
    auth_client: TestClient,
    test_settings: Settings,
) -> None:
    """서명·알고리즘·만료·미래 발급시각을 모두 거부합니다."""

    valid = login(auth_client)
    header, payload, signature = valid.split(".")
    changed = ("A" if signature[0] != "A" else "B") + signature[1:]
    tampered = ".".join((header, payload, changed))
    now = int(datetime.now(timezone.utc).timestamp())
    invalid_tokens = [
        tampered,
        _signed_token(
            test_settings,
            {"sub": "loginuser", "iat": now, "exp": now + 3600},
            algorithm="HS384",
        ),
        _signed_token(
            test_settings,
            {"sub": "loginuser", "iat": now - 7200, "exp": now - 3600},
        ),
        _signed_token(
            test_settings,
            {"sub": "loginuser", "iat": now + 3600, "exp": now + 7200},
        ),
        _signed_token(
            test_settings,
            {"sub": "loginuser", "iat": now - 3600, "exp": now},
        ),
        _signed_token(
            test_settings,
            {"sub": "", "iat": now, "exp": now + 3600},
        ),
        _signed_token(
            test_settings,
            {"sub": "loginuser", "iat": None, "exp": now + 3600},
        ),
        _signed_token(
            test_settings,
            {"sub": "loginuser", "iat": now, "exp": "not-a-number"},
        ),
    ]

    for token in invalid_tokens:
        response = auth_client.post(
            "/api/test/protected",
            headers={"Authorization": f"Bearer {token}"},
            json={"value": "blocked"},
        )
        assert response.status_code == 401


def test_token_for_missing_or_deleted_user_returns_401(
    auth_client: TestClient,
    test_settings: Settings,
) -> None:
    """서명만 유효하고 실제 사용자가 없으면 인증하지 않습니다."""

    missing_token = create_access_token("unknown", test_settings)
    valid_token = login(auth_client)

    async def delete_user() -> None:
        async with database_connection(test_settings) as connection:
            await connection.execute("DELETE FROM users WHERE username = ?", ("loginuser",))
            await connection.commit()

    missing_response = auth_client.post(
        "/api/test/protected",
        headers={"Authorization": f"Bearer {missing_token}"},
        json={"value": "blocked"},
    )
    asyncio.run(delete_user())
    deleted_response = auth_client.post(
        "/api/test/protected",
        headers={"Authorization": f"Bearer {valid_token}"},
        json={"value": "blocked"},
    )

    assert missing_response.status_code == 401
    assert deleted_response.status_code == 401


def test_corrupt_hash_and_auth_database_failure_return_safe_500(
    auth_client: TestClient,
    test_settings: Settings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """서버 저장상태 장애를 잘못된 자격 증명으로 숨기지 않습니다."""

    async def corrupt_hash() -> None:
        async with database_connection(test_settings) as connection:
            await connection.execute(
                "UPDATE users SET hashed_password = ? WHERE username = ?",
                ("corrupt-hash", "loginuser"),
            )
            await connection.commit()

    asyncio.run(corrupt_hash())
    login_response = auth_client.post(
        "/api/auth/login",
        json={"username": "loginuser", "password": "pass1234"},
    )

    async def fail_user_lookup(*_args: object, **_kwargs: object) -> None:
        raise aiosqlite.OperationalError("sensitive database detail")

    monkeypatch.setattr("app.auth.get_user_by_username", fail_user_lookup)
    token = create_access_token("loginuser", test_settings)
    protected_response = auth_client.post(
        "/api/test/protected",
        headers={"Authorization": f"Bearer {token}"},
        json={"value": "blocked"},
    )

    assert login_response.status_code == 500
    assert protected_response.status_code == 500
    assert "sensitive" not in protected_response.text
