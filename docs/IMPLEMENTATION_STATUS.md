# 구현 및 미션 검증 상태

최종 갱신: 2026-09-16 / R11 API 오류·세션 만료 검증

## 네 가지 완료 축

| 축 | 상태 | 현재 근거 / 다음 조건 |
|---|---|---|
| LOCAL_MINIMUM | NOT_RUN | 코드·의존성·로컬 E2E 구현 전 |
| REAL_AI | BLOCKED_EXTERNAL | 실제 코디세이 공급자 URL·모델·키·사용 권한·유료 호출 승인 필요 |
| PUBLIC_URL | BLOCKED_EXTERNAL | AWS 계정·리전·비용·보안그룹·TLS/HTTP 위험·외부 공개 승인 필요 |
| TEAM_HISTORY | NEEDS_TEAM_REVIEW | 평가 저장소의 팀원별 SHA·PR·최종 브랜치 범위 미확인 |

## 현재 환경과 Git

- 저장소 성격: 팀 Organization과 별개인 개인 풀스택 기준 구현
- 기준 SHA: `6b2ff28ab3947884b5ffe6f54f3bf28b60107d42`
- 작업 브랜치: `feat/fullstack-lee`
- 작성자: `Cerhovah <ljh951206@gmail.com>`
- 원격: `origin` 개인 저장소; push/PR/merge 미실행
- 입력 명세: 루트 2개와 docs 4개를 끝까지 검토
- 적용 결정: C01~C24, D01~D06; 특히 C06/C10/C11/C13은 팀/외부 확인이 남음

## M01~M21 추적표

| ID | 요구사항 | 상태 | 실제 증거 / 대기 조건 |
|---|---|---|---|
| M01 | 같은 화면 질문·응답 | PASS | 로컬 브라우저에서 질문과 Mock 답변·latency를 같은 화면에 렌더링 |
| M02 | 회원가입·로그인 | PASS | 임시 DB에서 실제 사용자 가입 201·로그인 200·해시/JWT 검증 |
| M03 | 인증별 접근제어 | PASS | 실제 `/api/chat`, `/api/me/chats`의 누락·변조·만료·삭제 사용자 401과 인증 우선순위 검증 |
| M04 | 실제 AI API 호출 | NOT_RUN | 외부 조건은 상단 REAL_AI에 별도 기록; 공급자·키·호출 승인 필요 |
| M05 | 최근 사용자 문맥 | PASS | 같은 사용자의 최근 5쌍·시간순 12 messages와 두 턴 Mock 확인 |
| M06 | 대화 DB 누적·영속 | PASS | commit 뒤 200, 앱 수명주기 재시작 뒤 기록 보존 검증 |
| M07 | 사용자별 기록 조회 | PASS | 인증 사용자 배열·id 오름차순·A/B 격리 검증 |
| M08 | 요청·AI·DB 성공/실패 로그 | PASS | 6개 이벤트의 성공·AI 실패·DB 실패 실제 경로와 비밀 비노출 검증 |
| M09 | AI 실패/timeout 복구 | PASS | 주입한 timeout/호출 실패 504 뒤 같은 프로세스 정상 요청 성공 |
| M10 | 입력 검증 | PASS | 공백 400, 원문 501자·padded 502자 422, Unicode 500자 검증 |
| M11 | 외부 URL | NOT_RUN | 외부 조건은 상단 PUBLIC_URL에 별도 기록; 배포·공개 승인 필요 |
| M12 | 필수 기술 문서 | NOT_RUN | 초기 문서만 존재; 실제 결과 반영 필요 |
| M13 | 비밀값 환경변수·Git 제외 | NOT_RUN | ignore 정적 확인과 추적 검사 예정 |
| M14 | 브랜치 전략·작업 흔적 | PASS | `feat/fullstack-lee`에서 기준 SHA 이후 본인 명의 기능 커밋 10개 확인 |
| M15 | 실제 PR merge | NOT_RUN | 원격 작업 별도 승인 필요 |
| M16 | 팀원별 유의미한 커밋 10개 | NOT_RUN | 팀 평가 저장소 이력 미확인 |
| M17 | 역할·이력 일치 | NOT_RUN | 실제 팀 SHA/PR 미확인 |
| M18 | Python/FastAPI/SQLite | PASS | Python 3.12.14 가상환경, FastAPI 0.141.1, aiosqlite 0.22.1 실제 테스트 |
| M19 | GitHub 저장소 링크 | NOT_RUN | 원격 주소 확인, 제출 대상 확인 필요 |
| M20 | DB 확인 가이드 | NOT_RUN | 도구 구현 전 |
| M21 | 여섯 흐름 개인 설명 | NOT_RUN | 실제 구현·직접 확인 후 작성 |

## T01~T33 테스트 추적표

아래 상태는 테스트 파일 존재가 아니라 실제 실행 결과를 뜻합니다.

