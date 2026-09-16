# B7-1 풀스택 구현 명세 — 최신 첨부 계약 준수판

버전 2.0 / 기준일 2026-09-16 / 입력: 공식 미션 M + 첨부 S01~S11

## 0. 구현 목표와 최소 범위

이 문서는 빈 개인 저장소에서 Codex가 구현할 **실행 가능한 설계**다. 원자료가 없는 부분은 D 결정, 충돌은 C 결정으로 분리했다. 원문 API와 스키마는 부록에 전부 있다. 구현 전에 `PROJECT_PLAN.md`의 결정을 읽는다.

첫 완료 기준은 실제 회원가입·JWT·사용자별 SQLite·Mock을 거치는 브라우저 왕복이다. 이어 실제 AI adapter·문맥·실패/로그·실행/배포 문서·커밋 증거를 완성한다. 실제 AI/공개 URL/팀 이력은 외부 증거로 별도 통과한다. 프론트 추출이나 다른 백엔드 연결은 지금 하지 않는다.

필수 화면은 로그인/가입 모달, 질문 입력, 사용자/AI 메시지, 전송 중 표시, 오류 안내, 내 기록 복원, 로그아웃이다. 관리 화면, 페이지네이션, 스트리밍, 다중 방, 이메일 로그인, RAG, 데이터 수집, 모델 선택 UI는 제외한다.

## 1. 원자료를 배치하는 순서

이 여섯 입력 MD를 먼저 읽고, 문서 안의 S 블록에서 다음 파일을 만든다. S 블록의 원문은 수정하지 않고 실제 생성 파일에만 C 결정에 따른 패치를 적용한다.

| 원자료 | 실제 생성 파일 | 적용 방식 |
|---|---|---|
| S02 | requirements.txt | 모든 원래 패키지/하한 유지. 검증 후 constraints/lock 별도 생성 |
| S04 | .env.example | 원래 키/비밀값 아닌 견본 유지, 아래 보완 설정/예시 경고 추가 |
| S05 | .gitignore | 원문 + DB 부속파일/다른 env/키/테스트 산출물 제외 |
| S06 | app/schemas.py | 필드/모델 보존; C05 로그인 공백과 한국어 주석 보완만 명시적으로 적용 |
| S07 | docs/api_spec.md | 외부 계약 원문 보존; C/D 조정·원래 자료 지위를 끝에 기록 |
| S09~S11 | .github의 PR/Issue 템플릿 | PROJECT_PLAN의 블록을 복원; S10 마지막 fence 보완 |
| S01 | README.md | 현재 실제 구현·미실행 상태로 다시 작성. 원문처럼 완료된 것으로 선작성 금지 |
| S03 | AGENTS.md | 이미 패키지에 원문과 적용지침이 있음. 원문만 추출해 덮어쓰지 않음 |
| S08 | docs/PROJECT_PLAN.md 안에 보존 | 소문자 project_plan.md를 별도 생성해 입력 문서 덮어쓰기 금지 |

원문 복원과 단순 파일 복사만으로 본인의 기능 기여 10개를 충족했다고 세지 않는다. Source SHA와 정규화 방법은 PROJECT_PLAN에 있다.

## 2. 파일 구조와 모듈 책임

```text
.
├── AGENTS.md
├── CODEX_START.md
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── constraints.txt                  # 실제 호환 검증 후 작성
├── app/
│   ├── __init__.py
│   ├── main.py                      # lifespan, 오류 처리기, 라우터, static
│   ├── config.py                    # Pydantic Settings와 모드/비밀값 검증
│   ├── schemas.py                   # 첨부 Pydantic 모델 기반
│   ├── models.py                    # 필요 최소 DB 행 타입; ORM 아님
│   ├── database.py                  # aiosqlite, SQL, 짧은 트랜잭션
│   ├── auth.py                      # hash/verify, JWT, get_current_user
│   ├── ai_service.py                # messages, 실제 HTTP 호출, Mock
│   ├── logger.py                    # 6개 운영 이벤트
│   └── routers/
│       ├── __init__.py
│       ├── auth_router.py
│       └── chat_router.py
├── static/
│   ├── index.html
│   ├── css/style.css
│   └── js/
│       ├── api.js                   # 공통 통신, JSON/비JSON 오류
│       ├── auth.js                  # 모달/토큰/로그인 상태
│       └── app.js                   # 대화·기록·로딩·오류 화면
├── scripts/
│   ├── init_env.py
│   ├── check_logs.sql               # DB 대화 확인용
│   ├── check_db.py                  # SQL 실행용, 사용자 필터
│   ├── smoke_test.py
│   └── audit_contributions.py       # 실제 Git 이력 검증 보조
├── tests/
│   ├── conftest.py
│   ├── test_contract.py
│   ├── test_auth.py
│   ├── test_chat.py
│   ├── test_ai_service.py
│   ├── test_database_logging.py
│   └── test_frontend_contract.py
├── deploy/
│   ├── nginx.conf.template
│   ├── chatbot.service.template
│   └── render_config.py
├── .github/
│   ├── pull_request_template.md
│   └── ISSUE_TEMPLATE/
│       ├── bug_report.md
│       └── feature_request.md
├── data/                           # 실제 DB/부속파일 추적 금지
├── logs/                           # 운영 로그 추적 금지
└── docs/
    ├── MISSION_REQUIREMENTS.md
    ├── PROJECT_PLAN.md
    ├── IMPLEMENTATION_SPEC.md
    ├── MILESTONES.md
    ├── api_spec.md
    ├── DEPLOYMENT.md
    ├── IMPLEMENTATION_STATUS.md
    └── CONTRIBUTIONS.md
```

추가 빈 추상 계층이나 프레임워크를 만들지 않는다. app/main.py가 `GET /`에서 index.html, `/static/`에서 static만 제공한다. 저장소 전체를 정적 디렉터리로 mount하지 않는다. 프론트 API는 동일 origin의 `/api/...` 상대 URL이며 CORS/별도 프론트 서버는 필요 없다. docs 경로의 실제 대소문자는 일관되게 유지한다.

## 3. 의존성·설정·초기 기동

### 3.1 의존성

Python 3.10+와 S02 전체 패키지를 기본으로 사용한다. JWT는 `from jose import jwt, JWTError`, DB는 `aiosqlite`, 설정은 `pydantic_settings.BaseSettings`로 구현한다. form 로그인을 쓰지 않더라도 원자료의 python-multipart를 임의 삭제하지 않는다.

개별 패키지의 하한은 ‘모든 최신 조합이 호환됨’이 아니다. 깨끗한 로컬 가상환경에서 실제 resolve/install, `python -m pip check`, 필수 테스트를 수행하고 버전을 기록한다. constraints는 원자료 하한 범위 안에서 검증된 조합을 잠근다. 배포 환경 Python/OS에서도 확인한다. 테스트 안 된 lock을 ‘검증 완료’로 제공하지 않는다.

**C06/C07 해시 주의:** 이 신규 개인 DB의 기본 설계는 Passlib의 `bcrypt_sha256` v2다. 일반 bcrypt 해시와 포맷이 다르며 이는 100자 계약을 보존하기 위한 명시적 보완 결정이다. 후보로 passlib 1.7.4 + bcrypt 4.0.1 조합을 검증할 수 있으나 이 패키지 작성 환경에서는 설치가 차단되어 테스트하지 못했다. 현재 사용 가능한 조합을 확인하고 짧은 비밀번호, 100자 ASCII, 100자 한글, 72바이트 이후만 다른 값의 구분 테스트를 먼저 한다. 문제가 생기면 실패를 기록하고 호환 조합을 검증한다. 비밀번호를 72바이트로 자르거나 100자 API를 몰래 축소하지 않는다. 더 최신의 검증된 호환 조합이 있으면 근거와 테스트로 선택하되 원문 라이브러리 방향을 바꾸지 않는다.

