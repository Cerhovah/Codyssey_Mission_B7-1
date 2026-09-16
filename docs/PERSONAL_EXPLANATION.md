# 여섯 흐름 직접 설명용 초안

이 문서는 개인 풀스택 구현을 본인이 검토하고 직접 설명하기 위한 초안입니다. AI가 정리한 문장을 그대로 읽었다는 사실만으로 M21을 PASS 처리하지 않습니다. 실제 코드와 실행 결과를 열어 보고, 아래 여섯 흐름을 자신의 말로 설명한 뒤 팀 증빙에 확인을 남겨야 합니다.

## 1. 브라우저 화면에서 API까지

`app/main.py`는 FastAPI 수명주기에서 설정·SQLite·AI HTTP client를 준비하고, `/`에서는 `static/index.html`, `/static/`에서는 정적 자원만 제공합니다. 브라우저의 모든 서버 호출은 `static/js/api.js`에 모여 있고 같은 origin의 `/api/...` 상대 경로를 사용합니다. 그래서 프론트 파일은 Python 모듈이나 `.env`를 직접 읽지 않으며, 나중에 `static/`만 옮길 때도 API base 경계만 팀 서버 조건에 맞추면 됩니다.

직접 설명할 핵심은 “화면이 서버 템플릿 없이 어떻게 열리는가”, “왜 API 호출을 api.js 한 곳에 모았는가”, “선택 헤더 `X-AI-Mode`가 없어도 왜 로그인·채팅·기록이 동작하는가”입니다.

## 2. 가입·로그인과 JWT 접근 제어

가입은 `app/routers/auth_router.py`가 입력을 검증하고 `app/auth.py`의 `bcrypt_sha256` 해시를 거쳐 사용자를 저장합니다. 로그인은 해시를 확인한 뒤 `sub`, `iat`, `exp`가 있는 HS256 JWT를 발급합니다. 보호 API의 `get_current_user`는 Bearer 토큰의 서명·알고리즘·만료·필수 claim을 확인할 뿐 아니라 `sub` 사용자가 DB에 실제 존재하는지도 다시 조회합니다.

JWT가 필요한 이유는 클라이언트가 body의 `user_id`를 주장하지 못하게 하고 서버가 인증된 사용자를 결정하기 위해서입니다. 다만 브라우저 localStorage 토큰 삭제는 서버 측 즉시 폐기가 아니므로, 복사된 토큰을 무효화하는 refresh/denylist 기능은 현재 범위 밖이라는 한계도 함께 설명해야 합니다.

## 3. 질문에서 답변 commit까지

`app/routers/chat_router.py`의 채팅 경로는 인증 사용자 → 질문 검증 → 같은 사용자의 최근 5쌍 조회 → messages 조립 → Mock 또는 real AI 호출 → SQLite 저장과 commit → `answer/latency_ms` 응답 순서입니다. 성공 답변은 DB commit 뒤에만 200으로 반환합니다. 같은 사용자의 동시 요청은 프로세스 내부 turn lock으로 직렬화하지만, 다른 사용자의 요청은 서로 막지 않습니다.

AI를 기다리는 동안 DB 쓰기 트랜잭션을 열지 않는 이유, 최근 5쌍이 system 1개+과거 10개+현재 질문 1개의 순서가 되는 이유, 다중 worker에서는 프로세스 내부 lock만으로 전체 순서를 보장하지 못하는 이유를 코드와 함께 설명합니다.

## 4. 사용자 격리와 영속 기록

`app/database.py`의 최근 기록과 전체 기록 쿼리는 모두 `WHERE user_id = ?`에 서버가 확인한 사용자 ID를 바인딩합니다. 다른 사용자의 ID를 URL이나 body로 받지 않습니다. `chat_logs`에는 질문·응답·지연시간·생성시각이 누적되고, 앱 재시작 때 `CREATE TABLE IF NOT EXISTS`를 사용하므로 기존 행을 초기화하지 않습니다. WAL과 사용자/id 인덱스는 SQLite 접근을 보완합니다.

직접 설명할 때는 A/B 사용자 테스트, 기록 API의 id 오름차순, 문맥 조회의 최신 5쌍 후 시간순 복원, `scripts/check_db.py`의 읽기 전용 사용자 필터를 연결해 보여 줍니다.

## 5. 8초 제한·실패 복구·운영 로그

`app/ai_service.py`의 real 경로는 HTTPS provider URL과 Bearer/model/messages 계약을 사용하고, HTTPX 단계별 timeout과 전체 await 제한을 함께 둡니다. timeout·네트워크·공급자 401/429/500·비JSON·빈 응답은 사용자에게 504 문자열 detail로 정규화하며 Mock 성공으로 바꾸거나 자동 재시도하지 않습니다. DB INSERT/commit 실패는 rollback 뒤 500이고 성공 행을 남기지 않습니다.

`app/logger.py`는 `request_received`, `ai_call_start`, `ai_call_success`, `ai_call_failed`, `db_save_success`, `db_save_failed`를 stdout과 파일에 기록하고 AI 시작·성공에는 `mode=mock|real`을 남깁니다. 질문·답변 원문, JWT, 비밀번호, API 키는 운영 로그에 넣지 않습니다. AI 실패 뒤 다음 요청과 DB 실패 뒤 다음 저장이 정상 복구되는 테스트를 함께 설명합니다.

## 6. Git·검증·외부 완료 조건

개인 작업은 기준 SHA `6b2ff28ab3947884b5ffe6f54f3bf28b60107d42`에서 `feat/fullstack-lee`로 분기해 실제 작성자 `Cerhovah <ljh951206@gmail.com>`의 기능 단위 커밋으로 남겼습니다. `scripts/audit_contributions.py`는 명시한 base..ref의 non-merge 커밋만 정확한 이메일로 집계하고, 빈 diff를 후보 수에서 제외합니다. 개수가 10 이상이어도 의미성과 PR을 자동 PASS 처리하지 않습니다.

로컬 기능·테스트가 통과한 것과 실제 AI, 공개 URL, 팀 최종 브랜치/PR은 별개입니다. 현재 원격 push·PR·merge, 유료 AI 호출, AWS 변경은 실행하지 않았습니다. 개인 저장소 이력은 팀원 4명 각각의 기여를 대신하지 않으며, `docs/CONTRIBUTIONS.md`와 `docs/IMPLEMENTATION_STATUS.md`의 실제 상태를 기준으로 설명합니다.

## 본인 확인 전에 남은 일

- 위 여섯 항목을 실제 파일과 실행 화면을 보며 자신의 말로 설명합니다.
- 이해가 다른 부분은 문장을 고치는 대신 코드·계약·실행 결과를 다시 대조합니다.
- 확인 날짜와 확인자를 팀이 정한 실제 증빙 위치에 기록합니다.
- 그 전까지 M21은 `NOT_RUN`으로 유지합니다.
