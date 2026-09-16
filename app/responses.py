"""JSON 응답의 UTF-8 Content-Type을 계약대로 고정합니다."""

from fastapi.responses import JSONResponse


class UTF8JSONResponse(JSONResponse):
    """모든 JSON 응답에 charset=utf-8을 명시합니다."""

    media_type = "application/json"

    def init_headers(self, headers: dict[str, str] | None = None) -> None:
        """OpenAPI media type은 유지하고 실제 HTTP 헤더에 charset을 붙입니다."""

        super().init_headers(headers)
        self.raw_headers = [
            (key, b"application/json; charset=utf-8") if key == b"content-type" else (key, value)
            for key, value in self.raw_headers
        ]