새 해시 방식은 팀 기존 해시와 동일하다고 주장하지 않는다. 팀의 인증 담당자가 순수 bcrypt 포맷을 고정했다면 그 부분은 C06 재합의 대상이다. 이 패키지는 기존 DB 자동 변환을 하지 않는다.

### 3.2 설정의 기본값

S04의 이름과 기본값을 유지한다.

| 키 | 기준값·역할 |
|---|---|
| SECRET_KEY | 견본 문자열은 예시일 뿐. 실제 .env에는 로컬 무작위 생성값 |
| ALGORITHM | HS256 고정 허용 |
| ACCESS_TOKEN_EXPIRE_MINUTES | **1440** |
| DATABASE_URL | **sqlite:///./data/chatbot.db** (팀 기본값) |
| CODESSEY_API_KEY | 제공자가 발급한 키. 견본은 미설정 취급 |
| CODESSEY_API_BASE | S04 예시 주소 보존, 실제 제공자 주소로 검증 필요 |
| AI_MODEL_NAME | S04 gpt-4o-mini 예시 보존, 실제 제공 가능 모델 확인 필요 |
| AI_TIMEOUT_SECONDS | **8.0** |

보완 키는 `.env.example` 아래에 다음처럼 **추가**한다. 기존 키를 다른 철자로 바꾸지 않는다.

```dotenv
# 아래는 독립 구현의 추가 설정이며 기존 팀 키를 대체하지 않습니다.
APP_ENV=development
AI_MODE=auto
CONTEXT_TURNS=5
```

`APP_ENV`: development/test/production. `AI_MODE`: auto/mock/real. 3~5쌍 범위 중 기본5쌍, 질문 상한500은 스키마 그대로 유지한다. 미지원 설정값·음수 timeout 등은 시작 시 명확한 설정 오류로 처리한다. process env가 .env보다 우선한다.

`SECRET_KEY`가 없거나 견본이면 시작을 거부한다. `scripts/init_env.py`는 `.env`가 없을 때만 생성하며 `secrets.token_urlsafe(32)` 등으로 서명키를 만든다. 키를 stdout에 출력하지 않는다. 기존 .env를 덮어쓰거나 매 기동마다 키를 바꾸지 않는다. 실제 API 키는 빈 값으로 생성한다.

Mock 구분을 위해 `init_env.py --mode mock`은 `.env`의 DATABASE_URL을 **명시적으로** `sqlite:///./data/chatbot.mock.db`로 지정한다. 이는 개발 초기화 선택이며 S04 기본 DB를 임의로 몰래 바꾸는 동작이 아니다. 생성 결과 안내에는 경로·모드만 표시하고 비밀값은 표시하지 않는다. real 전환은 사용자가 .env의 AI_MODE와 키/제공자 정보, DB를 `data/chatbot.db`로 직접 확인해 바꾼다. 기존 Mock DB를 삭제하지 않는다. 테스트는 임시 DB를 사용한다.

### 3.3 AI 모드 판정표

| APP_ENV / AI_MODE | 키 상태 | 동작 |
|---|---|---|
| development/test + auto | 빈 값 또는 알려진 견본 | Mock, 분명한 표시, 외부 호출0 |
| development/test + auto | 실제로 보이는 비어 있지 않은 값 | real 경로; 실호출에는 사용자 승인 필요 |
| development/test + mock | 무관 | Mock만, 키 존재를 성공으로 해석 안 함 |
| development/test + real | 없음/견본 | 시작 설정 실패; 자동 Mock 금지 |
| production + auto/real | 유효하게 설정된 값 | real, 제공자 계약/외부 검증 필요 |
| production + 어떤 모드든 | 키 없음 또는 mock 명시 | 운영 기동 실패; 평가 완료로 위장 안 함 |

실제 키가 잘못됐다는 사실은 호출하기 전에는 알 수 없다. ‘값이 있음’과 ‘검증 완료’를 분리한다. real 오류/timeout 뒤 Mock으로 성공 응답을 반환하지 않는다. health/chat에 `X-AI-Mode: mock` 또는 `real` **응답 헤더**를 넣을 수 있다. 원래 JSON body는 바꾸지 않는다. Mock 답변에는 `[Mock]`을 포함한다.

### 3.4 .gitignore 보완

S05를 그대로 복원한 뒤 아래 규칙을 덧붙인다. 예시 파일을 다시 추적 가능하게 하는 순서도 유지한다.

```gitignore
# 다른 환경설정 파일과 개인 키 제외
.env.*
!.env.example
*.pem
*.key

# SQLite WAL/SHM/저널 등 부속파일 제외
*.db-*
*.sqlite-*
*.sqlite3-*

# 테스트·로컬 생성물 제외
.pytest_cache/
.coverage
htmlcov/
artifacts/
deploy/generated/
*.bak
```

`git check-ignore`로 DB 본체와 -wal/-shm, 다른 env, 키, 로그를 검사한다. 이미 tracked인 비밀값은 `.gitignore`만 추가해 해결된 것으로 보고하지 않는다. 발견하면 값을 출력하지 말고 경로만 보고하고 키 폐기/교체 등 별도 대응이 필요함을 알린다.

## 4. DB 모델 — S01을 따른다

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    question TEXT NOT NULL,
    response TEXT NOT NULL,
    latency_ms INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_chat_logs_user_id_id
