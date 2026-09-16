# B7-1 프로젝트 자료 대조·팀 기획·적용 결정

버전 2.0 / 검토 기준일 2026-09-16

## 1. 검토 범위와 결론

이번 사용자 메시지의 공식 미션 M, 새 첨부 S01~S11, 이전 v1 패키지의 여섯 MD를 대조했다. **v1은 새로 제공된 팀 API/DB/설정과 여러 핵심 지점에서 호환되지 않는다.** 특히 아이디·질문·답변 필드, 중복가입 상태코드, 대화 응답 형태, JWT 기간, DB 파일/필드, 라이브러리를 수정해야 한다.

v1에 없던 새 자료가 이번에 제공되었으므로 과거의 임시 선택을 최신 확정 계약처럼 유지하지 않는다. 반대로 원자료의 모든 내용이 실행 검증을 거쳤다는 뜻도 아니다. 아래 C는 충돌 해결, D는 자료의 빈칸을 채운 최소 구현 결정, E는 별도 외부 기술 근거다. 모든 수정은 **개인 기준 구현의 적용안**이며 Organization에 대한 승인·반영 사실이 아니다.

11개 파일을 전부 이 패키지에 수록했다. CRLF/LF와 마지막 개행만 UTF-8/LF 기준으로 정규화했다. 본문·코드·예시는 원자료 블록에서 생략하지 않았다. 블록은 원본 보존용이며 `.env`의 예시 값이나 배포 명령을 그대로 실행하라는 지시가 아니다.

## 2. 출처 목록과 정규화 해시

M: 이번 메시지에 다시 제공된 공식 미션. `MISSION_REQUIREMENTS.md` 1~7절에 본문을 보존했다. 빈 이미지 자리와 화면 라벨은 제외했다. S01~S11의 원자료 SHA-256 및 정규화 텍스트 SHA-256을 아래에 적는다. 정규화는 BOM 제거, CRLF→LF, 마지막 개행 1개이며 내용 수정이 아니다.

| 출처 | 첨부 파일 → 원래 대상 | 이 패키지의 수록 위치 |
|---|---|---|
| S01 | `README(1).md` → `README.md` | `docs/PROJECT_PLAN.md`의 S01 블록 |
| S02 | `requirements.txt` → `requirements.txt` | `docs/IMPLEMENTATION_SPEC.md`의 S02 블록 |
| S03 | `AGENTS(2).md` → `AGENTS.md` | `AGENTS.md`의 S03 블록 |
| S04 | `.env.example` → `.env.example` | `docs/IMPLEMENTATION_SPEC.md`의 S04 블록 |
| S05 | `.gitignore` → `.gitignore` | `docs/IMPLEMENTATION_SPEC.md`의 S05 블록 |
| S06 | `schemas.py` → `app/schemas.py` | `docs/IMPLEMENTATION_SPEC.md`의 S06 블록 |
| S07 | `api_spec.md` → `docs/api_spec.md` | `docs/IMPLEMENTATION_SPEC.md`의 S07 블록 |
| S08 | `project_plan(1).md` → `docs/project_plan.md` | `docs/PROJECT_PLAN.md`의 S08 블록 |
| S09 | `pull_request_template.md` → `.github/pull_request_template.md` | `docs/PROJECT_PLAN.md`의 S09 블록 |
| S10 | `bug_report.md` → `.github/ISSUE_TEMPLATE/bug_report.md` | `docs/PROJECT_PLAN.md`의 S10 블록 |
| S11 | `feature_request.md` → `.github/ISSUE_TEMPLATE/feature_request.md` | `docs/PROJECT_PLAN.md`의 S11 블록 |

검증용 SHA-256 (첫째 원바이트, 둘째 정규화 본문):

```text
S01 raw=f035d58c7330dcfff6d3502e81f58e46ad5d2c596eb526ca35881d1606f76a52
S01 text=2d44bbc5dc91971f9a7fecf512bdc479c293ea8da4aaa8c9929d9306a3263ec0
S02 raw=423a1466bf09c94abbd015bbb1e06b79b076b3118338ab75d5d922dd0d5dbb6d
S02 text=b9a7da34db89df99254c2ae6cbc6ed2f250a7f368787254ebac23da7cd735384
S03 raw=00ca6de0ea6f82be124879a75ceb4d27667bceb9734108aba00e3d91dd9f8eaf
S03 text=44299820c1543a0752b7c457e0ce0bf87b7a2cd66250aa13de8d778d6efa5bcc
S04 raw=1a4c3167bf58dfd05fe6d928e28c5035b33836a17f4632b106bbd2a32f42df64
S04 text=e1f96cb6ea233592e483abfa6e0bdb48de0738580e2019706c9bb180962e1d9c
S05 raw=ef5988efd9a6c4e1dd8b650ca43bc10b39a6d53b022c207df86f94850d363e6e
S05 text=d43e38c376049351b5d1606f7731c0290786e02ab9fb3433cc65b4e94bddd2ac
S06 raw=e06b7d32f6fde28e44f4ff9758ed5e1270b933b19f69483a4fecb8df0f8f9af0
S06 text=6f1287874a1bbb6db61d8030af43684856e750bc4788dd24683b734fc9ab8380
S07 raw=0147ca48a96eceaa37e57586d93be34a528d5105c1d470eeea8295c4e3795793
S07 text=1277764bbabba334522188c951132d0c39a40a9a10786b40e9983de4f4cd25b4
S08 raw=aa6c0c81c7eec63993dc908c607392704a8d97e77461dbc7c7c1e625220ff98b
S08 text=b60640c2fd19293c937c573fc45b32a303667d38ac1820a5c4968654e071e9d6
S09 raw=bb1201e380b7f46f077291656b665f637d07985ab7c1e027abef5f7dcfabb509
S09 text=9cdfd36a09ce95adec57deff43ac8b7c32e2b1b726030492a20a5a7d9292f319
S10 raw=8b67eb9e798b0d67a266b1ef83a93dc73e5ad49b81d4df4ec4ecd4afe95f212a
S10 text=d9efb964e637d63c6b0a0fcb96418e4063038a110fde50e907dbb5c79d6192da
S11 raw=76ee2da1406bde14506adae5e1be6a6a647fd046069764f3584af8465ba80868
S11 text=8374e9c3954016960bc6431382c8257a4a6ad7a014c63c4786ac029945bb6010
```


