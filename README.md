# AI Assistant

> B7-1 웹 기반 AI 챗봇 개인 풀스택 기준 구현

## 현재 상태

이 저장소는 팀 Organization과 분리된 개인 기준 구현입니다. 최신 명세와 API 계약의 로컬 구현·재현 게이트를 완료했으며, 외부 조건과 실제 결과는 `docs/IMPLEMENTATION_STATUS.md`에 분리해 기록합니다.

- `LOCAL_MINIMUM`: PASS — 새 가상환경 설치부터 Mock 풀스택·브라우저·DB·실패 복구까지 로컬 검증했습니다.
- `REAL_AI`: BLOCKED_EXTERNAL — 실제 공급자 계약·키·호출 승인이 필요합니다.
- `PUBLIC_URL`: BLOCKED_EXTERNAL — AWS/비용/외부 공개 승인이 필요합니다.
- `TEAM_HISTORY`: NEEDS_TEAM_REVIEW — 개인 저장소 이력은 팀 4명 기여·PR 증거를 대신하지 않습니다.

백엔드와 `static/` 브라우저 프론트는 회원가입·로그인·보호 채팅·최근 5쌍 문맥·Mock 답변·사용자별 SQLite 저장/조회·오류 복구·모바일 키보드 흐름까지 연결했습니다. 실제 SQLite INSERT·COMMIT 실패의 rollback과 복구, 격리 smoke, 읽기 전용 DB 조회, Git 범위 감사, EC2 설정 렌더링, 완전한 새 가상환경의 205개 Python 테스트를 통과했습니다. OpenAI 호환 adapter는 가짜 HTTP transport로 검증했지만 실제 공급자 호출, 공개 URL, 팀 PR은 승인·외부 증거 대기입니다. 따라서 로컬 최소 구현 PASS는 미션 전체 완료를 뜻하지 않습니다.

## 문제와 사용자

로그인한 사용자가 한 화면에서 질문하고, 현재 사용자의 최근 대화를 문맥으로 이어가며, 자신의 기록을 다시 확인할 수 있는 최소 AI 채팅 서비스를 만듭니다. 학습자와 일반 사용자를 초기 대상으로 가정하며, 특정 정책·도메인 기능은 범위에 넣지 않습니다.

핵심 시나리오는 회원가입 → 로그인 → 인증된 질문 → 서버 AI 호출 → SQLite 저장 → 화면 표시 → 내 기록 재조회 → 로그아웃입니다.

## 확정 기술과 계약

- Python 3.10+, FastAPI, Uvicorn, aiosqlite, httpx, python-jose, Passlib/bcrypt
- Vanilla HTML/CSS/JavaScript; 실행 파일과 정적 자원은 모두 `static/`에 배치
- `users`, `chat_logs` 두 테이블과 최근 5쌍 문맥
- `username/password`, `question`, `answer/latency_ms`, 기록의 `response`
- JSON 오류는 항상 `{"detail":"한국어 문자열"}`
- JWT 1440분, AI 제한 8초, 질문 원문 최대 500자

비밀번호는 4~100자 계약과 원시 bcrypt의 72바이트 경계를 함께 지키기 위해 Passlib의 `bcrypt_sha256` v2로 저장합니다. 입력을 자르거나 단순 SHA-256으로 저장하지 않습니다. 이는 일반 bcrypt 포맷과 다르므로 기존 팀 DB에 자동 적용하지 않습니다.

로그인은 JSON `username/password`를 검증한 뒤 HS256 JWT를 발급합니다. 토큰에는 `sub`, `iat`, `exp`가 들어가며 기본 수명은 1440분입니다. 보호 API는 서명·알고리즘·만료·필수 claims뿐 아니라 `sub`의 사용자가 DB에 실제 존재하는지도 확인합니다. 클라이언트 로그아웃은 브라우저 토큰 삭제 방식이므로 이미 복사된 JWT를 서버에서 즉시 폐기하지 못하며, refresh token·블랙리스트는 현재 최소 범위에 포함하지 않습니다.

외부 계약의 기준은 `docs/api_spec.md`, 충돌 결정은 `docs/PROJECT_PLAN.md`, 구현 상세는 `docs/IMPLEMENTATION_SPEC.md`입니다. 프론트는 같은 origin의 `/api/...`만 호출하고 Python 모듈·서버 템플릿·`.env`에 직접 의존하지 않습니다. 선택 응답 헤더 `X-AI-Mode`가 없어도 핵심 기능은 동작해야 합니다.

## 구현 구조

```text
브라우저 static/ → FastAPI /api → 인증/JWT → AI adapter 또는 Mock
                                      └→ SQLite data/chatbot.db
```

FastAPI는 `/`에서 `static/index.html`, `/static/`에서 필요한 정적 자원만 제공합니다. 저장소 전체나 `.env`, DB, 로그는 정적으로 노출하지 않습니다.

