# B7-1 AGENTS.md — 첨부 자료 우선 · 미션 최소 완성 우선

버전 2.0 / 검토 기준일 2026-09-16

## 1. 현재 작업의 목적과 읽을 문서

이 저장소는 **팀 Organization과 별개인 개인 풀스택 기준 구현용 빈 저장소**다. 필요한 11개 첨부파일 원문은 이 여섯 MD의 `SOURCE_BEGIN` 블록에 모두 들어 있다. 원격 저장소나 이전 ChatGPT 대화를 찾아야 개발할 수 있다고 가정하지 않는다. 이미 코드가 있으면 현재 변경과 데이터부터 보존한다.

이번 범위는 회원가입·로그인 → 인증된 질문 → 서버 AI 호출 → 현재 사용자 문맥 → SQLite 저장 → 화면 표시 → 오류/로그 → 외부 배포 준비까지의 완결된 풀스택이다. **프론트 추출, 팀 백엔드로 교체, 별도 서비스화는 하지 않는다.**

먼저 아래 문서를 실제로 끝까지 읽는다. 길면 분할해서 읽는다. 원문 보존 블록과 현재 적용 지침을 구분한다.

1. `docs/MISSION_REQUIREMENTS.md`: 공식 미션 제공 본문, M01~M21, 최소 완료 기준.
2. `docs/PROJECT_PLAN.md`: 11개 파일 출처, 이전 패키지 대조, 충돌 C01~C24·보완 D01~D06, 팀 계획과 템플릿.
3. `docs/IMPLEMENTATION_SPEC.md`: 새 첨부 API·스키마·환경·의존성을 따르는 구현과 테스트, 원자료 S02/S04/S05/S06/S07.
4. `docs/MILESTONES.md`: 최소기능 먼저 만드는 순서, 실제 기능 단위 20커밋, 각 팀원 10기여 계획과 검증.
5. `CODEX_START.md`: 사용 방법, 이번 실행의 허용 범위, 시작/재개 프롬프트.

## 2. 근거와 충돌 처리

공식 미션 M은 최종 통과의 최소조건이다. **이번에 새로 첨부된 S01~S11이 이전 패키지와 이전 대화의 임의 설계보다 우선**한다. 역할·보안·코딩 규칙은 S03, 외부 API의 필드·상태코드는 S07, 모델 클래스/필드와 기본 검증은 S06, DB는 S01, 의존성은 S02, 설정명은 S04를 각각 기준으로 삼는다.

S06의 기본 검증이 S07의 상태코드와 다른 경우처럼 첨부자료끼리도 충돌할 수 있다. 해당 부분은 `PROJECT_PLAN.md` C 결정표의 **명시적 조정**을 적용한다. 이를 팀이 승인했다고 꾸미지 않는다. 새로운 충돌은 영향과 선택을 `docs/IMPLEMENTATION_STATUS.md`에 남긴다. 공식 조건·팀 계약을 없애서 테스트를 통과시키지 않는다.

이전 패키지의 `email`, 채팅 `message/reply`, 채팅 성공의 `chat_id/ai_mode`, 중복가입 409, 토큰 60분, `youthbot.db`, PyJWT, 동기 sqlite3 중심 설계는 사용하지 않는다. 최신의 `username`, `question`, `answer/latency_ms`, `hashed_password`, `data/chatbot.db`, `python-jose`, `aiosqlite`, 1440분을 따른다.

## 3. 최소 범위 및 실행 원칙

첫 목표는 예쁜 완제품이 아니라 **실제 인증·실제 DB를 거치는 최소 브라우저 E2E**다. Mock은 개발 보조이며 실제 AI·외부 URL·팀 협업 요건을 대신하지 않는다. 로컬 필수기능 이후 실제 AI, 외부배포, 팀 이력 검증을 별도 상태로 보고한다.

FastAPI, Uvicorn, Pydantic v2, pydantic-settings, httpx, python-jose, passlib/bcrypt, aiosqlite, Vanilla HTML/CSS/JS를 사용한다. S02의 패키지를 임의로 다른 스택으로 바꾸지 않는다. 버전 호환성은 실제 설치·테스트한 뒤 constraints/lock에 기록한다. SQLAlchemy, PyJWT, 이메일 검증 패키지, React, LangChain, RAG, 공공데이터, 결제, 다중 채팅방, SSE/WebSocket을 새로 추가하지 않는다.