## 3. 최신 첨부를 반영한 제품·역할 계획

서비스명은 **AI Assistant**다. FastAPI/SQLite/Vanilla JS 기반이며 로그인한 사용자가 AI와 대화하고 이전 문맥과 자신의 대화 기록을 이어가는 웹 서비스다. 코디세이 API를 서버에서 호출하고 8초 timeout과 운영 로그를 갖춘다. 기획의 기간은 4일 프로토타입 목표이고 공식 학습시간은 120시간이다.

| 팀원 | 원자료의 담당 | 개인 기준 구현에서 지킬 모듈 경계 |
|---|---|---|
| 고준석 | 인증 / PM | app/auth.py, auth_router.py, register/login, get_current_user |
| 박범규 | 백엔드 코어 / DB | main/database/models/logger/chat_router, 대화 저장·조회·SQL |
| 이준혁 | 프론트 UI/UX | static/index.html, css/style.css, js/auth.js·app.js, 모달·토큰·응답·오류 |
| 차종민 | AI 파이프라인 | ai_service.py, messages 조합, 공급자 호출, timeout, Mock |

`POST /api/chat`의 HTTP 흐름은 백엔드 라우터가 소유하고 AI 모듈은 질문/문맥을 받아 결과를 반환한다. 이 소유권의 구체화는 D01이며 원자료가 명시하지 않은 부분을 채운 것이다. 개인 저장소의 전체 구현을 위 네 사람이 실제 수행했다고 문서화하지 않는다.

## 4. v1과 새 자료의 불일치 및 자료 내부 충돌 — C01~C24

