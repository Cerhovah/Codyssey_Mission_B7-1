"""팀 문서, FastAPI OpenAPI, 프론트 API 모듈의 계약 일치 검증."""

from pathlib import Path

from app.config import Settings
from app.main import create_app


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _json_schema(operation: dict, status: str) -> dict:
    return operation["responses"][status]["content"]["application/json"]["schema"]


def _documented_endpoint_section(spec: str, number: int) -> str:
    marker = f"### 3.{number} "
    section = spec.split(marker, 1)[1]
    return section.split("\n---", 1)[0]


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


def test_team_spec_sections_define_each_endpoint_contract() -> None:
    """api_spec의 각 endpoint 섹션에서 method·status·필드를 함께 검증합니다."""

    spec = (PROJECT_ROOT / "docs" / "api_spec.md").read_text(encoding="utf-8")

    cases = (
        (1, "/api/auth/register", "POST", "201 Created", {"username", "password"}, {"message", "username"}, {400, 422}),
        (2, "/api/auth/login", "POST", "200 OK", {"username", "password"}, {"access_token", "token_type"}, {401}),
        (3, "/api/chat", "POST", "200 OK", {"question"}, {"answer", "latency_ms"}, {400, 401, 422, 504}),
        (4, "/api/me/chats", "GET", "200 OK", set(), {"id", "question", "response", "latency_ms", "created_at"}, {401}),
        (5, "/api/health", "GET", "200 OK", set(), {"status"}, set()),
    )

    for number, path, method, success, request_fields, response_fields, errors in cases:
        section = _documented_endpoint_section(spec, number)
        assert f"(`{path}`)" in section
        assert f"- **Method**: `{method}`" in section
        assert f"#### Success Response (`{success}`)" in section
        for field in request_fields:
            assert f"`{field}`" in section
        for field in response_fields:
            assert f"`{field}`" in section or f'"{field}"' in section
        for status in errors:
            assert f"**{status} " in section

    assert "배열(`Array<ChatLogItem>`)" in _documented_endpoint_section(spec, 4)
    assert "**필수** (`Authorization: Bearer <access_token>`)" in _documented_endpoint_section(spec, 3)
    assert "**필수** (`Authorization: Bearer <access_token>`)" in _documented_endpoint_section(spec, 4)


def test_frontend_module_uses_the_documented_relative_paths_and_keys() -> None:
    """api.js가 구형 key나 별도 서버 주소로 이탈하지 않게 합니다."""

    api_source = (PROJECT_ROOT / "static" / "js" / "api.js").read_text(encoding="utf-8")

    assert 'const API_BASE = "/api"' in api_source
    for relative_path in ("/auth/register", "/auth/login", "/chat", "/me/chats", "/health"):
        assert f'request("{relative_path}"' in api_source
    assert "reply" not in api_source
    assert "chat_id" not in api_source