직접 작성하는 주석·docstring은 한국어, 식별자와 JSON 키는 원래 영어를 유지한다. 원자료의 영어 주석 제목은 코드 생성 시 한국어로 정리할 수 있으나 기능·필드명은 바꾸지 않는다. UTF-8 without BOM, LF를 사용한다. 경로 표시는 `/`를 사용하며 문자열의 역슬래시를 실제 제어문자로 잘못 변환하지 않는다. raw string은 필요한 곳에만 사용한다.

## 4. 인터페이스에서 바꾸지 않을 것

- 가입: `POST /api/auth/register`, `username/password`, 201과 `message/username`, 중복 400.
- 로그인: `POST /api/auth/login`, JSON `username/password`, `access_token/token_type`.
- 채팅: `POST /api/chat`, `question`, 성공 `answer/latency_ms`만 반환.
- 기록: `GET /api/me/chats`, `ChatLogItem`의 **배열**. 임의 `{chats: [...]}` 포장 금지.
- 헬스: `GET /api/health`, `{"status":"ok"}`. 추가 상태를 body에 넣지 않는다.
- 보호 API: `Authorization: Bearer <access_token>`; 미인증·잘못된/만료 토큰 401.
- 오류 JSON: 항상 `{"detail":"한국어 문자열"}`. Pydantic의 배열이나 입력 원문/비밀번호를 노출하지 않는다.
- 팀 계약에 따라 AI 시간초과 및 호출 실패는 504. 내부 로그에서 원인을 구분한다. 공급자 401을 사용자의 로그인 401로 전달하지 않는다.
- 질문 빈 문자열·공백만 400, 500자 초과/잘못된 자료형 422. 상세 경계는 C02/C03과 구현 명세를 따른다.

## 5. 보안·데이터·배포 규칙

`.env`, API 키, JWT 서명키, 실제 DB·WAL·SHM·로그·백업은 커밋하지 않는다. 환경변수 이름 `CODESSEY_`의 기존 철자를 유지한다. 예시 키를 진짜 비밀값으로 사용하거나 시작 때마다 서명키를 재생성하지 않는다.

회원가입 비밀번호 4~100자 계약과 bcrypt의 바이트 한계가 충돌하므로 C06의 명시적 bcrypt 기반 해시 선택을 적용한다. 조용히 자르거나 원문/SHA256만 저장하지 않는다. `get_current_user`는 서명·만료·사용자 존재를 확인한다. 사용자 식별은 서버가 확인한 JWT에서만 얻는다.

localStorage 방식은 팀 규격을 유지한다. 입력/AI 응답은 `textContent`로 표시하고 비밀번호는 브라우저 저장소에 넣지 않는다. 로그아웃 후 이전 사용자의 지연 응답을 새 사용자 화면에 표시하지 않는다.

DB는 `aiosqlite`와 WAL, 사용자별 조회를 사용하고 AI 대기 중 쓰기 트랜잭션을 잡지 않는다. 성공 답변은 DB commit 뒤 200을 반환한다. AI 실패는 운영 로그에, 저장 실패는 `db_save_failed`에 남긴다. `scripts/check_logs.sql`은 대화 DB 확인용이다.

기본 AI 제한 8.0초와 최근 5쌍(팀 범위 3~5쌍)을 유지한다. 키가 없을 때 개발용 Mock을 허용하되 명확히 표시한다. 잘못된 실키/AI 장애를 Mock 성공으로 바꾸지 않는다. 배포 운영모드는 키 없으면 실패로 보고한다.

AWS EC2/Ubuntu 22.04/Nginx/systemd, 내부 8000, SSH 팀원 IP 제한, **팀이 지정한 2GB Swap 구성**을 보존한다. Swap이 OOM을 보장 예방한다거나 t2.micro가 이 사용자의 계정에서 무료라고 주장하지 않는다. HTTPS/80번만 공개 및 시스템 절대경로 충돌은 C10/C11에 명시했다. 팀 규칙을 몰래 바꾸지 말고 해당 배포 승인 여부를 별도 기록한다.

## 6. Git — 실제 작업에 따라 커밋을 남긴다

현재 사용자만의 `feat/fullstack-lee`에서 작은 기능 단위로 구현·검증·커밋한다. 사용자가 `CODEX_START.md`의 시작 프롬프트로 승인한 경우 **실제 본인 작성자 정보로 로컬 커밋을 허용**한다. 이름·이메일이 없으면 추측하지 말고 커밋만 대기 상태로 둔다. `--author`로 다른 팀원을 흉내 내지 않는다. 공용 PC 전역 설정은 바꾸지 않는다.