개발·테스트의 `AI_MODE=mock`은 외부 HTTP를 전혀 호출하지 않고 `[Mock]` 표식이 있는 결정적 응답을 반환하지만, 인증·문맥 조회·DB commit은 실제 경로를 사용합니다. `AI_MODE=real`에서 키가 없으면 기동을 거부합니다. real 경로는 설정한 절대 HTTPS base의 `/chat/completions`를 한 번 호출하며 timeout·공급자·응답 오류를 504로 처리하고 Mock으로 자동 전환하지 않습니다. 이 경로는 가짜 transport로만 검증했으며 실제 공급자 계약·키·모델은 아직 확인하지 않았습니다.

같은 사용자의 동시 채팅은 단일 서버 프로세스 안에서 사용자별 turn lock으로 직렬화합니다. 문맥 조회 뒤 AI를 기다리는 동안 SQLite 쓰기 트랜잭션은 열지 않으며, 배포는 명세대로 Uvicorn 단일 worker를 전제로 합니다. 다중 worker/다중 인스턴스에는 별도의 분산 순서 제어가 필요합니다.

## API 요약

프론트와 서버의 기준 계약은 `docs/api_spec.md`이며, 아래 다섯 경로를 같은 origin에서 사용합니다.

| Method / path | 인증 | 요청 | 성공 응답 |
|---|---|---|---|
| `GET /api/health` | 없음 | 없음 | 200 `{"status":"ok"}` |
| `POST /api/auth/register` | 없음 | `username`, `password` JSON | 201 `message`, `username` |
| `POST /api/auth/login` | 없음 | `username`, `password` JSON | 200 `access_token`, `token_type="bearer"` |
| `POST /api/chat` | Bearer JWT | `question` JSON | 200 `answer`, `latency_ms` |
| `GET /api/me/chats` | Bearer JWT | 없음 | 200 기록 객체의 JSON 배열 |

보호 API는 `Authorization: Bearer <token>`을 요구합니다. 질문 공백은 400, 일반 schema 오류는 422, 인증 실패는 401, AI 장애는 504, DB/서버 장애는 500이며 body는 모두 문자열 `detail`을 사용합니다. 기록 객체는 `id`, `question`, `response`, `latency_ms`, `created_at`을 포함하고 `user_id`나 wrapper 없이 배열로 반환합니다.

## SQLite 구조

| 테이블 | 필드 | 역할 |
|---|---|---|
| `users` | `id`, `username`, `hashed_password`, `created_at` | 고유 username과 단방향 비밀번호 해시 |
| `chat_logs` | `id`, `user_id`, `question`, `response`, `latency_ms`, `created_at` | 인증 사용자별 성공 대화 누적 |

`chat_logs.user_id`는 `users.id` 외래키이고 `(user_id, id)` 인덱스로 사용자별 문맥·기록 조회를 보완합니다. SQLite `CURRENT_TIMESTAMP`의 UTC 시각을 API에서 초 단위 문자열로 표시합니다. 성공 대화는 commit 뒤에만 응답하고, 실패 시 rollback합니다. 앱 재시작은 `CREATE TABLE IF NOT EXISTS`와 WAL을 적용할 뿐 기존 행을 초기화하지 않습니다.

## 환경 설정

로컬 Mock 개발은 `scripts/init_env.py --mode mock`으로 시작합니다. 이 도구는 `.env`가 없을 때만 무작위 `SECRET_KEY`, 빈 API 키, `sqlite:///./data/chatbot.mock.db`, `APP_ENV=development`, `AI_MODE=mock`을 만들며 키를 출력하지 않습니다. 기존 `.env`는 덮어쓰지 않습니다. `.env.example`의 키·URL은 형식 예시일 뿐 운영값이 아닙니다.

필수·보완 설정 이름:

- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL`
- `CODESSEY_API_KEY`, `CODESSEY_API_BASE`, `AI_MODEL_NAME`, `AI_TIMEOUT_SECONDS`
- `APP_ENV`, `AI_MODE`, `CONTEXT_TURNS`

real 전환은 `.env`에서 AI 모드·실제 키·확인된 HTTPS provider·model·`data/chatbot.db`를 운영자가 직접 함께 검토해야 합니다. 기존 Mock DB는 삭제하지 않습니다. 실제 AI URL·모델·권한은 확인되지 않았고 유료 호출은 별도 승인 전 실행하지 않습니다.

## 로컬 설치와 실행

저장소 루트에서 Python 3.10+ 가상환경을 만들고 `requirements.txt`를 검증된 `constraints.txt`와 함께 설치합니다. Windows에서는 먼저 실제 Python 3.10+ 실행 파일을 `$PythonExe`로 지정하고 버전을 확인합니다. 이 Codex 검증 호스트는 `py` launcher가 없어 아래 bundled Python 3.12.14 경로를 사용했습니다. 일반 환경에서는 첫 줄을 설치된 `python.exe`의 절대 경로로 바꾸면 되며, PowerShell 실행 정책을 바꿀 필요는 없습니다.

```powershell
$PythonExe = "$env:USERPROFILE/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe"
& $PythonExe --version
& $PythonExe -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -c constraints.txt
.venv/Scripts/python.exe -m pip check
.venv/Scripts/python.exe scripts/init_env.py --mode mock
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.venv/Scripts/python.exe -m pytest
```

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -c constraints.txt
.venv/bin/python -m pip check
.venv/bin/python scripts/init_env.py --mode mock
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.venv/bin/python -m pytest
```