| ID | 충돌·누락 | v2 처리와 지위 |
|---|---|---|
| C01 | v1 email/message/reply/chat_id/ai_mode vs S06/S07 username/question/answer/latency_ms | 최신 외부 API로 전면 교체. 이전 필드 alias도 제공하지 않음. signup 성공 message+username, 중복 400, health status만, 기록은 배열 |
| C02 | S07은 공백질문 400, S06의 Field/validator는 기본 FastAPI에서 422 | 스키마 필드 유지. RequestValidationError 처리기에서 해당 경로·필드의 실제 공백 입력만 400/detail 문자열로 정규화. 나머지 422를 400으로 뭉개지 않음 |
| C03 | S07 모든 오류 detail 문자열 vs 기본 검증 detail 배열 | 공통 오류 처리기를 추가. 예외 객체·입력·비밀번호를 응답/운영 로그에 반사하지 않음. OpenAPI 오류 모델도 맞춤 |
| C04 | S07 아이디 공백 400 vs S06 기본 422; ‘공백 불가’와 strip 처리의 해석 | 가입 아이디가 공백만이면 400. 원자료 코드처럼 앞뒤 공백만 제거, 내부 공백 금지 규칙은 새로 만들지 않음. 길이는 S06처럼 원문 max 검사 후 trim/min. 팀 공유 시 의미 재확인 |
| C05 | S07 로그인 password 공백 불가 vs S06은 빈 문자열만 거부 | 로그인 validator에 `not value.strip()` 검사를 추가하고 검증오류 422/detail로 처리. 비밀번호 자체는 trim해 저장/비교하지 않음 |
| C06 | S06/S07 비밀번호 4~100자 vs bcrypt의 72바이트 한계; v1 8자/72바이트로 축소 | 4~100자 계약을 보존. 독립 신규 DB는 문서화된 bcrypt 기반 `passlib.hash.bcrypt_sha256` v2 사용을 보완안으로 채택. 원시 bcrypt와 다른 해시 포맷임을 명시하고 기존 팀 DB에 묵시 적용 금지. 절단·평문·단순 SHA 저장 금지 |
| C07 | S02 passlib/bcrypt 모두 하한만 지정하여 임의 조합 설치 가능 | 원문 requirements 전체 유지. C06의 해시 smoke test 후 검증된 조합을 constraints/lock에 기록. 1.7.4/4.0.1은 **검증 후보**이지 본 패키지가 실행 검증·보안 보증한 조합 아님. 무조건 최신 설치/무조건 구버전 다운그레이드 금지 |
| C08 | v1 PyJWT/sqlite3/email-validator vs S02 python-jose/aiosqlite/pydantic-settings | S02 채택 라이브러리로 되돌림. SQLAlchemy 등 추가 안 함. hash 작업만 thread 경계 사용 |
| C09 | v1 youthbot.db/email/password_hash/ai_mode vs S01/S04 | chatbot.db, username, hashed_password, latency_ms 및 WAL로 맞춤. ai_mode DB/API 필드는 제거. Mock와 실데이터는 명시적 별도 DB 사용으로 구분 |
| C10 | S03 모든 경로 상대 vs S01 systemd 절대경로/시스템 설치 경로 | 앱·문서 링크는 상대경로. 배포용 설정은 템플릿→런타임 경로 렌더링으로 구분. 시스템 절대경로 필요성 자체는 사라지지 않으므로 팀 배포 해석 승인 필요. 원문 명령은 보존만 함 |
| C11 | S03 공개 HTTP80만 vs 로그인/JWT를 인터넷에 평문 전달하는 위험 | 80/내부8000의 원계획 보존. HTTPS443 추가는 안전한 공개운영을 위한 **변경 제안**으로 기록하고 승인 없이 SG 변경 금지. HTTP 평가 시연을 선택하면 전용 폐기 계정·비민감 질문·노출 시간/비용 제한의 위험을 명시; 보안 완료로 표현 금지 |
| C12 | v1 2GB Swap 선택 vs 최신 S03 ‘반드시’ | 팀 필수 2GB 구성을 다시 포함. 로컬 개발 선행조건은 아님. 기존 swap/디스크 확인, 중복 생성 금지, 시스템 변경 승인 필요. OOM 완전 방지 문구는 목표/완화책으로 구분 |
| C13 | t2.micro ‘프리티어’의 무조건 무료 전제 | 팀 목표 인스턴스 유지. 실제 계정 생성일/리전/요금/잔여 혜택은 미확인. 비용 확인 실패 시 배포만 대기. 임의 t3/Vercel/다른 클라우드 전환 금지 |
| C14 | v1 명시 Mock만 vs S01/S03/S08 키 미입력 시 Mock | 개발·테스트에서 키 없음/예시 키를 Mock으로 처리하는 auto 모드 추가. 실제 키 오류/timeout은 504, 자동 성공 fallback 금지. 운영 real 모드는 키 없으면 기동 실패 |
| C15 | S04 OpenAI URL/모델/500만 토큰 문구 vs 실제 코디세이 연결 확인 부재 | 첨부 .env.example 그대로 보존·초기 복원하되 예시라는 주석과 모드 설정 추가. 실제 .env는 키를 비우고 서명키 생성. URL/모델은 제공자 확인 전 실호출·성공 주장 금지 |
| C16 | v1 일부 AI 장애 502 vs S03 timeout 또는 API 에러 504 | 팀 규칙대로 외부 AI 실패 504/detail. 로그에는 timeout/upstream/auth/invalid_response 등을 분류. 변경 필요하면 팀 API 개정으로 별도 처리 |
| C17 | `httpx timeout=8`이면 전체 요청이 정확히 8초라는 해석 | connect/read/write/pool 제한과 전체 AI await 제한을 함께 적용. DB·인증·취소 정리까지 포함한 절대 8.000초 보장으로 설명하지 않음 |
| C18 | scripts/check_logs.sql 및 ‘4대 이벤트’를 오류라고 한 과거 지적 | 파일명과 네 범주 유지. 서버 운영 로그와 대화 DB는 별개. S03의 6개 이벤트 모두 포함 |
| C19 | S06 ChatHistoryResponse가 있어 래퍼 사용 가능성; v1 페이지네이션/모드필드 | S07 명시대로 List[ChatLogItem]을 반환. 래퍼 클래스는 보존하되 이 엔드포인트에 사용 안 함. 페이지네이션은 최소 범위에서 제외 |
| C20 | S05가 SQLite WAL/SHM 및 .env.production 제외 못 함 | 원문 ignore 유지 후 `.env.*`, 예시 예외, DB 부속파일·키·테스트 산출물 규칙 추가. 이미 추적한 파일은 별도 검사 |
| C21 | S10 bug_report.md의 마지막 코드 fence 미종료 | 원문 블록 보존. 실제 Issue 템플릿 생성 시 마지막 닫는 fence만 추가하고 수정 이력 기록. S09/S11 항목·예시의 뜻은 유지 |
| C22 | 주석 100% 한국어 vs S06에 영어 주석 제목; raw string 일괄 사용 | 새 코드 주석 제목을 한국어로 정리하되 클래스/API 이름은 유지. 모든 문자열에 r 접두사 강제하지 않고 경로/escape 안전성으로 규칙 목적을 충족 |
| C23 | v1 commit 금지/후보만 나열 vs 사용자 요청 최소10회; 개인 풀스택과 팀 이력 혼동 | 사용자 승인 시작 프롬프트에 실제 본인 로컬 20개 작업별 커밋 포함. 팀원 4명 각각의10개는 별도 실제 기록으로 검증. PR/원격 변경은 별도 승인, squash 영향 명시 |
| C24 | Windows에서 docs/PROJECT_PLAN.md와 docs/project_plan.md는 같은 파일로 충돌 | 입력 패키지 PROJECT_PLAN.md 하나를 유지. S08을 같은 이름의 소문자 파일로 다시 추출하지 않음. 생성 README의 링크는 실제 PROJECT_PLAN.md로 고침 |

위 표는 충돌을 숨기지 않고 선택을 드러낸다. C06 해시 형식, C10 배포 경로 해석, C11 HTTPS/보안그룹, C13 인스턴스 대안은 팀에 이식할 때 합의가 필요한 사항이다. 이로 인해 로컬 UI/API 개발까지 멈출 필요는 없지만 해당 항목을 ‘팀 승인 완료’로 표시하지 않는다.

## 5. 나머지 최소 구체화 — D01~D06