ON chat_logs(user_id, id);
```

S01의 필드명을 바꾸지 않는다. username은 원문대로 trim만 하고 대소문자를 일방 소문자화하지 않는다. 등록·로그인에 같은 정규화를 적용한다. email/password_hash/ai_mode 컬럼을 추가하지 않는다.

연결별 foreign_keys 활성화, 제한된 busy_timeout, 시작 시 WAL을 설정한다. WAL은 .gitignore 보완과 함께 적용한다. 디렉터리가 없으면 생성하고 테이블은 최초 생성만 한다. 재기동 시 DROP/DELETE/시드 덮어쓰기를 하지 않는다. SQL은 매개변수 바인딩으로 실행한다.

AI 호출 전 현재 사용자의 최근 기록을 짧게 조회하고 연결/읽기를 정리한다. AI 응답 대기 동안 쓰기 트랜잭션을 열지 않는다. AI 응답을 받은 뒤 question/response/latency_ms를 한 행에 저장하고 **commit 성공 후** 200을 반환한다. 실패는 rollback, db_save_failed, 안전한500/detail이다. AI 실패는 정상 대화 행을 만들지 않는다.

조회는 항상 검증된 사용자 id로 제한한다. request body/query의 user_id를 소유권으로 신뢰하지 않는다. 내 기록은 id 오름차순, 문맥은 최신5개를 역순 조회 후 시간순으로 되돌린다. DB 전체를 브라우저에 노출하지 않는다.

created_at은 UTC를 사용하고 API에는 원자료 예시와 같은 `YYYY-MM-DDTHH:MM:SS`로 직렬화한다. 문자열에 offset이 없으므로 README에 UTC임을 분명히 적고 프론트는 UTC임을 알고 표시한다. 기존 DB 표기를 조용히 로컬 시각으로 재해석하지 않는다.

## 5. API 외부 계약 — S07/S06 우선

### 5.1 공통

POST는 JSON이며 form-data 로그인으로 바꾸지 않는다. UTF-8 JSON Content-Type을 사용하고 응답은 `application/json; charset=utf-8`로 일관되게 제공한다. FastAPI 기본 직렬화를 사용할 때도 문자 인코딩과 클라이언트 파싱을 검증한다.

성공/오류 JSON에 문서에 없는 필드를 필요 없이 추가하지 않는다. 오류는 `{"detail":"한국어 안내"}` 한 구조다. X-Request-ID 헤더로 요청 추적을 보완할 수 있지만 body에 error/request_id를 의무 추가하지 않는다.

S06 기본처럼 여분 필드는 무시할 수 있지만 사용자 식별/모델/API키로 사용하지 않는다. `email` 또는 `message`만 보낸 구형 요청은 필수 username/question이 없어422여야 한다. 별칭으로 자동 호환하지 않는다.

### 5.2 POST /api/auth/register

요청: `{"username":"codyssey123","password":"password1234"}`.

username은 문자열, 원문3~50자, 앞뒤 공백 제거 후 최소3자; 공백만은400. 내부 공백 처리는 원문 코드의 허용을 유지하며 문서의 의미 모호성은 C04에 기록했다. 숫자/null/누락, 길이 위반은422. password는 문자열4~100자, 공백만 금지; **값 자체는 trim하지 않는다**.

성공201:

```json
{"message":"회원가입이 완료되었습니다.","username":"codyssey123"}
```

중복400 `{"detail":"이미 존재하는 아이디입니다."}`. 공백 username400 `{"detail":"아이디는 공백일 수 없습니다."}`. 다른 검증 실패422/detail. DB 장애500/detail. UNIQUE 충돌과 일반 DB 실패를 구별한다. 등록 후 별도 로그인하며 자동 계정·기본 비밀번호를 생성하지 않는다.

### 5.3 POST /api/auth/login

요청 JSON은 username/password. S06처럼 username을 trim하고 빈 값 검증, C05에 따라 password 공백-only도422 처리한다. 존재하지 않는 계정/잘못된 비밀번호는 동일401 안내. 가입 정책상 불가능한 지나치게 긴 비밀번호는 hash 검증을 우회하여 동일 인증 실패로 처리할 수 있으나 비밀번호를 잘라 비교하면 안 된다.

성공200:

```json
{"access_token":"실제 발급된 JWT","token_type":"bearer"}
```

실패401: `{"detail":"아이디 또는 비밀번호가 올바르지 않습니다."}`.

JWT는 python-jose로 HS256 서명·검증. 이 구현의 sub는 S06 TokenData와 맞춘 username 문자열이고 iat/exp를 포함한다. sub 선택은 원문 공백을 채운 내부 결정이며 클라이언트가 sub를 신뢰해서 사용자 소유권을 결정하면 안 된다. 수명1440분. 서명키/비밀번호를 payload에 넣지 않는다.

### 5.4 보호 API 공통

`Authorization: Bearer <access_token>`. `get_current_user`가 Bearer형식, HS256 고정검증, 서명, exp, sub, 실제 DB 사용자 존재를 검사한다. 없거나 위조/만료/삭제계정이면401이며 `WWW-Authenticate: Bearer`를 포함한다. 인증 의존성 기본403에 맡기지 않는다.

인증되지 않은 요청은 body가 잘못됐더라도 이 구현에서401을 우선 반환하며 AI/DB 쓰기를 호출하지 않는다. 검증 순서를 테스트한다. S07이 혼합오류 우선순위를 지정하지 않아 선택한 내부 정책이다.

### 5.5 POST /api/chat

요청:

```json
{"question":"이번 주 프로젝트 4일 일정 요약해줘."}
```

성공200:

```json
{"answer":"AI가 실제로 반환한 답변","latency_ms":520}
```

answer는 비어 있지 않은 문자열, latency_ms는0이상 정수이며 AI 호출/응답 처리 구간의 측정값이다. 미리 적은520은 예시일 뿐 실제 응답에 고정하지 않는다. `reply/message/chat_id/ai_mode/created_at`를 성공 body에 넣지 않는다.

DB 저장 시는 `ChatRequest.question` → `chat_logs.question`, `ChatResponse.answer` → `chat_logs.response`, latency_ms → 같은 필드로 정확히 매핑한다. 이름 차이를 API 버그로 오해해 response를 answer로 바꾸지 않는다.

| 상황 | HTTP | detail |
|---|---:|---|
| 질문 빈 문자열 또는 공백만 | 400 | 질문 내용은 공백일 수 없습니다. |
| 인증 무효·만료·없음 | 401 | 인증 토큰이 유효하지 않거나 만료되었습니다. |
| 질문 원문 길이500 초과 | 422 | 질문은 최대 500자까지 입력 가능합니다. |
| question 누락/null/배열/숫자/JSON 파싱 실패 | 422 | 입력 형식을 확인해 주세요. 등 안전한 문자열 |
| AI timeout | 504 | 현재 AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요. |
| 그 외 외부 AI 실패/잘못된 응답 | 504 | AI 응답을 가져오지 못했습니다. 잠시 후 다시 시도해 주세요. |
| DB 저장·조회 장애 | 500 | 대화 기록을 처리하지 못했습니다. 잠시 후 다시 시도해 주세요. |
| 예상하지 못한 내부 장애 | 500 | 서버 처리 중 오류가 발생했습니다. |

AI의401/403/429/500 등을 그대로 전달하지 않는다. S03의504 규칙을 유지하며 서버 로그에서 원인 구분한다. DB500은 원자료에 없는 실패 케이스를 위한 명시적 보완이다.

### 5.6 GET /api/me/chats

현재 사용자만, body 없음,200과 **배열**. id 오름차순, 기록 없음은 `[]`. 페이지네이션/사용자선택 query를 추가하지 않는다.

```json
[
  {"id":1,"question":"안녕?","response":"안녕하세요!","latency_ms":420,"created_at":"2026-09-16T05:00:00"}
]
```

`response_model=list[ChatLogItem]`. S06의 ChatHistoryResponse 클래스는 원문에 보존하되 이 경로에서는 사용하지 않는다. hashed_password·username·user_id·JWT는 반환하지 않는다.

### 5.7 GET /api/health

인증 없이200 `{"status":"ok"}`. 실제 AI를 호출하지 않는다. 필요하면 X-AI-Mode 응답헤더로 개발 모드를 알린다. health 성공은 실제 AI·DB 저장·배포 E2E를 보증하지 않는다.

### 5.8 검증 오류를 계약과 맞추는 방법

첨부 S06을 무작정 재작성하지 않는다. `RequestValidationError` 처리기에서 원래 route·오류필드·자료형을 분기하고 응답을 C02/C03에 맞춘다. `exc.body`에서 검증에 필요한 필드만 볼 수 있으나 전체 body를 기록/반사하지 않는다.

질문이 실제 문자열이고 strip 후 빈 경우400을 먼저 적용한다. 문자열이면서 빈값이 아니고 **원문 길이**가500 초과면422. 그 외 자료형/누락 오류는422다. 정상 질문은 원문의 after validator처럼 최대길이 검증 후 trim한다. 따라서 양끝공백+내용500자=502자는422다. ‘trim후500’이라는 이전 패키지의 정책을 가져오지 않는다. 비밀번호를 trim하는 것과 질문 trim을 혼동하지 않는다.

가입도 username 공백-only만400으로 정규화한다. 나머지 필드와 다른 API의422를 무차별400으로 바꾸지 않는다. 모든 detail은 안전한 한국어 문자열로 직렬화한다. Pydantic msg/input/ctx의 원문을 그대로 뿌리지 않는다. 404/405·예상하지 못한 API500도 detail 구조를 유지한다. Nginx/네트워크 등 앱 밖 오류는 JSON 아닐 수 있으므로 프론트도 방어한다.

OpenAPI에는 Request/Response 모델과400/401/422/504/500의 실제 오류 모델을 등록한다. JSON 로그인인 만큼 Swagger 인증은 HTTP Bearer로 지원하고 OAuth form token 흐름을 잘못 연결하지 않는다. `/docs`·`/redoc`과 `docs/api_spec.md`의 계약을 대조하는 테스트를 둔다.

## 6. 인증과 비밀번호의 내부 구현

`hash_password` / `verify_password`는 `passlib.hash.bcrypt_sha256` v2를 호출한다. 무작위 salt, 기본 rounds12를 사용하며 테스트에서만 별도 낮은 rounds를 주입할 수 있다. 본 방식은 원시 bcrypt 포맷이 아니므로 README에 설명한다. 팀 저장소로 옮기는 단계는 이번 범위가 아니고 기존 팀 해시를 자동 변경하지 않는다.

비밀번호는UTF-8 전체를 동일 함수로 hash/verify하고 72바이트 이후가 다른100자 문자열이 서로 인증되지 않는지 검증한다. 암호 포맷을 직접 발명하거나 HMAC/전처리를 자체 재구현하지 않는다. 준비된 라이브러리의 문서화된 scheme을 사용한다. 단순 SHA256만 저장하거나 입력을 잘라 bcrypt에 넘기지 않는다.

CPU 비용이 있는 해시/검증은 async 라우트의 event loop를 오래 막지 않도록 thread 경계를 사용한다. bcrypt 버전/설치 실패를 사용자401로 조용히 숨기지 않는다. 설정/라이브러리 오류는 서버 장애로 보고하고 사용자 비밀번호와 hash는 로그에 남기지 않는다.

로그아웃은 localStorage 토큰과 현재 화면 삭제다. 이미 복사된 JWT를 즉시 서버에서 폐기하는 기능은 없고 기본 만료1440분이라는 한계를 README에 적는다. refresh token/블랙리스트/비밀번호 재설정은 만들지 않는다.

## 7. AI·문맥·Mock

### 7.1 호출 흐름과 인터페이스

`chat_router.py`: 인증 → 질문 검증 → 현재 사용자 최근5쌍 조회 → messages 조합 → AI 함수 호출 → DB 저장 → 응답. AI 모듈은 인증/DB 트랜잭션/HTTPException을 직접 소유하지 않는다.

개념 인터페이스:

```python
async def generate_ai_response(messages: list[dict[str, str]], *, request_id: str) -> AIResult:
    """대화 문맥을 보내 답변과 소요 시간을 반환합니다."""
