# AI Assistant

> B7-1 웹 기반 AI 챗봇 개인 풀스택 기준 구현

## 현재 상태

이 저장소는 팀 Organization과 분리된 개인 기준 구현입니다. 최신 명세와 API 계약을 기준으로 기능 단위 개발 중이며, 실제 구현·검증 결과는 `docs/IMPLEMENTATION_STATUS.md`에 사실대로 갱신합니다.

- `LOCAL_MINIMUM`: NOT_RUN
- `REAL_AI`: BLOCKED_EXTERNAL — 실제 공급자 계약·키·호출 승인이 필요합니다.
- `PUBLIC_URL`: BLOCKED_EXTERNAL — AWS/비용/외부 공개 승인이 필요합니다.
- `TEAM_HISTORY`: NEEDS_TEAM_REVIEW — 개인 저장소 이력은 팀 4명 기여·PR 증거를 대신하지 않습니다.

현재 백엔드와 `static/` 브라우저 프론트는 회원가입·로그인·보호 채팅·최근 5쌍 문맥·Mock 답변·사용자별 SQLite 저장/조회·오류 복구·모바일 키보드 흐름까지 로컬에서 연결했습니다. OpenAI 호환 AI adapter는 가짜 HTTP transport로 계약·timeout·오류 경로를 검증했지만 실제 공급자 호출은 승인 대기입니다. 실제 SQLite INSERT·COMMIT 실패의 rollback과 복구도 검증했으며, 운영 확인 도구와 최종 재현 게이트가 남아 있어 `LOCAL_MINIMUM`은 아직 `NOT_RUN`입니다.

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

## 환경 설정

`.env.example`을 `.env`로 복사한 뒤 `SECRET_KEY`를 실제 무작위 값으로 바꿉니다. `scripts/init_env.py`가 구현되면 기존 파일을 덮어쓰지 않고 로컬 설정을 안전하게 만들 예정입니다.

필수·보완 설정 이름:

- `SECRET_KEY`, `ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`
- `DATABASE_URL`
- `CODESSEY_API_KEY`, `CODESSEY_API_BASE`, `AI_MODEL_NAME`, `AI_TIMEOUT_SECONDS`
- `APP_ENV`, `AI_MODE`, `CONTEXT_TURNS`

예시 키는 실제 비밀값이 아니며 운영에 사용할 수 없습니다. 실제 AI URL·모델·권한은 확인되지 않았고 유료 호출은 별도 승인 전 실행하지 않습니다.

## 개발 실행 계획

아래 명령은 해당 파일이 구현된 뒤 사용합니다. Windows에서는 PowerShell 실행 정책을 바꾸지 않고 가상환경 Python을 직접 호출할 수 있습니다.

```powershell
py -3.10 -m venv .venv
.venv/Scripts/python.exe -m pip install -r requirements.txt -c constraints.txt
.venv/Scripts/python.exe scripts/init_env.py --mode mock
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.venv/Scripts/python.exe -m pytest
```

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt -c constraints.txt
.venv/bin/python scripts/init_env.py --mode mock
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.venv/bin/python -m pytest
```

브라우저 검증 주소는 `http://127.0.0.1:8000`입니다. HTML 파일을 직접 여는 방식은 지원하지 않습니다.

`constraints.txt`는 Windows의 작업공간 Python 3.12.14에서 실제 설치·`pip check`·해시 smoke를 통과한 조합입니다. 특히 `passlib 1.7.4`와 최신 `bcrypt 5.0.0` 조합은 이 환경의 backend 탐지에서 실패하여, 긴 입력 구분 테스트를 통과한 `bcrypt 4.0.1`을 고정했습니다. 배포 Python/OS에서는 다시 설치 검증해야 합니다.

## 문서와 증빙

- 공식 미션: `docs/MISSION_REQUIREMENTS.md`
- 적용 결정: `docs/PROJECT_PLAN.md`
- 구현 명세: `docs/IMPLEMENTATION_SPEC.md`
- 작업 순서: `docs/MILESTONES.md`
- API 계약: `docs/api_spec.md`
- 프론트 실행·이식 경계: `docs/FRONTEND_GUIDE.md`
- 실행·검증 상태: `docs/IMPLEMENTATION_STATUS.md`
- 실제 기여 기록: `docs/CONTRIBUTIONS.md`

GitHub 저장소는 현재 `https://github.com/Cerhovah/Codyssey_Mission_B7-1`로 설정되어 있지만 이번 작업의 원격 push·PR·merge는 승인 전 보류합니다. 공개 서비스 URL은 아직 없습니다.

## 역할과 실제 구현자 구분

첨부 계획의 예정 역할은 고준석(인증/PM), 박범규(백엔드/DB), 이준혁(프론트), 차종민(AI)입니다. 이 개인 저장소의 현재 변경은 Git에 기록된 실제 작성자만의 작업이며, 예정 역할을 다른 팀원이 수행 완료한 것으로 표시하지 않습니다.