빈 저장소에 첫 추적 커밋이 필요하면 이 문서 패키지/ignore/템플릿의 실제 변경을 기능 브랜치에서 기록하고, 이후 팀 운영은 feature → develop → main의 PR 방식으로 한다. main에 구현을 직접 커밋하지 않는다. 기존 저장소의 원격·브랜치 규칙을 덮어쓰지 않는다.

본인 로컬 20개 계획은 팀 전체 10개×4명의 대체물이 아니다. 개인 저장소의 커밋이 평가 팀 저장소에 자동 산입되는 것도 아니다. 기여자의 실제 SHA·PR·검증·최종 브랜치 포함 여부를 확인한다. 빈 커밋, 공백만 변경, 완료 코드의 인위적 소급 분할, 가짜 공동작성은 금지한다.

원격 push·PR 생성/승인/merge, force push, 타인의 브랜치 수정은 별도 승인 없이는 하지 않는다. PR 초안과 명령 안내는 작성한다. 최소 10회 조건이 있는 이번 과제의 보수적 운영안은 원커밋이 남는 **Create a merge commit**이며, 팀 설정과 충돌하면 먼저 합의해야 한다.

## 7. 완료·검증 보고

파일 생성만으로 완료 선언하지 않는다. `docs/IMPLEMENTATION_STATUS.md`에 M01~M21, 실제 명령·버전·실패·미실행·외부조건을 기록한다. 상태는 `PASS / FAIL / NOT_RUN / BLOCKED_EXTERNAL / NEEDS_TEAM_REVIEW`다.

`LOCAL_MINIMUM`, `REAL_AI`, `PUBLIC_URL`, `TEAM_HISTORY`를 나눠 적는다. `.env`가 존재하거나 배포 템플릿이 있다는 이유로 뒤의 세 항목을 PASS로 하지 않는다. 실제 결제·유료 호출·AWS 생성·외부 공개는 별도 승인을 받는다. 막힌 항목 외의 로컬 개발은 계속하되, 미션 전체 통과로 보고하지 않는다.

아래 S03은 최신 첨부 조직 규칙을 원문 보존한 것이다. 충돌된 부분은 앞의 적용 규칙과 C 결정표로 추적한다. 다른 조직에 본 파일을 자동 적용하는 권한은 없다.

## 원자료 S03 — `AGENTS(2).md`

원래 배치 대상: `AGENTS.md`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S03 -->
````markdown
# B7-1 AI 챗봇 개발 가이드라인 (AGENTS.md)

본 문서는 프로젝트 개발 시 모든 팀원(고준석, 박범규, 이준혁, 차종민)과 AI 에이전트가 영구적으로 준수해야 하는 공통 협업 및 기술 규칙입니다.

---

## 1. 프로젝트 기본 정보
- **서비스명**: AI Assistant (7-1 웹 기반 AI 챗봇)
- **프로젝트 목표**: 4일 내 핵심 컴포넌트(웹 UI ↔ 로그인/인증 ↔ FastAPI 백엔드 ↔ 코디세이 AI API ↔ SQLite DB ↔ AWS EC2 배포)가 100% 결합된 동작 가능한 프로토타입(MVP) 완성
- **개발 환경**: Python 3.10+, FastAPI, SQLite, Vanilla HTML/CSS/JavaScript
- **AI 연동**: 코디세이 AI API (GPT-4o-mini / Claude 3.5 Sonnet 호환 엔드포인트) + Mock AI Fallback 지원
- **배포 인프라**: AWS EC2 프리티어 (t2.micro / Ubuntu 22.04 LTS), 2GB Swap 메모리, Nginx 리버스 프록시, Systemd 데몬

---

## 2. 팀원 4인 역할 분담 (R&R)