| ID | 원자료가 확정하지 않은 내용 | 개인 기준 구현의 결정 |
|---|---|---|
| D01 | POST /api/chat 최종 조립자 | chat_router가 인증→검증→조회→AI→저장→응답, ai_service는 DB/HTTP 상태코드 직접 소유 안 함 |
| D02 | DB 결과의 순서·시각 및 실패 처리 | 내 기록 id 오름차순, 저장시 UTC를 ISO8601 초 단위 문자열로 표시(팀 예시처럼 offset 없음, README에 UTC 명시). DB 실패는 500/detail와 rollback; AI 실패는 정상 대화 행 저장 안 함 |
| D03 | 최근 3~5쌍 중 선택 | 최근5쌍을 id 역순 조회 후 뒤집기. 다른 사용자/실패/Mock-실DB 혼입 방지. 전체 기록 삭제 안 함 |
| D04 | Mock 표시·실데이터 분리 | `AI_MODE=auto|mock|real`, 개발 auto 키없음 Mock. health/chat의 X-AI-Mode 헤더와 Mock 답변 표식 사용. JSON 스키마 추가 없음. init_env에서 개발 DB 경로를 명시적으로 분리 |
| D05 | 문제·타겟·최소 UI | 질문과 이전 대화를 이어 확인하려는 학습자/일반 사용자용 AI Assistant. 가정임을 표시. 한 화면·모달·반응형·텍스트 답변; 특정 청년정책 주제는 확정하지 않음 |
| D06 | 수행권한/검증·완료 선언 | 로컬 코드/테스트/승인된 본인 커밋 허용. real AI·비용·외부 공개·원격 PR/merge는 별도. LOCAL_MINIMUM/REAL_AI/PUBLIC_URL/TEAM_HISTORY를 따로 보고 |

## 6. 이번 검토에서 직접 재현한 것과 못 한 것

첨부 S06을 수정하지 않고 임시 FastAPI 라우트에 연결한 검증을 수행했다. 실제 팀 앱은 제공되지 않아 테스트하지 않았다. 환경은 FastAPI 0.128.2, Pydantic 2.13.4, Starlette 0.50.0, HTTPX 0.28.1이었다. 이는 재현 환경 표기이지 패키지의 고정 버전 추천이 아니다.

| 입력/검사 | 원문 기본 동작 | 의미 |
|---|---|---|
| question 빈 문자열/공백3개 | 422, detail 배열 | 팀 API의400/문자열과 다름; C02/C03 필요 |
| question 501자 | 422, detail 배열 | 상태는 맞고 응답형식 수정 필요 |
| 양끝 공백+내용500자, 총502자 | 422 | 원문 Field max_length는 trim 이전에 작동 |
| 가입 username 공백3개 | 422 | S07 공백400과 불일치 |
| 가입 username `ab cd` | 모델 검증 통과 | 원문은 내부 공백을 금지하지 않음 |
| 로그인 password 공백4개 | 모델 검증 통과 | 실제 인증 성공 의미가 아님; C05 필요 |
| chat에 여분 user_id 필드 | 무시되고 question만 모델에 남음 | 원문 extra 기본 동작 유지, 서버 사용자만 사용 |
| Git ignore .env/DB/log | 제외됨 | 기본 파일 제외 정상 |
| Git ignore DB-wal/DB-shm/.env.production | 제외되지 않음 | C20 보완 필요 |

bcrypt/passlib 해시 후보 조합을 설치해 확인하려 했으나 이 검토 환경의 DNS/패키지 네트워크 접근 실패로 설치하지 못했다. **해시 후보 smoke test·전체 의존성 설치는 미실행**이다. 이 사실을 앱의 호환 성공으로 바꾸지 않는다. Codex의 R03에서 실제 해시/로그인/긴 비밀번호 검증을 완료해야 한다.

## 7. 아직 원자료로 확인할 수 없는 사항

코디세이의 실제 제공자 URL·헤더·모델·권한·잔여 토큰, 현재 AWS 계정/요금/서버, GitHub 작성자 이메일과 팀 최종 PR/커밋 기록, 해시 형식에 대한 팀 합의, 배포 경로/HTTPS 예외 승인은 첨부자료로 확인되지 않았다. 자동 추정하지 않는다. 변수·대기 항목으로 분리하며 합의·실검증한 항목만 상태를 변경한다.

## 8. 별도 확인한 기술 근거 — 첨부자료를 대체하지 않음

확인일 2026-09-16. E는 구현상 충돌의 이유를 확인하는 자료다. 팀 미션·코디세이 공급자 계약을 대신하지 않는다.

| ID | 공식/1차 기술 자료 | 확인 범위 |
|---|---|---|
| E01 | `https://developers.openai.com/codex/guides/agents-md/` | AGENTS 발견과 나머지 문서의 명시적 읽기 |
| E02 | `https://developers.openai.com/codex/ide/` | IDE에서 로컬 폴더 작업 |
| E03 | `https://fastapi.tiangolo.com/tutorial/handling-errors/` | RequestValidationError 처리기 변경 |
| E04 | `https://github.com/pyca/bcrypt` | 원시 bcrypt의72바이트 한계와 버전별 동작 |
| E05 | `https://passlib.readthedocs.io/en/stable/lib/passlib.hash.bcrypt_sha256.html` | 길이 문제를 처리하는 문서화된 bcrypt 기반 scheme |
| E06 | `https://github.com/pyca/bcrypt/issues/684` | passlib와 bcrypt 조합의 버전 읽기 문제 보고; 검증 필요성, 모든 조합 실패 주장 아님 |
| E07 | `https://www.python-httpx.org/advanced/timeouts/` | 연결/읽기/쓰기/풀 timeout 구분 |
| E08 | `https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html` | 계정 생성시점별 혜택이 달라 무조건 무료라고 말할 수 없음 |
| E09 | `https://docs.github.com/en/pull-requests/reference/pull-request-merges` | merge/squash/rebase 및 원커밋 보존 차이 |
| E10 | `https://git-scm.com/docs/git-shortlog` | 작성자별 이력 집계; 내용의 유의미성 자동 보증 아님 |
| E11 | `https://git-scm.com/docs/gitignore` | 추적 중인 파일은 ignore만으로 제거 안 됨 |
| E12 | `https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html` | 암호 해시와 길이 제약·임의 전처리의 위험 참고 |

