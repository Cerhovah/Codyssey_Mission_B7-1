# B7-1 웹 기반 AI 챗봇 REST API 명세서

> 문서 버전: v1.0.0 / 기본 Base URL: `/api`

이 문서는 프론트엔드 `static/`과 백엔드 `app/` 사이의 고정 계약입니다. 원자료 S07의 필드와 상태코드를 유지하며, 첨부 간 충돌은 `PROJECT_PLAN.md` C01~C24에 따라 명시적으로 조정합니다.

## 공통 통신 규칙

- POST 요청: `Content-Type: application/json; charset=utf-8`
- 응답: JSON UTF-8
- 보호 API: `Authorization: Bearer <access_token>`
- 날짜: UTC의 `YYYY-MM-DDTHH:MM:SS`
- 모든 앱 오류 body: `{"detail":"한국어 안내 문자열"}`
- 선택 응답 헤더 `X-AI-Mode`가 없더라도 클라이언트 핵심 기능은 정상 동작해야 합니다.

## 엔드포인트 요약

| 메서드 | 경로 | 인증 | 성공 |
|---|---|---:|---:|
| POST | `/api/auth/register` | 없음 | 201 |
| POST | `/api/auth/login` | 없음 | 200 |
| POST | `/api/chat` | Bearer | 200 |
| GET | `/api/me/chats` | Bearer | 200 |
| GET | `/api/health` | 없음 | 200 |

## POST /api/auth/register

```json
{"username":"codyssey123","password":"password1234"}
```

- `username`: 문자열, 원문 3~50자. 앞뒤 공백을 제거한 뒤 최소 3자. 공백만이면 400.
- `password`: 문자열 4~100자. 공백만 금지하고 값 자체는 trim하지 않음.

성공 201:

```json
{"message":"회원가입이 완료되었습니다.","username":"codyssey123"}
```

- 중복 400: `{"detail":"이미 존재하는 아이디입니다."}`
- 공백 아이디 400: `{"detail":"아이디는 공백일 수 없습니다."}`
- 다른 형식/길이 실패 422: 안전한 detail 문자열
- DB 장애 500: 안전한 detail 문자열

## POST /api/auth/login

JSON `username/password`만 사용하며 form 로그인으로 바꾸지 않습니다.

```json
{"username":"codyssey123","password":"password1234"}
```

성공 200:

```json
{"access_token":"실제 JWT","token_type":"bearer"}
```

- 자격 증명 불일치 401: `{"detail":"아이디 또는 비밀번호가 올바르지 않습니다."}`
- 공백-only password 등 형식 실패 422: 안전한 detail 문자열

JWT는 HS256, 수명 1440분이며 서명·만료·sub와 실제 사용자 존재를 서버가 확인합니다.

## POST /api/chat

Bearer 인증이 필수입니다.

```json
{"question":"이번 주 프로젝트 4일 일정 요약해줘."}
```

성공 200 body에는 아래 두 필드만 반환합니다.

```json
{"answer":"AI가 반환한 비어 있지 않은 답변","latency_ms":520}
```

| 상황 | 상태 | detail |
|---|---:|---|
| 빈 문자열·공백 질문 | 400 | 질문 내용은 공백일 수 없습니다. |
| 인증 무효·만료·없음 | 401 | 인증 토큰이 유효하지 않거나 만료되었습니다. |
| 원문 500자 초과 | 422 | 질문은 최대 500자까지 입력 가능합니다. |
| 누락/null/잘못된 자료형·JSON | 422 | 입력 형식을 확인해 주세요. |
| AI timeout | 504 | 현재 AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요. |
| 그 외 AI 실패 | 504 | AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요. |
| DB 기록 장애 | 500 | 대화 기록을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요. |
| 예상하지 못한 서버 장애 | 500 | 서버 처리 중 오류가 발생했습니다. |

`question`은 `chat_logs.question`, 응답 `answer`는 DB의 `response`에 저장합니다. `reply`, `message`, `chat_id`, `ai_mode` 같은 구형 필드나 추가 body 필드를 사용하지 않습니다.

## GET /api/me/chats

Bearer 인증된 현재 사용자의 기록만 id 오름차순으로 반환합니다. 응답은 wrapper가 아닌 배열이며 빈 기록은 `[]`입니다.

```json
[
  {
    "id": 1,
    "question": "안녕?",
    "response": "안녕하세요!",
    "latency_ms": 420,
    "created_at": "2026-09-16T05:00:00"
  }
]
```

`hashed_password`, `username`, `user_id`, JWT를 응답하지 않습니다. 인증 실패는 401과 공통 토큰 안내입니다.

## GET /api/health

인증 없이 정확히 아래 JSON을 반환하며 실제 AI 호출 성공을 의미하지 않습니다.

```json
{"status":"ok"}
```

## 검증 오류 조정 기록

- S06 기본 FastAPI의 배열형 오류를 공통 `detail` 문자열로 정규화합니다.
- 실제 문자열 공백 질문과 공백-only 가입 아이디만 계약에 따라 400으로 조정합니다.
- 질문 길이는 trim 전 원문 기준이므로 내용 500자에 양끝 공백을 더한 502자도 422입니다.
- 보호 API에서는 인증 실패를 request body 검증보다 먼저 처리합니다.
- 실제 공급자의 401/403/429/5xx를 사용자 로그인 401로 전달하지 않고 504로 매핑합니다.