| 팀원 | 담당 영역 | 세부 업무 내용 |
| :--- | :--- | :--- |
| **고준석**<br>(팀장) | **로그인 & 인증 (Auth)** | • 회원가입 API (POST /api/auth/register) 및 로그인 API (POST /api/auth/login)<br>• 비밀번호 bcrypt 해싱 및 JWT 토큰 발급/검증 유틸리티<br>• 미인증 사용자 401 차단용 FastAPI 의존성(get_current_user) 구현<br>• 전체 일정 관리 및 마일스톤 조율 (PM) |
| **박범규** | **백엔드 코어 & DB** | • FastAPI 메인 애플리케이션 진입점 및 라우터 통합 (app/main.py)<br>• SQLite DB 연결 및 테이블 스키마 (users, chat_logs)<br>• 대화 로그 저장 함수 및 내 대화 조회 API (GET /api/me/chats)<br>• 과제 필수 표준 4대 이벤트 로깅 모듈 및 scripts/check_logs.sql 작성 |
| **이준혁** | **프론트엔드 UI/UX** | • 반응형 단일 페이지 웹 챗봇 인터페이스 (static/index.html, style.css)<br>• 로그인 / 회원가입 모달 UI 및 JWT 로컬 스토리지 보관 처리 (auth.js)<br>• 실시간 질문 입력, 로딩 인디케이터, AI 응답 렌더링 스크립트 (app.js)<br>• 에러 알림 토스트 및 모바일/데스크탑 반응형 레이아웃 구성 |
| **차종민** | **AI 파이프라인** | • 코디세이 AI API 연동 모듈 (app/ai_service.py) 구축<br>• 최근 대화 3~5쌍을 조합하는 슬라이딩 윈도우 문맥(Context) 유지 전략 구현<br>• 8.0초 타임아웃 예외 핸들링 및 서버 프로세스 다운 방지 로직<br>• 키 미설정 및 테스트용 내장 Mock AI 엔진 구현 |

---

## 3. 4일 프로토타입 완성 마일스톤

- **Day 1 (독립 모듈 세팅 & AI PoC)**:
  - 브랜치 생성 (feat/auth-ko, feat/backend-park, feat/ui-lee, feat/ai-cha)
  - [차종민] 코디세이 AI API 단독 호출 PoC 스크립트 작성 및 8초 타임아웃 검증
  - [고준석] bcrypt 암호화 및 JWT 토큰 생성 유틸 함수 작성
  - [박범규] FastAPI 기본 서버 세팅 및 SQLite 스키마(users, chat_logs) 생성
  - [이준혁] 반응형 채팅 웹 UI HTML/CSS 와이어프레임 작성
- **Day 2 (코어 로직 & API 완성)**:
  - [고준석] 회원가입/로그인 엔드포인트 및 get_current_user 의존성 완성
  - [박범규] 대화 로그 DB 저장 함수, GET /api/me/chats 구현, 표준 4대 로깅 세팅
  - [이준혁] 로그인/회원가입 모달 완성, 토큰 저장 및 백엔드 비동기 통신 연동
  - [차종민] 슬라이딩 윈도우 문맥 조립, 8초 타임아웃 방어, Mock AI 모드 구현
- **Day 3 (전체 E2E 결합 - Alpha Release)**:
  - 인증 미들웨어 + 채팅 라우터 결합
  - UI에서 질문 입력 시 토큰 검증 -> 백엔드 수신 -> AI 호출 -> DB 저장 -> 화면 출력 전체 파이프라인 1차 통합
  - 통합 PR 생성 및 코드 리뷰 후 develop 브랜치 머지
- **Day 4 (안정성 강화 & 프로토타입 시연 검증)**:
  - 비정상 입력(공백, 500자 초과) 유효성 검사 차단
  - 타임아웃/API 에러 시 사용자 친절 안내(504) 연동
  - scripts/check_logs.sql로 SQLite 로그 검증
  - AWS EC2 프리티어 인프라 세팅(Nginx, Swap 2GB, Systemd) 및 외부 접속 시연 점검

---

## 4. 코드 및 주석 작성 규칙 (Self-Audit Guardrail)

1. **언어 규칙**:
   - 코드 docstring 및 모든 주석은 **100% 한국어**로 작성합니다. (영문 docstring 금지)
   - 변수명, 함수명, 클래스명은 명확한 표준 영어(snake_case, PascalCase)를 사용합니다.