```

AIResult는 answer:str, latency_ms:int의 작은 dataclass/타입이다. timeout/upstream/response 오류는 전용 예외 또는 분류코드로 전달하여 라우터가 팀 규칙의504로 매핑한다. DB 담당자가 외부 공급자 구조를 직접 파싱하게 하지 않는다.

### 7.2 문맥

system 한 개 → 최근 성공대화5쌍을 과거부터 user(question)/assistant(response) → 현재 question 한 개. user_id 조건은 서버에서 얻는다. 다른 사용자, 실패 안내, 현재 질문 중복을 넣지 않는다. ‘5쌍’은10개 메시지이며 전체 DB 저장개수의 상한이 아니다.

Mock와 real은 초기화/전환 시 별도 DB 경로를 명시해 분리한다. 실모드 전환 전에 Mock 데이터가 섞였는지 확인하고 무단 삭제하지 않는다. ai_mode 필드를 API/DB에 새로 추가해 해결하지 않는다. 실제 모델의 토큰 한도는 미확인이고 5쌍이 토큰 상한을 보장하지 않는다.

### 7.3 실제 공급자 adapter

S08의 ‘OpenAI 호환’을 기준으로 최초 adapter는 서버에서 `{base.rstrip('/')}/chat/completions`에 POST한다. `/v1`이 날아가거나 두 번 붙지 않게 테스트한다. 키는 Authorization Bearer, body는 model/messages/stream=false, 응답은 `choices[0].message.content`의 문자열을 기대한다. 이는 **첨부 기획을 구현 가능한 형태로 만든 가정**이며 코디세이의 실제 제공자 계약을 검증했다는 뜻이 아니다.

S04에 있는 OpenAI URL/모델을 코드에 박지 않고 설정에서 읽는다. 실행 전 실제 제공자 주소·사용 권한을 확인한다. GPT/Claude 이름을 보고 프로토콜을 임의 혼용하지 않는다. 실제 공급자 응답이 다르면 확인된 내용에 맞춰 adapter만 고치고 외부 /api/chat 계약은 유지한다.

httpx.AsyncClient를 lifespan에서 생성/종료하고 TLS 검증을 끄지 않는다. timeout8.0을 설정하고 Python3.10 호환 `asyncio.wait_for`로 AI await 제한을 함께 둔다. 취소 정리 시간을 포함한 절대벽시계8초 보장으로 설명하지 않는다. 자동 재시도는 하지 않는다.

공급자 에러 원문·인증헤더·키가 있는 URL·사용자 전체 대화는 응답/로그에 남기지 않는다. 상태/에러 종류/request_id만 기록한다. 네트워크 장애·비JSON·빈 content·JSON구조 불일치는 실패다.

### 7.4 Mock

외부 HTTP 호출 없이 실제 인증/DB/라우터를 거친다. Mock 답변은 `[Mock]` 표식을 포함한다. 기본은 간단한 결정적 응답이며 직전 질문을 묻는 테스트에서는 전달된 history의 직전 user 항목을 이용한다. 구현 입력에 이전 질문이 실제로 포함됐는지 별도 spy로 검증한다. 이를 실제 모델의 문맥 이해 성공이라고 쓰지 않는다.

오류를 일부러 내는 테스트는 dependency/transport 주입으로 만든다. 공개 사용자에게 특정 문자열 입력 시 인증을 우회하거나 DB를 망가뜨리는 백도어를 제공하지 않는다.

## 8. 서버 로그와 대화 DB 확인

Python logging으로 아래 원자료의 이벤트를 남긴다. 네 범주·6개 세부 이벤트이다.

```text
INFO request_received user_id={user_id} path={path}
INFO ai_call_start user_id={user_id} request_id={request_id}
INFO ai_call_success request_id={request_id} latency_ms={latency_ms}
INFO db_save_success user_id={user_id} chat_id={chat_id}
ERROR ai_call_failed request_id={request_id} error={error_detail}
ERROR db_save_failed user_id={user_id} error={error_detail}
```

추가 request_id 필드를 수신/DB 이벤트 뒤에 붙여 연결할 수 있으나 원래 이벤트 이름·필수 필드는 지운다거나 변경하지 않는다. 인증 전 거절은 user_id=anonymous처럼 로그하고 실제 id를 꾸미지 않는다. Mock은 별도 mode 정보로 구분한다. 실패 상세는 안전한 분류명이며 비밀번호/JWT/API키/원문 전체를 기록하지 않는다.

stdout과 `logs/app.log`에 기록하거나 systemd journal에서 확인한다. 동일 handler 중복 등록으로 한 요청이 중복 출력되지 않게 한다. DB 오류 주입 테스트로 db_save_failed를 실제 확인하고, 이후 정상 요청이 성공하는지 검사한다.

`scripts/check_logs.sql`은 DB만 검사한다.

```sql
SELECT id, user_id, question, response, latency_ms, created_at
FROM chat_logs
WHERE user_id = :user_id
ORDER BY id DESC
LIMIT 20;
```

`scripts/check_db.py --user-id 1`처럼 현재 설정의 DB에 읽기 연결하여 바인딩한 SQL을 실행한다. 이 내부 도구는 운영자 로컬 확인용이고 인터넷에 무인증 공개하지 않는다. DB 검사 결과를 Git에 올릴 때는 테스트 전용 데이터만 사용한다.

README에는 `python scripts/check_db.py --user-id ...`와 운영 로그 확인 방법을 **서로 다른 절차**로 적는다. 실제 user_id는 실행결과에서 얻고 존재하지 않는1을 고정 사용자라고 설명하지 않는다.

## 9. 프론트엔드

### 9.1 기본 구조

Vanilla HTML/CSS/JS만 사용하며 API 호출은 api.js에 모은다. auth.js는 가입/로그인·모달·토큰, app.js는 질문·답변·기록·로딩·오류를 관리한다. addEventListener, fetch, async/await, try/catch/finally를 사용한다. ES module로 분리 가능하다.

로그인창 username/password, 가입창 같은 필드. 가입은201을 안내한 뒤 로그인으로 이동한다. 성공 토큰은 localStorage의 `access_token`에 저장한다. 비밀번호는 저장하지 않는다. 로그인 후 /api/me/chats를 불러와 이전 기록을 표시한다.

질문 입력은 `JSON.stringify({question})`, 답변은 data.answer를 표시한다. 과거 기록은 item.response를 표시한다. latency_ms는 표시해도 되고 생략해도 되나 API필드/DB저장은 유지한다. 기존 reply/message 키를 참조하지 않는다.

### 9.2 상태 처리

비로그인·로그인/가입 중·기록 로딩·빈 기록·질문 전송 중·성공·400/422·401·504·500·네트워크/비JSON 오류를 처리한다. 전송 중 버튼/Enter 중복을 막고 finally에서 복원한다. 자동 POST 재시도는 하지 않는다.

401은 보호 API의 현재 세션 요청에만 토큰 삭제/로그인 모달로 처리한다. 로그인 실패401은 해당 모달 오류로 표시해 반복 루프를 만들지 않는다. 로그아웃 시 진행요청을 취소하거나 세션번호로 늦은 응답을 무시하여 이전 사용자의 답변이 새 사용자에게 보이지 않게 한다.

질문 원문 code point 길이와 공백 여부를 서버와 동일하게 검사한다. JS에서는 `Array.from(value).length`를 사용할 수 있다. HTML maxlength의UTF-16 길이만으로 다른 기준을 강제하지 않는다. 앞뒤 공백 포함 raw500 상한, whitespace-only400을 기준으로 맞춘다. 클라이언트 검증은 편의이고 서버검증은 필수다.

### 9.3 최소 UX·안전성

사용자/AI/내 기록은 `textContent`와 `white-space: pre-wrap`로 렌더링한다. innerHTML/외부 스크립트/Markdown 렌더러를 추가하지 않는다. 반응형은 좁은 모바일과 데스크톱에서 스크롤/입력창이 사용 가능한 수준이면 충분하다. 입력 label, 버튼 역할, 키보드 포커스·오류 안내를 제공한다.

Enter 전송/Shift+Enter줄바꿈을 제공한다면 한글 IME의 `isComposing`을 확인한다. 초기에 구현 부담이 있으면 버튼 전송부터 만들고 이후 실제 테스트 후 추가한다. UI 테스트 없는 상태를 브라우저 검증 PASS라고 말하지 않는다.

health의 X-AI-Mode 및 Mock 답변 표식으로 개발 모드를 표시한다. body에 새로운 mode 키가 있다고 가정하지 않는다. localStorage의 XSS 위험과 클라이언트 로그아웃의 한계는 숨기지 않는다.

## 10. 테스트 — 원문 계약을 실제로 검증

자동 테스트는 임시 DB·가짜 AI transport/dependency를 사용한다. 운영 DB/실키에 단위 테스트를 돌리지 않는다. 아래 T는 최소 구현 회귀기준이며 실행한 것만 PASS로 쓴다.

| ID | 검사 | 기대 |
|---|---|---|
| T01 | 기동, /, 정적 리소스, health | 정상 HTML/CSS/JS, health body 정확히status |
| T02 | 가입/중복 | 201 message+username, 중복400/detail문자열 |
| T03 | username 공백/2자/51자/trim/내부공백 | C04와 S06 일치, 대소문자 일방 변환 없음 |
| T04 | password3/4/100/101/공백 | 경계값 정책, 평문 저장 없음 |
| T05 | 100자 ASCII·한글 hash/verify, 72바이트 이후만 차이 | 올바른 값만 인증, 절단 없음; C06 핵심 |
| T06 | 로그인 성공/실패/공백 |200 토큰,401 동일 안내, 공백-only422 |
| T07 | JWT 서명·만료·sub·알고리즘·없는 사용자 | 유효 사용자만 통과, 나머지401 |
| T08 | chat/history 미인증/변조/만료 |401, AI/DB쓰기 없음 |
| T09 | JSON vs form, 필수 key 구형 email/message | 계약 JSON만, 구형 필드만이면422 |
| T10 | 정상Mock 채팅 |200 answer/latency_ms 정확한 타입, 실제DB 저장 |
| T11 | 질문 '', 공백,500/501, padded502, emoji |400/422 규칙과 원문 길이 기준 일치 |
| T12 | 누락/null/숫자/배열/잘못된JSON |422/detail문자열, 원문 비밀정보 비반사 |
| T13 | history 배열/빈값/정렬/필드 |배열,[],id오름차순, response/latency_ms/created_at |
| T14 | 사용자A/B격리, body user_id 조작 |본인 기록/문맥만 |
| T15 | DB재시작 |성공 대화 보존, DROP/초기화 없음 |
| T16 | 6쌍 기록의 최근5쌍 문맥 |시스템1+과거10메시지+현재1, 올바른 순서 |
| T17 | real adapter transport |URL/v1·Bearer·model/messages·응답파싱 검증, 외부실호출 아님 |
| T18 | HTTPX timeout/전체 AI 제한 |504/detail, ai_call_failed, 이후 정상처리 |
| T19 | 공급자401/429/500·네트워크·비JSON·빈답변 |사용자401/가짜Mock 성공 아닌504 |
| T20 | DB삽입/commit 실패 주입 |500/detail,rollback,db_save_failed,정상행 없음 |
| T21 | 정상/AI실패/DB실패 운영로그 |6개 이벤트 실제 경로, 키/토큰/비밀번호 비노출 |
| T22 | Git 제외/HTTP 정적노출 |.env/DB/wal/shm/log/key 비추적·다운로드불가 |
| T23 | Mock자동선택·real설정실패·모드전환 |키없음 개발Mock,운영실패,장애fallback없음 |
| T24 | OpenAPI vs api_spec vs schemas |필드/상태/배열/공통오류 일치 |
| T25 | 브라우저 가입→로그인→채팅→재로그인기록 |실제DOM과fetch; 도구없으면NOT_RUN |
| T26 | 중복전송/504/500/비JSON/로딩복구 |멈춤없이 안내,버튼복원 |
| T27 | 로그아웃 후 늦은응답·새 사용자 |이전사용자 대화 비표시 |
| T28 | HTML태그 문자열·모바일·키보드·IME |스크립트 실행없음,사용 가능한 화면 |
| T29 | SQL확인도구 |현재설정DB에서 사용자조건 실제조회 |
| T30 | 새 가상환경 재현 |requirements+constraints로설치,pip check,필수pytest |
| T31 | 실제AI 두턴 |승인된 제공자·실제응답·문맥·DB·로그,Mock대체불가 |
| T32 | 외부배포 |외부네트워크에서실제인증/AI,재시작보존 |
| T33 | 개인·팀커밋/PR증빙 |평가브랜치의작성자별10개+유의미성+실PR |

T31~T33의 외부조건은 BLOCKED_EXTERNAL/NEEDS_TEAM_REVIEW로 둘 수 있지만 최종미션 PASS라고 말하면 안 된다. T25~T28은 정적코드만 읽고 브라우저 테스트를 했다고 적지 않는다. `smoke_test.py`는 테스트 사용자/임시DB로 최소 API왕복을 실행하고 실키를 출력하지 않는다.

## 11. 배포 — 마지막 장식이 아니라 필수 준비

목표는 S01/S03의 EC2 t2.micro/Ubuntu22.04/Nginx/systemd이다. 실제 계정 무료혜택·리전·CPU아키텍처/패키지 호환·비용한도를 먼저 확인한다. 새 AWS 리소스/포트/인증서는 승인 없이 생성하지 않는다. 외부 URL을 만들지 않은 상태에서 템플릿만으로 배포완료라고 표시하지 않는다.

Uvicorn은 단일 worker, 배포에서는 127.0.0.1:8000 바인딩과 --reload 없음으로 운영한다. Nginx가 80번 포트를 받아 API와 화면 요청을 전달한다. 최소 구현에서는 FastAPI가 정적 파일까지 제공하도록 proxy해도 된다. S01 아키텍처의 Nginx 직접 static 서빙은 배포 세부 선택으로 구분한다. 서비스는 비root 실행 계정, 재시작 정책, 영속 DB 디렉터리를 사용한다.

2GB Swap은 이번 팀의 배포 규칙으로 포함한다. 현재 swap과 디스크를 먼저 확인하고 이미 구성되어 있다면 중복 생성하지 않는다. fstab에 무조건 append하지 않으며 추가·재시작 후 확인법을 문서화한다. Swap 구성이 OOM을 완전히 막는다고 보장하지 않는다.

머신별 WorkingDirectory와 ExecStart 등은 템플릿 placeholder에 실제 배포 값을 대입한다. 저장소에 개인 홈 경로를 하드코딩하는 것과 OS가 요구하는 절대경로를 구분한다. C10의 팀 해석이 없다면 배포 적용은 대기하되 로컬 템플릿 생성은 가능하다. 생성 결과는 deploy/generated에 두어 추적에서 제외한다. 자동 sudo, systemd 설치, 서비스 재시작은 하지 않는다.

HTTP 80만 공개하는 원계획과 HTTPS가 필요한 보안상 이유는 C11에 기록한다. 443 추가와 TLS는 팀·운영자 승인 후 반영한다. 임시 HTTP 평가 시연을 선택해도 재사용 비밀번호, 개인정보, 민감 대화를 넣지 않으며 위험과 공개 시간 제한을 명시한다. 일반 사용자 대상 서비스의 안전성을 확보했다고 표현하지 않는다. SSH 22는 승인된 팀원 IP로 제한하고 8000은 외부 비공개를 유지한다.

Nginx 대기시간은 AI 8초와 DB 처리 여유보다 길게 설정하고 측정한다. 비용·요청 빈도 제한과 공급자 한도를 운영자에게 안내하되 완전한 비용 상한 보장으로 쓰지 않는다. 서비스 재시작 뒤 DB와 키 보존을 확인한다. 공개 접속 검증은 다른 네트워크에서 한다.

## 12. README·증거·협업 산출물

README는 S01의 역할, 아키텍처, DB, API 방향을 유지하며 실제 결과에 맞춘다. 문제 정의, 가정한 타겟, 핵심 시나리오, 실행 버전, 로컬 명령, 설정 키, Mock/real 구분, API 예시, DB 표, SQL·운영 로그 확인, 배포, 개인 기여를 빠짐없이 포함한다. GitHub 링크와 공개 URL에 실제 값이 없다면 미확정·미배포라고 쓴다.

`docs/CONTRIBUTIONS.md`는 이 개인 저장소의 본인 작업과 팀의 예정 역할을 구분한다. MILESTONES의 실제 작업 단위마다 검증 후 커밋하고 SHA를 남긴다. 본인 10개와 다른 팀원의 10개는 서로 대체되지 않는다. audit_contributions.py는 정확한 기준 커밋, 대상 브랜치, 작성자 이메일을 입력받아 non-merge SHA·파일·제목을 집계한다. 의미성은 사람이 검토하며, 실제 조회나 수동 증거가 없는 원격 PR은 NOT_RUN이다. 서로 다른 사람 명의를 인위적으로 만들지 않는다.

PR·Issue 양식을 실제 디렉터리에 복원하고 확인한 항목만 체크한다. PR 초안에는 변경, 테스트, 검토 대상, 미실행 항목, 연결 Issue를 적는다. 존재하지 않는 Issue 번호는 넣지 않는다. 원격 변경 승인 전에는 초안만 만들고, 최종 평가 전에는 실제 PR merge와 개인별 커밋 증거를 확인해야 한다.

IMPLEMENTATION_STATUS에는 실제 명령, 출력 요약, 환경, T01~T33과 M01~M21의 상태를 기록한다. C 결정 적용과 팀 확인 대기, 로컬·실제 AI·공개 URL·팀 이력은 구분한다. 증빙 문서 업데이트를 이유로 빈 커밋을 반복하지 않는다. 테스트 실패를 숨기거나 결과가 없는 곳에 임의 PASS를 쓰지 않는다.

## 13. 원자료 보존 블록을 읽는 방법

아래는 첨부 그대로의 개발 입력이다. 예시 API 키, 외부 URL, 모델은 실제 사용 권한의 증명이 아니다. C/D 적용 전 원문은 변경하지 않고 생성한 파일에 필요한 수정을 기록한다. 원문 블록의 영문 주석과 가짜 토큰은 보존 근거이지 실제 운영 값으로 사용하라는 지시가 아니다.

## 원자료 S02 — `requirements.txt`

원래 배치 대상: `requirements.txt`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S02 -->
````text
# [웹 프레임워크 및 ASGI 서버]
fastapi>=0.100.0
uvicorn[standard]>=0.23.0

# [데이터 유효성 검증 및 환경변수 로드]
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0

# [비동기 HTTP 클라이언트 (코디세이 AI API 호출)]
httpx>=0.25.0

# [인증 및 보안 (비밀번호 해싱 & JWT 토큰)]
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
bcrypt>=4.0.0
python-multipart>=0.0.6

# [비동기 데이터베이스 지원 (SQLite)]
aiosqlite>=0.19.0

# [테스트 도구 (선택 사항)]
pytest>=7.0.0
pytest-asyncio>=0.21.0
````
<!-- SOURCE_END:S02 -->

## 원자료 S04 — `.env.example`

원래 배치 대상: `.env.example`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S04 -->
````dotenv
# [보안 설정]
SECRET_KEY="your_super_secret_jwt_key_here"
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# [데이터베이스 경로]
DATABASE_URL="sqlite:///./data/chatbot.db"

# [코디세이 AI API 설정 (500만 토큰 제공)]
CODESSEY_API_KEY="your_codessey_api_key"
CODESSEY_API_BASE="https://api.openai.com/v1"
AI_MODEL_NAME="gpt-4o-mini"
AI_TIMEOUT_SECONDS=8.0
````
<!-- SOURCE_END:S04 -->

## 원자료 S05 — `.gitignore`

원래 배치 대상: `.gitignore`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S05 -->
````gitignore
# Python 가상환경
.venv/
venv/
__pycache__/
*.pyc

# 보안 및 환경 변수 (절대 깃허브 업로드 금지!)
.env
.env.local

# SQLite 데이터베이스 파일 (과제 제약조건 충족)
*.db
*.sqlite
*.sqlite3
data/*.db

# 로그 파일
logs/
*.log

# OS 및 IDE 설정
.DS_Store
.vscode/
.idea/
````
<!-- SOURCE_END:S05 -->

## 원자료 S06 — `schemas.py`

원래 배치 대상: `app/schemas.py`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S06 -->
````python
"""FastAPI 애플리케이션 Pydantic 요청 및 응답 데이터 스키마 정의 모듈.

본 모듈은 프론트엔드와 백엔드 간 통신 규약(API Contract)을 정의하며,
클라이언트 요청 데이터의 자동 유효성 검증 및 Swagger UI 대화형 API 문서 생성을 담당합니다.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# 1. 인증 관련 스키마 (Authentication Schemas)
# ============================================================================

class UserRegisterRequest(BaseModel):
    """신규 사용자 회원가입 요청 스키마."""

    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="사용자 로그인 아이디 (3자 이상 50자 이하)",
    )
    password: str = Field(
        ...,
        min_length=4,
        max_length=100,
        description="사용자 로그인 비밀번호 (최소 4자 이상)",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """아이디의 공백 여부를 검증하고 앞뒤 공백을 제거합니다."""
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("아이디는 공백일 수 없습니다.")
        if len(trimmed) < 3:
            raise ValueError("아이디는 최소 3자 이상이어야 합니다.")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """비밀번호의 공백 여부를 검증합니다."""
        if not value or not value.strip():
            raise ValueError("비밀번호는 공백일 수 없습니다.")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "codyssey123",
                "password": "password1234",
            }
        }
    )


class UserRegisterResponse(BaseModel):
    """신규 사용자 회원가입 성공 응답 스키마."""

    message: str = Field(
        default="회원가입이 완료되었습니다.",
        description="회원가입 성공 안내 메시지",
    )
    username: str = Field(
        ...,
        description="등록 완료된 사용자 계정 아이디",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "회원가입이 완료되었습니다.",
                "username": "codyssey123",
            }
        }
    )


class UserLoginRequest(BaseModel):
    """사용자 로그인 및 토큰 발급 요청 스키마."""

    username: str = Field(
        ...,
        description="사용자 로그인 아이디",
    )
    password: str = Field(
        ...,
        description="사용자 로그인 비밀번호",
    )

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        """로그인 아이디의 앞뒤 공백을 제거하고 빈 문자열을 검증합니다."""
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("아이디를 입력해 주세요.")
        return trimmed

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        """로그인 비밀번호 입력을 검증합니다."""
        if not value:
            raise ValueError("비밀번호를 입력해 주세요.")
        return value

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "username": "codyssey123",
                "password": "password1234",
            }
        }
    )


class TokenResponse(BaseModel):
    """로그인 성공 시 반환되는 JWT 액세스 토큰 응답 스키마."""

    access_token: str = Field(
        ...,
        description="JWT 기반 인증 액세스 토큰 문자열",
    )
    token_type: str = Field(
        default="bearer",
        description="토큰 인증 방식 (기본값: bearer)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
            }
        }
    )


class TokenData(BaseModel):
    """JWT 토큰 디코딩 및 검증 결과 보관용 스키마."""

    username: Optional[str] = Field(
        default=None,
        description="토큰 페이로드에서 추출한 사용자 계정 아이디",
    )


# ============================================================================
# 2. AI 챗봇 대화 관련 스키마 (Chat Schemas)
# ============================================================================

class ChatRequest(BaseModel):
    """AI 챗봇 질문 전송 요청 스키마."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="사용자가 질문할 텍스트 내용 (최대 500자)",
    )

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        """질문 문자열의 공백 여부를 검증하고 앞뒤 공백을 제거합니다."""
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("질문 내용은 공백일 수 없습니다.")
        if len(trimmed) > 500:
            raise ValueError("질문은 최대 500자까지 입력 가능합니다.")
        return trimmed

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "question": "이번 주 프로젝트 4일 일정 요약해줘.",
            }
        }
    )


class ChatResponse(BaseModel):
    """AI 챗봇 질문에 대한 응답 반환 스키마."""

    answer: str = Field(
        ...,
        description="AI 모델이 생성한 답변 내용",
    )
    latency_ms: int = Field(
        ...,
        ge=0,
        description="AI 호출 및 응답 처리에 소요된 시간 (밀리초 단위)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "answer": "이번 주 4일 프로토타입 프로젝트 일정은 Day 1 독립 모듈 세팅, Day 2 코어 로직 완성, Day 3 E2E 결합, Day 4 안정성 점검 및 배포 순서로 진행됩니다.",
                "latency_ms": 520,
            }
        }
    )


class ChatLogItem(BaseModel):
    """사용자의 개별 대화 이력 로그 단일 항목 스키마."""

    id: int = Field(
        ...,
        description="대화 이력 식별자 (PK)",
    )
    question: str = Field(
        ...,
        description="사용자가 입력했던 질문 내용",
    )
    response: str = Field(
        ...,
        description="AI가 생성했던 답변 내용",
    )
    latency_ms: int = Field(
        default=0,
        ge=0,
        description="답변 생성 소요 시간 (밀리초)",
    )
    created_at: datetime = Field(
        ...,
        description="대화 기록 생성 일시 (ISO 8601 형식)",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "question": "안녕? 너는 누구야?",
                "response": "안녕하세요! AI 어시스턴트입니다.",
                "latency_ms": 420,
                "created_at": "2026-09-15T20:45:00",
            }
        },
    )


class ChatHistoryResponse(BaseModel):
    """대화 이력 목록 응답 래퍼 스키마 (필요 시 목록 감싸기 용도)."""

    chats: List[ChatLogItem] = Field(
        default_factory=list,
        description="사용자의 대화 이력 목록",
    )

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "chats": [
                    {
                        "id": 1,
                        "question": "안녕?",
                        "response": "안녕하세요! AI 어시스턴트입니다.",
                        "latency_ms": 420,
                        "created_at": "2026-09-15T20:45:00",
                    }
                ]
            }
        },
    )


# ============================================================================
# 3. 공통 시스템 및 오류 응답 스키마 (System & Error Schemas)
# ============================================================================

class HealthResponse(BaseModel):
    """서버 헬스체크 응답 스키마."""

    status: str = Field(
        default="ok",
        description="서버 가용 상태 (정상: ok)",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "ok",
            }
        }
    )


class ErrorDetailResponse(BaseModel):
    """서버 공통 오류 응답 상세 스키마."""

    detail: str = Field(
        ...,
        description="오류 발생 상세 원인 메시지",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "아이디 또는 비밀번호가 올바르지 않습니다.",
            }
        }
    )
````
<!-- SOURCE_END:S06 -->

## 원자료 S07 — `api_spec.md`

원래 배치 대상: `docs/api_spec.md`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S07 -->
````markdown
# B7-1 웹 기반 AI 챗봇 REST API 명세서 (API Contract)

> **문서 버전**: v1.0.0  
> **최종 수정일**: 2026-09-15  
> **기본 Base URL**: `/api` (로컬 테스트: `http://localhost:8000/api`)  
> **대화형 문서**: `http://localhost:8000/docs` (Swagger UI), `http://localhost:8000/redoc` (ReDoc)  
> **관련 소스 파일**: `B7-1/7-1/app/schemas.py`, `B7-1/7-1/app/routers/`

