"""회원가입 계약과 bcrypt_sha256 경계값 검증."""

import asyncio
from collections.abc import Iterator

import aiosqlite
import pytest
from fastapi.testclient import TestClient
from passlib.hash import bcrypt_sha256

from app.auth import PasswordHashError, hash_password, verify_password
from app.config import Settings
from app.database import get_user_by_username
from app.main import create_app


@pytest.fixture
def client(test_settings: Settings) -> Iterator[TestClient]:
    """임시 DB를 사용하는 API 클라이언트를 제공합니다."""

    with TestClient(create_app(test_settings), raise_server_exceptions=False) as test_client:
        yield test_client


def test_register_returns_exact_contract_and_stores_hash(
    client: TestClient,
    test_settings: Settings,
) -> None:
    """성공 응답과 평문 비저장 여부를 함께 확인합니다."""

    response = client.post(
        "/api/auth/register",
        json={"username": "codyssey123", "password": "password1234"},
    )
    user = asyncio.run(get_user_by_username(test_settings, "codyssey123"))

    assert response.status_code == 201
    assert response.json() == {
        "message": "회원가입이 완료되었습니다.",
        "username": "codyssey123",
    }
    assert user is not None
    assert user.hashed_password != "password1234"
    assert bcrypt_sha256.identify(user.hashed_password)


def test_duplicate_username_returns_400(client: TestClient) -> None:
    """중복 등록만 계약상의 400으로 반환합니다."""

    payload = {"username": "duplicate", "password": "pass1234"}
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 400
    assert response.json() == {"detail": "이미 존재하는 아이디입니다."}


@pytest.mark.parametrize(
    ("username", "status_code", "detail"),
    [
        ("   ", 400, "아이디는 공백일 수 없습니다."),
        (" a ", 422, "아이디는 최소 3자 이상이어야 합니다."),
        ("ab", 422, "아이디는 최소 3자 이상이어야 합니다."),
        ("x" * 51, 422, "아이디는 최대 50자까지 입력 가능합니다."),
    ],
)
def test_register_username_boundaries(
    client: TestClient,
    username: str,
    status_code: int,
    detail: str,
) -> None:
    """아이디 공백과 길이 오류의 상태코드를 구분합니다."""

    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pass1234"},
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


def test_register_trims_edges_but_keeps_internal_space_and_case(client: TestClient) -> None:
    """원문 계약 이상의 내부 공백·대소문자 정규화를 하지 않습니다."""

    first = client.post(
        "/api/auth/register",
        json={"username": "  Ab cd  ", "password": "pass1234"},
    )
    second = client.post(
        "/api/auth/register",
        json={"username": "ab cd", "password": "pass1234"},
    )

    assert first.status_code == 201
    assert first.json()["username"] == "Ab cd"
    assert second.status_code == 201
    assert second.json()["username"] == "ab cd"


@pytest.mark.parametrize(
    ("password", "status_code", "detail"),
    [
        ("abc", 422, "비밀번호는 최소 4자 이상이어야 합니다."),
        ("    ", 422, "비밀번호는 공백일 수 없습니다."),
        ("x" * 101, 422, "비밀번호는 최대 100자까지 입력 가능합니다."),
    ],
)
def test_register_password_rejects_invalid_boundaries(
    client: TestClient,
    password: str,
    status_code: int,
    detail: str,
) -> None:
    """비밀번호 길이와 공백-only 오류를 안전한 문자열로 반환합니다."""

    response = client.post(
        "/api/auth/register",
        json={"username": f"user{len(password)}", "password": password},
    )

    assert response.status_code == status_code
    assert response.json() == {"detail": detail}


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("minimum", "abcd"),
        ("ascii100", "a" * 100),
        ("korean100", "한" * 100),
    ],
)
def test_register_accepts_password_contract_boundaries(
    client: TestClient,
    username: str,
    password: str,
) -> None:
    """회원가입 API가 4자와 100자 다바이트 상한을 모두 허용합니다."""

    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": password},
    )

    assert response.status_code == 201


@pytest.mark.parametrize("password", ["abcd", "a" * 100, "한" * 100])
async def test_hash_supports_full_password_contract(password: str) -> None:
    """4~100자 ASCII와 다바이트 입력을 자르지 않고 검증합니다."""

    hashed = await hash_password(password, rounds=4)

    assert await verify_password(password, hashed)
    assert not await verify_password(password + "다름", hashed)


async def test_hash_distinguishes_bytes_after_bcrypt_72_byte_boundary() -> None:
    """72바이트 뒤만 다른 입력이 같은 비밀번호로 취급되지 않게 합니다."""

    left = "a" * 72 + "X" * 28
    right = "a" * 72 + "Y" * 28
    hashed = await hash_password(left, rounds=4)

    assert await verify_password(left, hashed)
    assert not await verify_password(right, hashed)


async def test_corrupt_password_hash_is_server_error_not_auth_failure() -> None:
    """손상된 저장 해시를 일반 비밀번호 불일치로 숨기지 않습니다."""

    with pytest.raises(PasswordHashError):
        await verify_password("password1234", "not-a-valid-password-hash")


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"email": "old@example.com", "password": "pass1234"},
        {"username": None, "password": "pass1234"},
        {"username": ["array"], "password": "pass1234"},
        {"username": "valid", "password": 1234},
    ],
)
def test_register_malformed_payload_returns_string_detail(
    client: TestClient,
    payload: dict[str, object],
) -> None:
    """구형 키와 잘못된 자료형이 Pydantic 배열을 노출하지 않게 합니다."""

    response = client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    assert response.json() == {"detail": "입력 형식을 확인해 주세요."}


def test_register_database_failure_returns_safe_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """일반 DB 장애를 중복 오류로 오인하지 않습니다."""

    async def fail_create_user(*_args: object, **_kwargs: object) -> None:
        raise aiosqlite.OperationalError("sensitive database detail")

    monkeypatch.setattr("app.routers.auth_router.create_user", fail_create_user)
    response = client.post(
        "/api/auth/register",
        json={"username": "dbfail", "password": "pass1234"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "detail": "회원가입을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요."
    }
    assert "sensitive" not in response.text


def test_non_unique_integrity_failure_returns_500(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """UNIQUE가 아닌 무결성 장애를 중복 아이디로 오인하지 않습니다."""

    async def fail_create_user(*_args: object, **_kwargs: object) -> None:
        raise aiosqlite.IntegrityError("NOT NULL constraint failed")

    monkeypatch.setattr("app.routers.auth_router.create_user", fail_create_user)
    response = client.post(
        "/api/auth/register",
        json={"username": "integrity", "password": "pass1234"},
    )

    assert response.status_code == 500
    assert response.json()["detail"].startswith("회원가입을 처리하지 못했습니다.")


def test_default_404_and_405_use_korean_detail(client: TestClient) -> None:
    """프레임워크 기본 영문 오류도 공통 한국어 구조로 변환합니다."""

    missing = client.get("/api/does-not-exist")
    wrong_method = client.get("/api/auth/register")

    assert missing.status_code == 404
    assert missing.json() == {"detail": "요청한 경로를 찾을 수 없습니다."}
    assert wrong_method.status_code == 405
    assert wrong_method.json() == {"detail": "허용되지 않은 요청 방식입니다."}