| ID | 상태 | 비고 |
|---|---|---|
| T01 | PASS | 로컬 Uvicorn에서 `/`, CSS·JS·health 200과 브라우저 로드 확인 |
| T02 | PASS | 가입 201과 중복 400 응답·DB 저장 검증 |
| T03 | PASS | 공백/2자/51자/trim/내부공백·대소문자 보존 검증 |
| T04 | PASS | 3/4/100/101자·공백·100자 한글 경계 검증 |
| T05 | PASS | 100자 ASCII·한글과 72바이트 이후 차이 검증 |
| T06 | PASS | JSON 로그인 성공·동일 401·공백 422·form 거부·긴 입력 우회 검증 |
| T07 | PASS | HS256, sub/iat/exp, 1440분, 위조·만료·타알고리즘·없는 사용자 401 |
| T08 | PASS | 실제 chat/history 인증 누락·변조·만료·body 오류 우선순위 |
| T09 | PASS | register/chat 구형 키 422, 로그인 form 거부, JSON 계약 검증 |
| T10 | PASS | Mock 200의 정확한 body 타입과 실제 DB 저장 |
| T11 | PASS | 빈/공백/500/501/padded502/emoji 경계 |
| T12 | PASS | 누락/null/숫자/배열/잘못된 JSON의 문자열 detail |
| T13 | PASS | history 배열·빈값·id 정렬·정확한 필드·UTC 형식 |
| T14 | PASS | A/B 기록·문맥 격리와 body user_id 무시 |
| T15 | PASS | 앱 재시작 뒤 사용자·대화 보존 |
| T16 | PASS | 최신 5쌍과 현재 질문의 12 messages 순서 |
| T17 | NOT_RUN | 실제 adapter 가짜 transport |
| T18 | NOT_RUN | timeout·복구 |
| T19 | NOT_RUN | 공급자·응답 실패 |
| T20 | NOT_RUN | DB 실패·rollback |
| T21 | PASS | 성공 4개+AI/DB 실패 2개 이벤트와 토큰·암호·질문 비노출 |
| T22 | PASS | ignore 15/15과 `/.env`·DB·로그·Git·README HTTP 404 검증 |
| T23 | NOT_RUN | AI 모드 판정 |
| T24 | NOT_RUN | OpenAPI·문서·스키마 |
| T25 | NOT_RUN | 브라우저 핵심 E2E |
| T26 | NOT_RUN | 브라우저 오류·로딩 복구 |
| T27 | NOT_RUN | 늦은 응답 사용자 격리 |
| T28 | NOT_RUN | XSS·모바일·키보드·IME |
| T29 | NOT_RUN | SQL 확인 도구 |
| T30 | NOT_RUN | 새 가상환경 재현 |
| T31 | BLOCKED_EXTERNAL | 승인된 실제 AI 두 턴 필요 |
| T32 | BLOCKED_EXTERNAL | 승인된 외부 배포 필요 |
| T33 | NEEDS_TEAM_REVIEW | 실제 팀 PR·기여 이력 필요 |

## 외부 입력 및 합의 대기

- C06: `bcrypt_sha256` 포맷을 팀 인증 담당과 합의해야 하며 개인 신규 DB에서 먼저 검증합니다.
- C10: systemd의 필수 절대 경로와 앱 문서 상대 경로 규칙의 팀 해석이 필요합니다.
- C11: 원안 HTTP 80과 인터넷 로그인/JWT의 위험 때문에 HTTPS/443 변경 여부 승인이 필요합니다.
- C13/C15: AWS 비용 조건과 실제 코디세이 URL·모델·권한이 확인되지 않았습니다.
- 원격 push·PR·merge, 실제 유료 AI, AWS 변경, 외부 공개는 실행하지 않았습니다.

## 실행 기록