---

## 1. 개요 및 공통 통신 규칙 (Global Conventions)

본 문서는 프론트엔드(`static/`)와 백엔드(`app/`) 간 데이터 통신 접지면을 사전에 확정하여, 병렬 개발 시 발생할 수 있는 필드 불일치 및 통신 에러를 방지하기 위한 **API 규약(API Contract)**입니다.

### 1.1 HTTP 요청/응답 헤더
- **요청 Body 포맷**: `Content-Type: application/json; charset=utf-8`
- **응답 Body 포맷**: `Content-Type: application/json; charset=utf-8`
- **인증 헤더 (보안 엔드포인트 필수)**:
  ```http
  Authorization: Bearer <access_token>
  ```

### 1.2 날짜 및 시간 포맷
- 모든 일시는 **ISO 8601** 문자열 형식을 따릅니다.
- 포맷: `YYYY-MM-DDTHH:MM:SS` (예: `2026-09-15T22:45:00`)

### 1.3 표준 오류 응답 형식 (Common Error Response)
모든 에러 상황(4xx, 5xx)에서 백엔드는 일관된 JSON 구조로 오류 원인을 반환합니다:
```json
{
  "detail": "오류 상세 설명 메시지"
}
```

---

## 2. API 엔드포인트 요약 (Overview)