이 자료들의 기술 설명은 원문 전체를 전재하지 않고 필요한 범위만 요약했다. 확인된 동작 외 보안/성능/완성 시간은 보장하지 않는다.

## 9. 원자료 복원 원칙

S01 README는 참고로 읽고 실제 구현 상태에 맞춰 생성한다. S08의 날짜별 업무·역할은 보존하되 실행 순서는 MILESTONES의 조기 E2E 방식으로 보완한다. S09/S11 양식은 원문 유지 후 실제 Issue 연결·검증 결과·체크 항목을 추가할 수 있다. 예시의 청년정책/30건 데이터는 예시이지 기능 요구사항이 아니다. S10만 닫는 fence를 명시적으로 보완한다. 정리 과정에서 가짜 Issue 번호/PR URL/팀 기여를 만들지 않는다.

## 원자료 S01 — `README(1).md`

원래 배치 대상: `README.md`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S01 -->
````markdown
# AI Assistant (7-1 웹 기반 AI 챗봇 서비스)

> **과제명**: B7-1 웹 기반 AI 챗봇 서비스 개발 프로젝트  
> **프로젝트 목표**: 사용자 인증, 코디세이 AI API 비동기 연동, 대화 문맥 유지, SQLite 영속 저장 및 4대 표준 로깅을 결합한 4일 단기 완성 웹 챗봇 프로토타입(MVP)

---

## 1. 팀 구성원 및 역할 분담 (R&R)

전 팀원은 각자의 담당 영역을 독립적으로 개발하고, PR 기반 머지 및 1인당 최소 10회 이상의 커밋을 달성합니다.

| 팀원 | 담당 역할 | 세부 업무 내용 및 기여 영역 |
| :--- | :--- | :--- |
| **고준석** (팀장) | **로그인 & 인증 (Auth) / PM** | • 회원가입(`POST /api/auth/register`) 및 로그인(`POST /api/auth/login`) API<br>• 비밀번호 `bcrypt` 단방향 해싱 및 JWT 액세스 토큰 발급/검증 로직<br>• 미인증 사용자 접근 차단용 FastAPI Dependency (`get_current_user`) 구현<br>• 프로젝트 전체 일정 조율 및 마일스톤 관리 |
| **박범규** | **백엔드 코어 & DB** | • FastAPI 메인 애플리케이션 진입점 및 라우터 통합 (`app/main.py`)<br>• SQLite DB 연결 및 테이블 스키마 (`users`, `chat_logs`) 설계/구축<br>• 대화 로그 저장 함수 및 내 대화 이력 조회 API (`GET /api/me/chats`)<br>• 과제 필수 표준 4대 이벤트 로깅 모듈 및 검증용 `scripts/check_logs.sql` 작성 |
| **이준혁** | **프론트엔드 UI/UX** | • 단일 페이지 반응형 웹 챗봇 인터페이스 (`static/index.html`, `style.css`)<br>• 로그인 및 회원가입 모달 UI, JWT 로컬 스토리지 보관 및 헤더 전송 (`auth.js`)<br>• 실시간 메시지 버블 렌더링, 로딩 인디케이터, 비동기 API 통신 (`app.js`)<br>• 에러 토스트 피드백 및 모바일/데스크탑 반응형 웹 최적화 |
| **차종민** | **AI 파이프라인** | • 코디세이 AI API 비동기 연동 모듈 (`app/ai_service.py`) 구축<br>• 최근 대화 3~5쌍을 조합하는 슬라이딩 윈도우 문맥(Context) 유지 전략 구현<br>• 8.0초 타임아웃 예외 핸들링 및 서버 프로세스 다운 방지 로직 (504 반환)<br>• 외부 키 미설정 시에도 시연 및 평가가 가능한 내장 Mock AI 엔진 구현 |

---

## 2. 시스템 아키텍처

```text
[ 사용자 브라우저 ]
        │ HTTP (80)
        ▼
[ AWS EC2 t2.micro (Ubuntu 22.04 LTS) ]
 ├── [ Nginx 리버스 프록시 ] (Port 80 -> Port 8000 라우팅 및 정적 리소스 서빙)
 └── [ Uvicorn + FastAPI ] (Port 8000 로컬 바인딩, Systemd 서비스 데몬 구동)
      ├── [ 인증 미들웨어 ] (JWT 토큰 유효성 검증, 미인증 시 401 차단)
      ├── [ AI 파이프라인 ] (문맥 조립 -> 8초 타임아웃 -> 코디세이 AI API / Mock AI)
      ├── [ 표준 로거 ] (4대 핵심 이벤트 실시간 콘솔/파일 기록)
      └── [ SQLite DB ] (users, chat_logs 테이블 / WAL 모드)
```

---

## 3. 4일 프로토타입 개발 일정 (마일스톤 요약)

```text
[Day 1] 독립 모듈 구축 ──> [Day 2] 코어 기능/API 완성 ──> [Day 3] 전체 E2E 결합 ──> [Day 4] 안정성 & 시연 점검
```

- **Day 1**: 독립 컴포넌트 뼈대 세팅 & 단독 PoC 검증 (인증, DB, UI, AI API)
- **Day 2**: 각자 담당 코어 API 및 비즈니스 로직 완성
- **Day 3**: 백엔드-프론트엔드-AI 전체 파이프라인 E2E 1차 결합 (Alpha Release)
- **Day 4**: 안정성 강화, 입력 검증, EC2 배포 및 프로토타입 시연 점검

👉 **일자별 상세 태스크 및 체크리스트**: [docs/project_plan.md](docs/project_plan.md) 참고

---

## 4. 데이터베이스 구조 (Data Schema)

SQLite 데이터베이스 파일 경로: `data/chatbot.db`

