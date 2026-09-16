"""팀 문서, FastAPI OpenAPI, 프론트 API 모듈의 계약 일치 검증."""

from pathlib import Path

from app.config import Settings
from app.main import create_app


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _json_schema(operation: dict, status: str) -> dict:
    return operation["responses"][status]["content"]["application/json"]["schema"]


def test_paths_methods_statuses_and_security_match_contract(test_settings: Settings) -> None:
    """다섯 endpoint의 method·status·Bearer 경계를 고정합니다."""

    openapi = create_app(test_settings).openapi()
    expected = {
        ("/api/auth/register", "post"): {"201", "400", "422", "500"},
        ("/api/auth/login", "post"): {"200", "401", "422", "500"},
        ("/api/chat", "post"): {"200", "400", "401", "422", "500", "504"},
        ("/api/me/chats", "get"): {"200", "401", "500"},
        ("/api/health", "get"): {"200"},
    }

    assert set(openapi["paths"]) == {path for path, _method in expected}
    for (path, method), statuses in expected.items():
        operation = openapi["paths"][path][method]
        assert set(operation["responses"]) == statuses
        if path in {"/api/chat", "/api/me/chats"}:
            assert operation["security"] == [{"HTTPBearer": []}]
        else:
            assert "security" not in operation

    assert openapi["components"]["securitySchemes"]["HTTPBearer"] == {
        "type": "http",
        "scheme": "bearer",
    }


def test_openapi_request_and_response_fields_match_frontend_contract(
    test_settings: Settings,
) -> None:
    """요청·응답 필드와 history 배열·공통 detail 스키마를 대조합니다."""

    openapi = create_app(test_settings).openapi()
    schemas = openapi["components"]["schemas"]

    assert set(schemas["UserRegisterRequest"]["properties"]) == {"username", "password"}
    assert set(schemas["UserRegisterRequest"]["required"]) == {"username", "password"}
    assert set(schemas["UserLoginRequest"]["properties"]) == {"username", "password"}
    assert set(schemas["UserLoginRequest"]["required"]) == {"username", "password"}
    assert set(schemas["UserRegisterResponse"]["properties"]) == {"message", "username"}
    assert set(schemas["TokenResponse"]["properties"]) == {"access_token", "token_type"}
    assert set(schemas["ChatResponse"]["properties"]) == {"answer", "latency_ms"}
    assert set(schemas["ChatResponse"]["required"]) == {"answer", "latency_ms"}
    assert set(schemas["ChatLogItem"]["properties"]) == {
        "id",
        "question",
        "response",
        "latency_ms",
        "created_at",
    }
    assert set(schemas["HealthResponse"]["properties"]) == {"status"}
    assert schemas["ErrorDetailResponse"]["properties"]["detail"]["type"] == "string"
    assert schemas["ErrorDetailResponse"]["required"] == ["detail"]

    chat_request = openapi["paths"]["/api/chat"]["post"]["requestBody"]["content"]
    chat_request = chat_request["application/json"]["schema"]
    assert set(chat_request["properties"]) == {"question"}
    assert chat_request["required"] == ["question"]

    history_schema = _json_schema(openapi["paths"]["/api/me/chats"]["get"], "200")
    assert history_schema["type"] == "array"
    assert history_schema["items"]["$ref"].endswith("/ChatLogItem")

    error_ref = "#/components/schemas/ErrorDetailResponse"
    for path, method, statuses in (
        ("/api/auth/register", "post", {"400", "422", "500"}),
        ("/api/auth/login", "post", {"401", "422", "500"}),
        ("/api/chat", "post", {"400", "401", "422", "500", "504"}),
        ("/api/me/chats", "get", {"401", "500"}),
    ):
        operation = openapi["paths"][path][method]
        for status in statuses:
            assert _json_schema(operation, status)["$ref"] == error_ref


def test_team_spec_and_frontend_module_name_the_same_contract() -> None:
    """문서와 api.js가 구형 key나 별도 서버 주소로 이탈하지 않게 합니다."""

    spec = (PROJECT_ROOT / "docs" / "api_spec.md").read_text(encoding="utf-8")
    api_source = (PROJECT_ROOT / "static" / "js" / "api.js").read_text(encoding="utf-8")

    for path in (
        "/api/auth/register",
        "/api/auth/login",
        "/api/chat",
        "/api/me/chats",
        "/api/health",
    ):
        assert path in spec

    for field in (
        "username",
        "password",
        "access_token",
        "token_type",
        "question",
        "answer",
        "latency_ms",
        "response",
        "created_at",
        "detail",
    ):
        assert f"`{field}`" in spec or f'"{field}"' in spec

    assert 'const API_BASE = "/api"' in api_source
    for relative_path in ("/auth/register", "/auth/login", "/chat", "/me/chats", "/health"):
        assert f'request("{relative_path}"' in api_source
    assert "reply" not in api_source
    assert "chat_id" not in api_source
