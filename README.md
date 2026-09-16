# AI Assistant

> B7-1 웹 기반 AI 챗봇 개인 풀스택 기준 구현

## 현재 상태

이 저장소는 팀 Organization과 분리된 개인 기준 구현입니다. 현재는 명세·API 계약·보안 제외 규칙·검증 증빙 틀을 복원한 준비 단계이며, 기능별 구현과 검증 결과는 `docs/IMPLEMENTATION_STATUS.md`에 사실대로 갱신합니다.

- `LOCAL_MINIMUM`: NOT_RUN
- `REAL_AI`: BLOCKED_EXTERNAL — 실제 공급자 계약·키·호출 승인이 필요합니다.
- `PUBLIC_URL`: BLOCKED_EXTERNAL — AWS/비용/외부 공개 승인이 필요합니다.
- `TEAM_HISTORY`: NEEDS_TEAM_REVIEW — 개인 저장소 이력은 팀 4명 기여·PR 증거를 대신하지 않습니다.

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

외부 계약의 기준은 `docs/api_spec.md`, 충돌 결정은 `docs/PROJECT_PLAN.md`, 구현 상세는 `docs/IMPLEMENTATION_SPEC.md`입니다. 프론트는 같은 origin의 `/api/...`만 호출하고 Python 모듈·서버 템플릿·`.env`에 직접 의존하지 않습니다. 선택 응답 헤더 `X-AI-Mode`가 없어도 핵심 기능은 동작해야 합니다.

## 예정 구조

```text
브라우저 static/ → FastAPI /api → 인증/JWT → AI adapter 또는 Mock
                                      └→ SQLite data/chatbot.db
```

FastAPI는 `/`에서 `static/index.html`, `/static/`에서 필요한 정적 자원만 제공합니다. 저장소 전체나 `.env`, DB, 로그는 정적으로 노출하지 않습니다.

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
.venv/Scripts/python.exe -m pip install -r requirements.txt
.venv/Scripts/python.exe scripts/init_env.py --mode mock
.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.venv/Scripts/python.exe -m pytest
```

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python scripts/init_env.py --mode mock
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
.venv/bin/python -m pytest
```

브라우저 검증 주소는 `http://127.0.0.1:8000`입니다. HTML 파일을 직접 여는 방식은 지원하지 않습니다.

## 문서와 증빙

- 공식 미션: `docs/MISSION_REQUIREMENTS.md`
- 적용 결정: `docs/PROJECT_PLAN.md`
- 구현 명세: `docs/IMPLEMENTATION_SPEC.md`
- 작업 순서: `docs/MILESTONES.md`
- API 계약: `docs/api_spec.md`
- 실행·검증 상태: `docs/IMPLEMENTATION_STATUS.md`
- 실제 기여 기록: `docs/CONTRIBUTIONS.md`

GitHub 저장소는 현재 `https://github.com/Cerhovah/Codyssey_Mission_B7-1`로 설정되어 있지만 이번 작업의 원격 push·PR·merge는 승인 전 보류합니다. 공개 서비스 URL은 아직 없습니다.

## 역할과 실제 구현자 구분

첨부 계획의 예정 역할은 고준석(인증/PM), 박범규(백엔드/DB), 이준혁(프론트), 차종민(AI)입니다. 이 개인 저장소의 현재 변경은 Git에 기록된 실제 작성자만의 작업이며, 예정 역할을 다른 팀원이 수행 완료한 것으로 표시하지 않습니다.