| 번호 | 메서드 | URI 경로 | 인증 필요 | 기능 설명 | 성공 응답 |
| :---: | :---: | :--- | :---: | :--- | :---: |
| 1 | `POST` | `/api/auth/register` | X | 신규 사용자 회원가입 | `201 Created` |
| 2 | `POST` | `/api/auth/login` | X | 사용자 로그인 및 JWT 토큰 발급 | `200 OK` |
| 3 | `POST` | `/api/chat` | **O (필수)** | AI 챗봇 질문 전송 및 답변 수신 | `200 OK` |
| 4 | `GET` | `/api/me/chats` | **O (필수)** | 로그인 사용자의 대화 이력 목록 조회 | `200 OK` |
| 5 | `GET` | `/api/health` | X | 서버 상태 및 가용성 확인 (헬스체크) | `200 OK` |

---

## 3. 상세 엔드포인트 규격

### 3.1 [POST] 회원가입 (`/api/auth/register`)
신규 사용자 계정을 생성합니다. 비밀번호는 서버에서 `bcrypt` 단방향 해싱 후 저장됩니다.

- **URL**: `/api/auth/register`
- **Method**: `POST`
- **Authentication**: 없음

#### Request Body
| 필드명 | 타입 | 필수 여부 | 유효성 제약 | 설명 |
| :--- | :---: | :---: | :--- | :--- |
| `username` | `string` | **필수** | 3자 이상 50자 이하, 공백 불가 | 사용자 로그인 아이디 |
| `password` | `string` | **필수** | 4자 이상 100자 이하 | 계정 비밀번호 |

