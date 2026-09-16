# 구현 및 미션 검증 상태

최종 갱신: 2026-09-16 / R02 서버·DB 기반 검증

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
| M01 | 같은 화면 질문·응답 | NOT_RUN | 구현 전 |
| M02 | 회원가입·로그인 | NOT_RUN | 구현 전 |
| M03 | 인증별 접근제어 | NOT_RUN | 구현 전 |
| M04 | 실제 AI API 호출 | NOT_RUN | 외부 조건은 상단 REAL_AI에 별도 기록; 공급자·키·호출 승인 필요 |
| M05 | 최근 사용자 문맥 | NOT_RUN | 구현 전 |
| M06 | 대화 DB 누적·영속 | NOT_RUN | 구현 전 |
| M07 | 사용자별 기록 조회 | NOT_RUN | 구현 전 |
| M08 | 요청·AI·DB 성공/실패 로그 | NOT_RUN | 구현 전 |
| M09 | AI 실패/timeout 복구 | NOT_RUN | 구현 전 |
| M10 | 입력 검증 | NOT_RUN | 구현 전 |
| M11 | 외부 URL | NOT_RUN | 외부 조건은 상단 PUBLIC_URL에 별도 기록; 배포·공개 승인 필요 |
| M12 | 필수 기술 문서 | NOT_RUN | 초기 문서만 존재; 실제 결과 반영 필요 |
| M13 | 비밀값 환경변수·Git 제외 | NOT_RUN | ignore 정적 확인과 추적 검사 예정 |
| M14 | 브랜치 전략·작업 흔적 | NOT_RUN | 기능 브랜치 생성; 실제 이력 누적 필요 |
| M15 | 실제 PR merge | NOT_RUN | 원격 작업 별도 승인 필요 |
| M16 | 팀원별 유의미한 커밋 10개 | NOT_RUN | 팀 평가 저장소 이력 미확인 |
| M17 | 역할·이력 일치 | NOT_RUN | 실제 팀 SHA/PR 미확인 |
| M18 | Python/FastAPI/SQLite | NOT_RUN | 의존성·기동 검증 전 |
| M19 | GitHub 저장소 링크 | NOT_RUN | 원격 주소 확인, 제출 대상 확인 필요 |
| M20 | DB 확인 가이드 | NOT_RUN | 도구 구현 전 |
| M21 | 여섯 흐름 개인 설명 | NOT_RUN | 실제 구현·직접 확인 후 작성 |

## T01~T33 테스트 추적표

아래 상태는 테스트 파일 존재가 아니라 실제 실행 결과를 뜻합니다.

| ID | 상태 | 비고 |
|---|---|---|
| T01 | NOT_RUN | 기동·정적·health |
| T02 | PASS | 가입 201과 중복 400 응답·DB 저장 검증 |
| T03 | PASS | 공백/2자/51자/trim/내부공백·대소문자 보존 검증 |
| T04 | PASS | 3/4/100/101자·공백·100자 한글 경계 검증 |
| T05 | PASS | 100자 ASCII·한글과 72바이트 이후 차이 검증 |
| T06 | NOT_RUN | 로그인 |
| T07 | NOT_RUN | JWT 위조·만료·claims |
| T08 | NOT_RUN | 보호 API 인증 |
| T09 | NOT_RUN | JSON·구형 key 거부 |
| T10 | NOT_RUN | Mock 채팅·DB |
| T11 | NOT_RUN | 질문 길이·공백·emoji |
| T12 | NOT_RUN | 자료형·잘못된 JSON |
| T13 | NOT_RUN | 기록 배열·정렬·필드 |
| T14 | NOT_RUN | 사용자 격리 |
| T15 | NOT_RUN | DB 재기동 보존 |
| T16 | NOT_RUN | 최근 5쌍 문맥 |
| T17 | NOT_RUN | 실제 adapter 가짜 transport |
| T18 | NOT_RUN | timeout·복구 |
| T19 | NOT_RUN | 공급자·응답 실패 |
| T20 | NOT_RUN | DB 실패·rollback |
| T21 | NOT_RUN | 6개 운영 이벤트·비밀 비노출 |
| T22 | NOT_RUN | Git 제외·정적 비노출 |
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