### 4.1 users 테이블
| 필드명 | 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 사용자 고유 번호 |
| `username` | VARCHAR(50) | UNIQUE, NOT NULL | 로그인 아이디 |
| `hashed_password` | VARCHAR(255) | NOT NULL | bcrypt 단방향 암호화된 비밀번호 |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 계정 생성 일시 |

### 4.2 chat_logs 테이블
| 필드명 | 타입 | 제약 조건 | 설명 |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 대화 로그 고유 번호 |
| `user_id` | INTEGER | NOT NULL, FK(users.id) | 대화를 진행한 사용자 식별자 |
| `question` | TEXT | NOT NULL | 사용자가 입력한 질문 |
| `response` | TEXT | NOT NULL | AI가 생성한 응답 텍스트 |
| `latency_ms` | INTEGER | DEFAULT 0 | AI API 호출 소요 시간 (밀리초) |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 대화 기록 일시 |

---

## 5. API 명세 (핵심 엔드포인트)

| 메서드 | 엔드포인트 | 인증 필요 | 설명 | 요청 예시 | 응답 예시 |
| :--- | :--- | :---: | :--- | :--- | :--- |
| `POST` | `/api/auth/register` | X | 신규 회원가입 | `{"username": "testuser", "password": "pass1234"}` | `201 Created` |
| `POST` | `/api/auth/login` | X | 로그인 및 JWT 토큰 발급 | `{"username": "testuser", "password": "pass1234"}` | `{"access_token": "eyJ...", "token_type": "bearer"}` |
| `POST` | `/api/chat` | **O (필수)** | AI 질문 전송 및 답변 수신 | `{"question": "안녕? 너는 누구야?"}` | `{"answer": "안녕하세요! AI 어시스턴트입니다.", "latency_ms": 450}` |
| `GET` | `/api/me/chats` | **O (필수)** | 본인 대화 이력 조회 | - | `[{"id": 1, "question": "...", "response": "...", "created_at": "..."}]` |
| `GET` | `/api/health` | X | 서버 헬스체크 | - | `{"status": "ok"}` |

---

## 6. 설치 및 로컬 실행 방법

### 6.1 가상환경 생성 및 패키지 설치
```bash
# 가상환경 생성 (Python 3.10+)
python -m venv venv

# 가상환경 활성화 (Windows PowerShell)
.\venv\Scripts\Activate.ps1
# (Linux/macOS) source venv/bin/activate

# 필수 패키지 설치
pip install -r requirements.txt
```

### 6.2 환경변수 설정
`.env.example` 파일을 복사하여 `.env` 파일을 생성하고 값을 설정합니다:
```bash
cp .env.example .env
```
`.env` 파일 내용:
```ini
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
```

### 6.3 로컬 개발 서버 실행
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
브라우저에서 `http://localhost:8000` 접속 시 웹 챗봇 화면이 서빙됩니다.

---

## 7. AWS EC2 프리티어 배포 및 인프라 가이드

### 7.1 인스턴스 사양 및 메모리 스왑 설정
*   **인스턴스**: AWS EC2 `t2.micro` (Ubuntu 22.04 LTS, RAM 1GB)
*   **2GB Swap 메모리 설정 (OOM 크래시 방지 필수)**:
    ```bash
    sudo fallocate -l 2G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    ```

### 7.2 Nginx 리버스 프록시 설정
FastAPI 단독 노출 대신 80번 표준 포트 수신 후 내부 8000번 포트로 전달합니다:
```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### 7.3 Systemd 백그라운드 서비스 등록
SSH 세션 종료 후에도 서비스가 상시 구동되도록 systemd에 등록합니다.
`/etc/systemd/system/chatbot.service`:
```ini
[Unit]
Description=FastAPI AI Chatbot Service
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/7-1
ExecStart=/home/ubuntu/7-1/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

---

## 8. 운영 안정성 및 표준 로깅 체계

1. **표준 4대 이벤트 로깅**:
   ```text
   INFO request_received user_id=1 path=/api/chat
   INFO ai_call_start user_id=1 request_id=req-98234
   INFO ai_call_success request_id=req-98234 latency_ms=480
   INFO db_save_success user_id=1 chat_id=102
   ```
2. **AI 타임아웃 및 장애 복원력**:
   * 코디세이 API 호출 시 `timeout=8.0초` 강제. 지연 발생 시 서버가 죽지 않고 504 Gateway Timeout 반환.
   * `CODESSEY_API_KEY` 미입력 시 내장 Mock AI가 친절한 모의 답변을 생성하여 평가자 환경에서도 100% 정상 구동 지원.
3. **대화 로그 확인 SQL 스크립트**:
   `scripts/check_logs.sql`을 실행하여 누적된 질문, 답변, 응답 지연시간(`latency_ms`)을 즉시 조회할 수 있습니다.
````
<!-- SOURCE_END:S01 -->

## 원자료 S08 — `project_plan(1).md`

원래 배치 대상: `docs/project_plan.md`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S08 -->
````markdown
# B7-1 웹 기반 AI 챗봇 4일 프로토타입 프로젝트 계획서

> **프로젝트명**: AI Assistant (7-1 웹 기반 AI 챗봇 서비스)  
> **개발 기간**: 4일 집중 완성 (Day 1 ~ Day 4)  
> **목표**: 4일 내 핵심 컴포넌트(웹 UI ↔ 로그인/인증 ↔ FastAPI 백엔드 ↔ 코디세이 AI API ↔ SQLite DB ↔ AWS EC2 배포)가 100% 결합된 동작 가능한 프로토타입(MVP) 완성

---

## 1. 프로젝트 개요 및 범위