```json
{
  "username": "codyssey123",
  "password": "password1234"
}
```

#### Success Response (`201 Created`)
```json
{
  "message": "회원가입이 완료되었습니다.",
  "username": "codyssey123"
}
```

#### Error Response
- **400 Bad Request** (아이디 중복 또는 공백):
  ```json
  {
    "detail": "이미 존재하는 아이디입니다."
  }
  ```
- **422 Unprocessable Entity** (유효성 검사 실패):
  ```json
  {
    "detail": "아이디는 최소 3자 이상이어야 합니다."
  }
  ```

---

### 3.2 [POST] 로그인 및 JWT 발급 (`/api/auth/login`)
아이디와 비밀번호를 검증하고, 이후 인증 요청에 사용할 JWT 액세스 토큰을 발급합니다.

- **URL**: `/api/auth/login`
- **Method**: `POST`
- **Authentication**: 없음

#### Request Body
| 필드명 | 타입 | 필수 여부 | 유효성 제약 | 설명 |
| :--- | :---: | :---: | :--- | :--- |
| `username` | `string` | **필수** | 공백 불가 | 사용자 로그인 아이디 |
| `password` | `string` | **필수** | 공백 불가 | 계정 비밀번호 |

```json
{
  "username": "codyssey123",
  "password": "password1234"
}
```

