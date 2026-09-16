"""환경 변수에서 애플리케이션 설정을 안전하게 읽습니다."""

from functools import lru_cache
from typing import Literal

from pydantic import AnyHttpUrl, Field, TypeAdapter, ValidationError, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


PLACEHOLDER_SECRET_KEYS = {
    "your_super_secret_jwt_key_here",
    "change-me",
    "changeme",
}
PLACEHOLDER_API_KEYS = {
    "your_codessey_api_key",
    "change-me",
    "changeme",
}
AI_BASE_URL_ADAPTER = TypeAdapter(AnyHttpUrl)


class Settings(BaseSettings):
    """서버 기동에 필요한 설정과 모드 제약을 검증합니다."""

    secret_key: str = Field(validation_alias="SECRET_KEY")
    algorithm: str = Field(default="HS256", validation_alias="ALGORITHM")
    access_token_expire_minutes: int = Field(
        default=1440,
        gt=0,
        validation_alias="ACCESS_TOKEN_EXPIRE_MINUTES",
    )
    database_url: str = Field(
        default="sqlite:///./data/chatbot.db",
        validation_alias="DATABASE_URL",
    )
    codessey_api_key: str = Field(default="", validation_alias="CODESSEY_API_KEY")
    codessey_api_base: str = Field(
        default="https://api.openai.com/v1",
        validation_alias="CODESSEY_API_BASE",
    )
    ai_model_name: str = Field(default="gpt-4o-mini", validation_alias="AI_MODEL_NAME")
    ai_timeout_seconds: float = Field(
        default=8.0,
        gt=0,
        validation_alias="AI_TIMEOUT_SECONDS",
    )
    app_env: Literal["development", "test", "production"] = Field(
        default="development",
        validation_alias="APP_ENV",
    )
    ai_mode: Literal["auto", "mock", "real"] = Field(
        default="auto",
        validation_alias="AI_MODE",
    )
    context_turns: int = Field(
        default=5,
        ge=3,
        le=5,
        validation_alias="CONTEXT_TURNS",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
        hide_input_in_errors=True,
    )

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        """누락되거나 예시인 JWT 서명키를 거부합니다."""

        normalized = value.strip()
        if not normalized or normalized.lower() in PLACEHOLDER_SECRET_KEYS:
            raise ValueError("SECRET_KEY에 예시가 아닌 실제 비밀값을 설정해 주세요.")
        if len(normalized) < 32:
            raise ValueError("SECRET_KEY는 최소 32자 이상이어야 합니다.")
        return normalized

    @field_validator("algorithm")
    @classmethod
    def validate_algorithm(cls, value: str) -> str:
        """첨부 계약의 JWT 알고리즘만 허용합니다."""

        if value != "HS256":
            raise ValueError("ALGORITHM은 HS256이어야 합니다.")
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        """이 구현이 지원하는 SQLite URL인지 확인합니다."""

        if not value.startswith("sqlite:///") or not value.removeprefix("sqlite:///"):
            raise ValueError("DATABASE_URL은 sqlite:/// 경로여야 합니다.")
        return value

    @field_validator("codessey_api_base")
    @classmethod
    def validate_ai_base_url(cls, value: str) -> str:
        """키와 대화가 나갈 공급자 주소를 안전한 절대 HTTPS URL로 제한합니다."""

        normalized = value.strip()
        try:
            parsed = AI_BASE_URL_ADAPTER.validate_python(normalized)
        except ValidationError as exc:
            raise ValueError("CODESSEY_API_BASE는 유효한 HTTPS URL이어야 합니다.") from exc
        if (
            parsed.scheme != "https"
            or not parsed.host
            or parsed.username is not None
            or parsed.password is not None
            or parsed.query is not None
            or parsed.fragment is not None
        ):
            raise ValueError(
                "CODESSEY_API_BASE는 사용자정보·query·fragment가 없는 HTTPS URL이어야 합니다."
            )
        return normalized

    @field_validator("ai_model_name")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        """외부 호출 모델 이름의 빈 문자열을 거부합니다."""

        normalized = value.strip()
        if not normalized:
            raise ValueError("AI 모델 이름은 비어 있을 수 없습니다.")
        return normalized

    @model_validator(mode="after")
    def validate_ai_mode(self) -> "Settings":
        """실모드와 운영모드가 Mock으로 조용히 전환되지 않게 합니다."""

        has_key = self.has_real_api_key
        if self.ai_mode == "real" and not has_key:
            raise ValueError("AI_MODE=real에는 실제 CODESSEY_API_KEY가 필요합니다.")
        if self.app_env == "production" and (self.ai_mode == "mock" or not has_key):
            raise ValueError("운영 환경은 Mock 또는 미설정 API 키로 기동할 수 없습니다.")
        return self

    @property
    def has_real_api_key(self) -> bool:
        """API 키 값이 비어 있거나 알려진 예시인지 구분합니다."""

        normalized = self.codessey_api_key.strip()
        return bool(normalized) and normalized.lower() not in PLACEHOLDER_API_KEYS

    @property
    def resolved_ai_mode(self) -> Literal["mock", "real"]:
        """현재 설정에서 실제로 선택되는 AI 모드를 반환합니다."""

        if self.ai_mode == "mock":
            return "mock"
        if self.ai_mode == "real" or self.has_real_api_key:
            return "real"
        return "mock"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """프로세스 환경과 `.env`를 한 번 읽어 설정을 반환합니다."""

    return Settings()