### 1.1 프로젝트 개요
본 프로젝트는 사용자가 웹 브라우저에서 로그인 후 실시간으로 AI 챗봇과 대화를 나누고, 이전 대화의 문맥(Context)을 유지하며 응답을 제공받는 웹 기반 AI 서비스입니다. 모든 대화 기록은 SQLite DB에 영속적으로 저장되며, 표준화된 4대 핵심 서버 로깅과 AI 호출 타임아웃 방어 체계를 갖추어 안정적인 운영을 보장합니다.

### 1.2 핵심 개발 범위 (Scope)
- **인증 및 접근 제어**: 회원가입, 로그인, bcrypt 단방향 암호화, JWT 토큰 발급 및 엔드포인트 인가
- **AI 대화 파이프라인**: 코디세이 AI API(OpenAI 호환 GPT-4o-mini) 비동기 호출, 슬라이딩 윈도우(최근 3~5쌍) 문맥 조합, 8.0초 타임아웃 방어, Mock AI 엔진
- **데이터베이스 및 로깅**: SQLite users/chat_logs 모델링, 대화 이력 저장/조회 API, 4대 핵심 이벤트 로깅
- **웹 인터페이스**: 반응형 단일 페이지 챗봇 UI, 로그인/회원가입 모달, 비동기 REST 통신
- **인프라 및 배포**: AWS EC2 프리티어(t2.micro), 2GB Swap 메모리, Nginx 리버스 프록시, Systemd 상시 구동

---

## 2. 팀 구성원 및 역할 분담 (R&R)

| 팀원 | 담당 역할 | 핵심 개발 영역 |
| :--- | :--- | :--- |
| **고준석** (팀장) | **로그인 & 인증 (Auth) / PM** | • 회원가입(POST /api/auth/register) 및 로그인(POST /api/auth/login) API<br>• 비밀번호 bcrypt 단방향 해싱 및 JWT 액세스 토큰 발급/검증 로직<br>• 미인증 사용자 접근 차단용 FastAPI Dependency (get_current_user) 구현<br>• 프로젝트 전체 일정 조율 및 마일스톤 관리 |
| **박범규** | **백엔드 코어 & DB** | • FastAPI 메인 애플리케이션 진입점 및 라우터 통합 (app/main.py)<br>• SQLite DB 연결 및 테이블 스키마 (users, chat_logs) 설계/구축<br>• 대화 로그 저장 함수 및 내 대화 이력 조회 API (GET /api/me/chats)<br>• 과제 필수 표준 4대 이벤트 로깅 모듈 및 검증용 scripts/check_logs.sql 작성 |
| **이준혁** | **프론트엔드 UI/UX** | • 단일 페이지 반응형 웹 챗봇 인터페이스 (static/index.html, style.css)<br>• 로그인 및 회원가입 모달 UI, JWT 로컬 스토리지 보관 및 헤더 전송 (auth.js)<br>• 실시간 메시지 버블 렌더링, 로딩 인디케이터, 비동기 API 통신 (app.js)<br>• 에러 토스트 피드백 및 모바일/데스크탑 반응형 웹 최적화 |
| **차종민** | **AI 파이프라인** | • 코디세이 AI API 비동기 연동 모듈 (app/ai_service.py) 구축<br>• 최근 대화 3~5쌍을 조합하는 슬라이딩 윈도우 문맥(Context) 유지 전략 구현<br>• 8.0초 타임아웃 예외 핸들링 및 서버 프로세스 다운 방지 로직 (504 반환)<br>• 외부 키 미설정 시에도 시연 및 평가가 가능한 내장 Mock AI 엔진 구현 |

---

## 3. 4일간의 일자별 상세 마일스톤

```text
[Day 1] 독립 모듈 구축 ──> [Day 2] 코어 기능/API 완성 ──> [Day 3] 전체 E2E 결합 ──> [Day 4] 안정성 & 시연 점검
```

### Day 1: 독립 컴포넌트 뼈대 세팅 & 단독 PoC 검증
- **공통 목표**: 개인별 작업 브랜치 생성 및 각자 영역의 독립 베이스라인 구축
- **작업 브랜치**: feat/auth-ko, feat/backend-park, feat/ui-lee, feat/ai-cha
- **세부 태스크**:
  - [고준석] 비밀번호 bcrypt 해싱 및 JWT 토큰 생성 유틸리티 함수 작성 (app/auth.py)
  - [박범규] FastAPI 기본 프로젝트 골격 생성 및 SQLite 스키마(users, chat_logs) 세팅 (app/database.py, app/models.py)
  - [이준혁] 반응형 채팅 인터페이스 HTML/CSS 와이어프레임 작성 (static/index.html, static/css/style.css)
  - [차종민] 코디세이 AI API 단독 호출 PoC 스크립트 작성 및 8초 타임아웃 사전 검증 (app/ai_service.py)

### Day 2: 각자 담당 코어 API 및 비즈니스 로직 완성
- **공통 목표**: 각 컴포넌트의 핵심 기능 완성 및 단위 테스트 통과
- **세부 태스크**:
  - [고준석] 회원가입/로그인 엔드포인트 및 get_current_user 인증 의존성 완성 (app/routers/auth_router.py)
  - [박범규] 대화 로그 DB 저장 함수, GET /api/me/chats 구현, 표준 4대 로깅 포맷터 적용 (app/logger.py, app/routers/chat_router.py)
  - [이준혁] 로그인/회원가입 모달 UI 완성, 토큰 로컬스토리지 저장 및 백엔드 비동기 통신 연동 (static/js/auth.js)
  - [차종민] 슬라이딩 윈도우 문맥 조립 함수, 8초 타임아웃 예외처리 및 Mock AI 엔진 구현 (app/ai_service.py)