#### Success Response (`200 OK`)
프론트엔드는 수신한 `access_token`을 `localStorage`에 보관하고 이후 API 호출 헤더에 첨부합니다.
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### Error Response
- **401 Unauthorized** (자격 증명 불일치):
  ```json
  {
    "detail": "아이디 또는 비밀번호가 올바르지 않습니다."
  }
  ```

---

### 3.3 [POST] AI 챗봇 질문 전송 (`/api/chat`)
로그인된 사용자가 질문을 전송하면, 백엔드는 최근 대화 문맥을 조합하여 AI API를 호출하고 응답과 응답 시간(latency_ms)을 반환하며 SQLite DB에 기록합니다.

- **URL**: `/api/chat`
- **Method**: `POST`
- **Authentication**: **필수** (`Authorization: Bearer <access_token>`)

#### Request Headers
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn...
Content-Type: application/json; charset=utf-8
```

#### Request Body
| 필드명 | 타입 | 필수 여부 | 유효성 제약 | 설명 |
| :--- | :---: | :---: | :--- | :--- |
| `question` | `string` | **필수** | 1자 이상 500자 이하, 공백 불가 | 사용자가 질문할 내용 |

```json
{
  "question": "이번 주 프로젝트 4일 일정 요약해줘."
}
```

#### Success Response (`200 OK`)
| 필드명 | 타입 | 설명 |
| :--- | :---: | :--- |
| `answer` | `string` | AI 모델이 생성한 답변 내용 |
| `latency_ms` | `integer` | AI API 처리 및 응답 생성 소요 시간 (밀리초) |

```json
{
  "answer": "이번 주 4일 프로토타입 프로젝트 일정은 Day 1 독립 모듈 세팅, Day 2 코어 로직 완성, Day 3 E2E 결합, Day 4 안정성 점검 및 배포 순서로 진행됩니다.",
  "latency_ms": 520
}
```

#### Error Response
- **400 Bad Request** (공백 질문 입력):
  ```json
  {
    "detail": "질문 내용은 공백일 수 없습니다."
  }
  ```
- **401 Unauthorized** (토큰 누락, 위변조 또는 만료):
  ```json
  {
    "detail": "인증 토큰이 유효하지 않거나 만료되었습니다."
  }
  ```
- **422 Unprocessable Entity** (500자 초과 등):
  ```json
  {
    "detail": "질문은 최대 500자까지 입력 가능합니다."
  }
  ```
- **504 Gateway Timeout** (AI API 호출 8.0초 초과):
  ```json
  {
    "detail": "현재 AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요."
  }
  ```

---

### 3.4 [GET] 내 대화 이력 목록 조회 (`/api/me/chats`)
로그인한 본인의 대화 기록 목록을 최신순 또는 등록순으로 반환합니다.

- **URL**: `/api/me/chats`
- **Method**: `GET`
- **Authentication**: **필수** (`Authorization: Bearer <access_token>`)

#### Request Headers
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsIn...
```

#### Request Body
- 없음

#### Success Response (`200 OK`)
대화 객체의 배열(`Array<ChatLogItem>`) 형태로 반환됩니다.
```json
[
  {
    "id": 1,
    "question": "안녕?",
    "response": "안녕하세요! AI 어시스턴트입니다.",
    "latency_ms": 420,
    "created_at": "2026-09-15T20:45:00"
  },
  {
    "id": 2,
    "question": "너의 역할은 뭐야?",
    "response": "저는 사용자의 질문에 친절하고 정확하게 답변해 드리는 챗봇입니다.",
    "latency_ms": 610,
    "created_at": "2026-09-15T20:45:30"
  }
]
```

#### Error Response
- **401 Unauthorized**:
  ```json
  {
    "detail": "인증 토큰이 유효하지 않거나 만료되었습니다."
  }
  ```

---

### 3.5 [GET] 서버 헬스체크 (`/api/health`)
서버 인스턴스가 정상 동작 중인지 확인하는 헬스체크 엔드포인트입니다.

- **URL**: `/api/health`
- **Method**: `GET`
- **Authentication**: 없음

#### Success Response (`200 OK`)
```json
{
  "status": "ok"
}
```

---

## 4. 프론트엔드 연동 가이드 (Frontend Integration Guide)

프론트엔드 담당(이준혁)은 백엔드 완성 전이라도 아래 표준 통신 함수 패턴과 가짜 데이터(Mocking)를 사용하여 UI를 독립적으로 완성할 수 있습니다.

### 4.1 인증 토큰 관리 및 공통 Fetch 래퍼 (예시)
```javascript
// static/js/auth.js 또는 static/js/app.js
const API_BASE = '/api';

// 인증 헤더 획득 함수
function getAuthHeader() {
  const token = localStorage.getItem('access_token');
  return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// 챗봇 질문 비동기 전송 함수
async function sendChatMessage(question) {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeader(),
    },
    body: JSON.stringify({ question }),
  });

  if (response.status === 401) {
    alert('로그인이 만료되었습니다. 다시 로그인해주세요.');
    localStorage.removeItem('access_token');
    showLoginModal();
    return null;
  }

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || '채팅 요청 처리에 실패했습니다.');
  }

  return data; // { answer: "...", latency_ms: 520 }
}
```

### 4.2 프론트엔드 Mock 테스트용 더미 응답 데이터
백엔드 서버 연동 전 로컬 브라우저 단독 개발 시 아래 더미 데이터를 활용하여 채팅 버블 렌더링, 로딩 인디케이터 동작, 에러 토스트 피드백을 테스트할 수 있습니다:

```javascript
// 가짜(Mock) AI 응답 예시
const MOCK_CHAT_RESPONSE = {
  answer: "안녕하세요! [Mock] 프론트엔드 인터페이스 검증용 테스트 답변입니다.",
  latency_ms: 350
};
```
````
<!-- SOURCE_END:S07 -->