브라우저 검증 주소는 `http://127.0.0.1:8000`입니다. HTML 파일을 직접 여는 방식은 지원하지 않습니다.

`constraints.txt`는 Windows의 Python 3.12.14에서 새 가상환경 설치·`pip check`·전체 회귀·해시 smoke를 통과한 41개 패키지 조합입니다. 주요 실제 버전은 FastAPI 0.141.1, Uvicorn 0.53.0, aiosqlite 0.22.1, HTTPX 0.28.1, Pydantic 2.13.5, Passlib 1.7.4, bcrypt 4.0.1입니다. 최신 bcrypt 5.0.0은 이 환경의 Passlib backend 탐지에서 실패하여, 긴 입력 구분 테스트를 통과한 4.0.1을 고정했습니다. 배포 Python/OS에서는 다시 설치 검증해야 합니다.

## 로컬 검증 도구

아래 명령은 저장소 루트에서 실행합니다. 최소 API smoke는 현재 `.env`와 운영 DB를 읽지 않고 임시 DB·Mock 모드·외부 호출 차단 transport를 사용합니다. 토큰·비밀번호·질문·응답 본문은 출력하지 않습니다.

```powershell
.venv/Scripts/python.exe scripts/smoke_test.py
```

DB 대화 기록은 현재 `DATABASE_URL`이 가리키는 기존 SQLite 파일을 읽기 전용으로 엽니다. 먼저 로그인한 사용자로 대화 한 건을 만든 뒤 로컬 `logs/app.log` 또는 systemd journal의 해당 `request_received user_id=... path=/api/chat`에서 인증된 실제 ID를 확인하며, `1`을 고정 사용자라고 가정하지 않습니다. 기록 API는 `user_id`를 노출하지 않습니다. 이 도구는 질문과 답변 원문을 표시하므로 로컬 운영자만 실행하고 실제 사용자 결과를 Git·Issue·채팅에 붙이지 않습니다.

```powershell
.venv/Scripts/python.exe scripts/check_db.py --user-id <실제 사용자 ID>
```

`scripts/check_logs.sql`도 같은 **DB 대화 기록**을 확인하는 고정 SQL이며 `:user_id`를 바인딩합니다. 서버 운영 이벤트는 별개입니다. 로컬 파일 로그는 `Get-Content -LiteralPath logs/app.log -Tail 100`, 배포 후 journal은 `journalctl -u ai-assistant -n 100 --no-pager`로 확인합니다.

개인 Git 후보 감사는 저장소·대상 ref·기준 SHA·정확한 작성자 이메일을 모두 명시합니다. 로컬 이력만 읽고 fetch/push하지 않으며, 커밋 수가 기준을 넘어도 내용 검토나 실제 PR을 자동 PASS 처리하지 않습니다.

```powershell
.venv/Scripts/python.exe scripts/audit_contributions.py `
  --repository . `
  --ref feat/fullstack-lee `
  --base 6b2ff28ab3947884b5ffe6f54f3bf28b60107d42 `
  --author-email ljh951206@gmail.com
```

## 문서와 증빙

- 공식 미션: `docs/MISSION_REQUIREMENTS.md`
- 적용 결정: `docs/PROJECT_PLAN.md`
- 구현 명세: `docs/IMPLEMENTATION_SPEC.md`
- 작업 순서: `docs/MILESTONES.md`
- API 계약: `docs/api_spec.md`
- 프론트 실행·이식 경계: `docs/FRONTEND_GUIDE.md`
- EC2 배포 절차·승인 경계: `docs/DEPLOYMENT.md`
- 실행·검증 상태: `docs/IMPLEMENTATION_STATUS.md`
- 실제 기여 기록: `docs/CONTRIBUTIONS.md`
- 여섯 흐름 직접 설명용 초안: `docs/PERSONAL_EXPLANATION.md`
- 원격 생성 전 PR 본문 초안: `docs/PR_DRAFT.md`

GitHub 저장소는 현재 `https://github.com/Cerhovah/Codyssey_Mission_B7-1`로 설정되어 있지만 이번 작업의 원격 push·PR·merge는 승인 전 보류합니다. 공개 서비스 URL은 아직 없습니다.

## 역할과 실제 구현자 구분

첨부 계획의 예정 역할은 고준석(인증/PM), 박범규(백엔드/DB), 이준혁(프론트), 차종민(AI)입니다. 이 개인 저장소의 현재 변경은 Git에 기록된 실제 작성자만의 작업이며, 예정 역할을 다른 팀원이 수행 완료한 것으로 표시하지 않습니다.