### Day 3: 백엔드-프론트엔드-AI 전체 결합 (Alpha Release)
- **공통 목표**: 전체 데이터 파이프라인의 엔드-투-엔드(E2E) 첫 결합 및 통합 테스트
- **세부 태스크**:
  - [고준석 + 박범규] 인증 미들웨어와 채팅 엔드포인트(POST /api/chat) 라우터 결합
  - [차종민 + 박범규] AI 응답 생성 결과를 SQLite chat_logs 테이블에 자동 저장하는 파이프라인 결합
  - [이준혁 + 팀 전원] 브라우저 UI에서 질문 입력 시 토큰 검증 -> 백엔드 수신 -> AI 호출 -> DB 저장 -> 화면 렌더링 전 과정 첫 E2E 성공 검증
  - [공통] 통합 PR 생성, 상호 코드 리뷰 후 develop 브랜치에 머지

### Day 4: 안정성 강화, 입력 검증 & 프로토타입 최종 점검
- **공통 목표**: 예외 방어 및 인프라 배포를 완료하고 시연 준비 완료
- **세부 태스크**:
  - [고준석] 비로그인 사용자 및 만료된 토큰 요청 시 401 차단 동작 검증
  - [박범규] 공백 입력(400) 및 500자 초과 비정상 입력(422) 차단 검증, scripts/check_logs.sql 작성 및 로그 조회 확인
  - [차종민] AI 타임아웃 발생 시 504 안내 메시지 UI 연동 및 Mock AI 정상 구동 테스트
  - [이준혁] 에러 토스트 피드백, 로딩 스피너 및 반응형 UI 최종 디테일 보완
  - [팀 전원] AWS EC2 인프라 세팅(Nginx, 2GB Swap, Systemd) 및 외부 접속 시연 점검

---

## 4. 리스크 관리 및 대응 방안

| 리스크 요인 | 영향도 | 사전 예방 및 대응 방안 |
| :--- | :---: | :--- |
| **AWS EC2 t2.micro 메모리 부족 (OOM)** | 높음 | 1GB RAM 한계 극복을 위해 OS 설치 직후 **2GB Swap 메모리**를 즉시 생성하여 프로세스 강제 종료를 사전에 차단합니다. |
| **코디세이 AI API 지연 및 무한 대기** | 높음 | 모든 외부 AI 호출에 timeout=8.0초를 강제 설정하고, 실패 시 504 안내 메시지를 반환하여 서버 프로세스가 다운되지 않도록 격리합니다. |
| **평가자 환경의 API 키 부재** | 중간 | CODESSEY_API_KEY가 설정되지 않았을 때도 서비스 시연이 가능하도록 내장 Mock AI 엔진을 기본 탑재합니다. |
| **브랜치 병합 시 코드 충돌** | 중간 | 기능 단위별로 모듈(auth.py, database.py, ai_service.py, static/)을 엄격히 분리하여 독립 개발하고, PR 기반으로 순차 머지합니다. |
````
<!-- SOURCE_END:S08 -->

## 원자료 S09 — `pull_request_template.md`

원래 배치 대상: `.github/pull_request_template.md`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S09 -->
````markdown
## 📌 PR 개요
- **작업자**: 
- **관련 기능**: (예: 회원가입 API 구현, 청년정책 DB 시딩 등)

## 🛠️ 주요 변경 사항
- [ ] 
- [ ] 

## 🧪 테스트 및 동작 검증 결과
- [ ] 로컬 실행 및 정상 동작 확인
- [ ] 비정상 입력(공백 등) 예외 처리 확인

## 📋 과제 필수 체크리스트
- [ ] 코드 주석 및 docstring이 100% 한국어로 작성되었는가?
- [ ] API Key, 비밀번호 등 민감정보가 하드코딩되지 않고 `.env`로 격리되었는가?
- [ ] 절대 경로(`file:///`) 없이 상대 경로로 작성되었는가?
````
<!-- SOURCE_END:S09 -->

## 원자료 S10 — `bug_report.md`

원래 배치 대상: `.github/ISSUE_TEMPLATE/bug_report.md`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S10 -->
````markdown
---
name: "버그 리포트 (Bug)"
about: "발생한 오류나 버그를 보고하고 수정하기 위한 티켓입니다."
title: "[BUG] "
labels: "fix"
assignees: ""
---

## 🐛 버그 설명
- 어떤 오류가 발생했는지 명확하게 적어주세요.
- (예: 비로그인 상태에서 챗봇 API 호출 시 401 에러 대신 500 에러 발생)

## 🔍 재현 방법
1. 
2. 
3. 

## 💡 예상되는 정상 동작
- 원래 어떻게 동작해야 하는지 작성해 주세요.

## 📋 참고 사항 / 에러 로그
```text
(터미널이나 콘솔 에러 로그를 여기에 붙여넣어 주세요)
````
<!-- SOURCE_END:S10 -->

## 원자료 S11 — `feature_request.md`

원래 배치 대상: `.github/ISSUE_TEMPLATE/feature_request.md`. 이 블록은 보존 자료이며, 실행 시 수정은 C/D 결정표에 열거한 부분만 적용합니다.

<!-- SOURCE_BEGIN:S11 -->
````markdown
---
name: "기능 개발 (Feature)"
about: "새로운 기능 구현을 위한 작업 티켓입니다."
title: "[FEAT] "
labels: "feat"
assignees: ""
---

## 📌 기능 개요
- 구현할 기능에 대한 간략한 설명을 작성해 주세요.
- (예: 데이터 30건 SQLite 적재 스크립트 작성)

## 🛠️ 상세 작업 목록 (Todo)
- [ ] 
- [ ] 
- [ ] 

## 🎯 완료 조건 (Definition of Done)
- [ ] 단위 테스트 또는 정상 동작 확인 완료
- [ ] 100% 한국어 주석 및 상대 경로 준수
````
<!-- SOURCE_END:S11 -->