2. **경로 표기 최우선 규칙**:
   - 문서, 코드, 산출물 내 경로 표기 시 절대 경로(file:///...)를 엄격히 금지하며, 항상 **상대 경로(예: B7-1/7-1/app/...)**로만 작성합니다.
3. **간결성 원칙 (Simplicity First)**:
   - 불필요하게 무거운 외부 프레임워크(LangChain 등)를 배제하고, FastAPI + httpx + SQLite + 바닐라 JS 기반의 직관적인 코드를 유지합니다.
4. **인코딩 및 제어문자 오염 방지 규칙**:
   - 모든 파일은 UTF-8(Without BOM)로 저장합니다.
   - 역슬래시(`\`)와 영문자가 결합되어 의도치 않은 ASCII 제어문자(`\a`, `\b`, `\f`, `\t`, `\r`)로 변환되지 않도록 경로 표기 시 항상 슬래시(`/`)를 사용하고, 스크립트 작성 시 Raw String(`r"..."`)을 사용합니다.

---

## 5. 보안 및 설정 가드레일 (Security First)

1. **민감 정보 절대 노출 금지**:
   - 코디세이 AI API Key, JWT Secret Key, DB 파일 등 모든 민감 정보는 소스코드에 하드코딩하지 않습니다.
   - 반드시 .env 파일과 환경 변수를 사용하며, .gitignore에 .env 및 *.db를 반드시 등록합니다.
   - 공개 저장소에는 .env.example만 제공합니다.
2. **AWS EC2 프리티어 인프라 보안**:
   - 보안 그룹 인바운드 규칙: SSH(22)는 팀원 IP 한정, HTTP(80)만 전체 오픈합니다.
   - FastAPI 포트(8000)를 외부에 직접 개방하지 않고, 앞단의 Nginx 리버스 프록시를 통해서만 전달합니다.
   - 메모리 1GB의 t2.micro 특성상 OOM 크래시를 방지하기 위해 **반드시 2GB Swap 파티션**을 구성합니다.
3. **비밀번호 단방향 암호화**:
   - 사용자 비밀번호는 절대 평문으로 저장하지 않고 bcrypt로 솔팅 및 해싱하여 저장합니다.
4. **엔드포인트 접근 제어**:
   - 챗봇 질의응답(POST /api/chat) 및 로그 조회(GET /api/me/chats)는 반드시 유효한 JWT 토큰이 검증된 로그인 사용자만 접근할 수 있도록 401 Unauthorized를 반환합니다.

---

## 6. 표준 로깅 규격 (과제 필수 요구사항 5항)

서버 로그는 Python 표준 logging 모듈을 사용하며, 아래 4대 핵심 이벤트 규격 포맷을 반드시 준수합니다:
```text
INFO request_received user_id={user_id} path={path}
INFO ai_call_start user_id={user_id} request_id={request_id}
INFO ai_call_success request_id={request_id} latency_ms={latency_ms}
INFO db_save_success user_id={user_id} chat_id={chat_id}
ERROR ai_call_failed request_id={request_id} error={error_detail}
ERROR db_save_failed user_id={user_id} error={error_detail}
```

---

## 7. 예외 처리 및 안정성 규칙

1. **AI API 호출 타임아웃**:
   - 코디세이 AI 호출 시 timeout=8.0초를 설정하여 무한 대기를 방지합니다.
   - 타임아웃 또는 API 에러 발생 시 FastAPI 프로세스가 다운되지 않고, 사용자에게 504 Gateway Timeout과 친절한 오류 안내(현재 AI 응답이 지연되고 있습니다. 잠시 후 다시 시도해 주세요.)를 반환합니다.
2. **사용자 입력 검증**:
   - 빈 문자열 또는 공백만 있는 질문 차단 (400 Bad Request).
   - 최대 500자 길이 초과 질문 차단 (422 Unprocessable Entity).

---

## 8. Git 협업 및 커밋 컨벤션

1. **브랜치 전략**:
   - main: 배포용 프로덕션 브랜치 (직접 푸시 금지, PR 필수)
   - develop: 개발 통합 브랜치
   - feat/{기능명}-{이름}: 개인 작업 브랜치 (예: feat/auth-ko, feat/backend-park, feat/ui-lee, feat/ai-cha)
2. **커밋 메시지 형식**:
   - feat: 새로운 기능 구현
   - fix: 버그 수정
   - docs: 문서 작성 및 수정
   - style: 코드 포맷팅 및 주석 정리
   - refactor: 비즈니스 로직 리팩토링
   - test: 테스트 코드 및 검증 스크립트 추가
3. **팀원별 10회 커밋 룰**:
   - 전 팀원(4명)은 구현, 테스트, 리팩토링, 문서화를 작은 단위로 나누어 **최소 10회 이상의 유의미한 커밋**을 반드시 기록합니다.
````
<!-- SOURCE_END:S03 -->