| 시각/단계 | 실제 명령 | 결과 |
|---|---|---|
| R01 | `git status --short --branch`, author/remote/log 확인 | clean main, 기준 SHA와 작성자·개인 원격 확인 |
| R01 | `git switch -c feat/fullstack-lee` | 로컬 기능 브랜치 생성 성공 |
| R01 | S01~S11 정규화 본문 SHA-256 재계산 | PROJECT_PLAN에 기록된 해시와 11/11 일치 |
| R01 | 원문 복원 규칙 독립 재감사 | S02/S04/S05/S06/S07/S09~S11 누락·재작성 문제를 발견해 별도 수정 |
| R02 | 시스템 `python --version`, `python -m venv .venv` | Windows Store 별칭만 있어 실패; 전역 설치는 하지 않음 |
| R02 | 작업공간 Python 3.12.14로 `.venv` 생성·requirements 설치·`pip check` | 설치 성공, broken requirements 없음 |
| R02 | 최신 bcrypt 5.0.0 해시 smoke | Passlib backend의 72바이트 탐지 단계에서 실패; 호환 조합 검증 필요 확인 |
| R02 | bcrypt 4.0.1 재설치 후 bcrypt_sha256 smoke | 4자·100자 ASCII·100자 한글·72바이트 이후 차이 모두 PASS |
| R02 | `.venv/Scripts/python.exe -m pytest tests/test_bootstrap.py -q` | 8 passed, dependency deprecation warning 2건 |
| R03 | `.venv/Scripts/python.exe -m pytest tests/test_auth.py -q` | 22 passed, dependency deprecation warning 2건 |
| R03 보강 | 전체 `.venv/Scripts/python.exe -m pytest -q` | 34 passed; 손상 해시·트랜잭션·404/405 한국어 오류 회귀 포함 |
| R04 | `.venv/Scripts/python.exe -m pytest tests/test_login_auth.py tests/test_auth.py -q` | 47 passed, dependency deprecation warning 2건 |
| R05 | `.venv/Scripts/python.exe -m pytest -q` | 93 passed, Mock·문맥·기록·복구·인증 우선순위·동시 turn 직렬화·UTF-8/OpenAPI health 포함 |
| R05 | constraints의 `Requires-Python`을 Python 3.10.0 기준 전수 검사 | websockets 17.1만 3.11+ 충돌 확인; 15.0.1(3.9+)로 교체 후 `pip check` PASS |
| R06 | `.venv/Scripts/python.exe -m pytest tests/test_frontend_contract.py tests/test_bootstrap.py -q` | 17 passed; `/`·CSS 제공, 정적 DOM·비노출 경계 검증 |
| R06 | 전체 `.venv/Scripts/python.exe -m pytest -q` | 101 passed, dependency deprecation warning 2건 |
| R07 | Node ESM `--check`로 `static/js/api.js`, `static/js/auth.js` 검사 | 두 파일 모두 구문 검사 PASS |
| R07 | `.venv/Scripts/python.exe -m pytest tests/test_frontend_contract.py -q` | 14 passed; 로그인 계약·fetch 중앙화·토큰 저장·선택 헤더 비의존·취소 요청 무효화 검증 |
| R07 | 전체 `.venv/Scripts/python.exe -m pytest -q` | 107 passed, dependency deprecation warning 2건 |
| R08 | Node ESM `--check`로 `static/js/api.js`, `static/js/auth.js` 검사 | 두 파일 모두 구문 검사 PASS |
| R08 | `.venv/Scripts/python.exe -m pytest tests/test_frontend_contract.py tests/test_auth.py -q` | 44 passed; 가입 201/400/422 서버 계약·UI 연결·취소 오류 격리 검증 |
| R08 | 전체 `.venv/Scripts/python.exe -m pytest -q` | 111 passed, dependency deprecation warning 2건 |
| R09 | Node ESM `--check`로 `static/js/api.js`, `static/js/auth.js`, `static/js/app.js` 검사 | 세 파일 모두 구문 검사 PASS |
| R09 | `.venv/Scripts/python.exe -m pytest tests/test_frontend_contract.py tests/test_chat.py -q` | 59 passed; chat 필드·Unicode 길이·textContent·세션 응답 격리 검증 |
| R09 | 숨은 로컬 브라우저에서 가입 → 로그인 → 질문 → Mock 답변 | 201 → 200 → 200; 같은 화면 질문/답변·0 ms 표시, 브라우저 warning/error 0건 |
| R09 | `data/browser_e2e.db`와 `logs/app.log` 교차 확인 | 사용자 1명·대화 1행, request/AI start/AI success/DB save 이벤트 확인 |
| R09 | 전체 `.venv/Scripts/python.exe -m pytest -q` | 115 passed, dependency deprecation warning 2건 |
| R10 | Node ESM `--check`로 `static/js/api.js`, `static/js/app.js` 검사 | 두 파일 모두 구문 검사 PASS |
| R10 | `.venv/Scripts/python.exe -m pytest tests/test_frontend_contract.py tests/test_chat.py -q` | 62 passed; 배열·response·필드 타입·history 세션 격리 검증 |
| R10 | 기존 토큰으로 브라우저 새로고침, 로그아웃 후 재로그인 | 같은 DB의 질문·response·latency 복원, 로그아웃 즉시 화면 제거, console warning/error 0건 |
| R10 | 신규 `browser_empty_r10` 계정 로그인과 DB 교차 확인 | 빈 배열 화면 유지; 기존 사용자 1행, 신규 사용자 0행으로 격리 확인 |
| R10 | 전체 `.venv/Scripts/python.exe -m pytest -q` | 118 passed, dependency deprecation warning 2건 |
| R11 | Node `--test tests/frontend/api.test.mjs` | 10 passed; 400/422/500/504·비JSON·빈/객체 detail·본문 읽기·네트워크·무재시도 검증 |
| R11 | `.venv/Scripts/python.exe -m pytest tests/test_frontend_contract.py -q` | 26 passed; 보호 API 401과 로그인 401 경계·stale guard 순서 검증 |
| R11 | 로컬 JWT 서명키 교체 뒤 저장 토큰으로 브라우저 새로고침 | history 401 뒤 토큰 null·대화 초기화·만료 안내 로그인 모달 확인 |
| R11 | 같은 모달에서 잘못된 비밀번호 로그인 | 로그인 401 detail만 폼에 표시, 재호출 루프·자동 로그인 없음 |
| R11 | 전체 `.venv/Scripts/python.exe -m pytest -q` | 119 passed, dependency deprecation warning 2건 |
