# 실제 기여 및 협업 증빙

## 판정 범위

- 저장소: `https://github.com/Cerhovah/Codyssey_Mission_B7-1`
- 기준 커밋: `6b2ff28ab3947884b5ffe6f54f3bf28b60107d42`
- 로컬 작업 브랜치: `feat/fullstack-lee`
- 확인된 작성자: `Cerhovah <ljh951206@gmail.com>`
- 팀 평가 대상 브랜치와 PR 인정 범위: 미확인

현재 파일은 계획이 아니라 실제 SHA와 검증 결과를 누적하는 증빙입니다. 다른 팀원 명의나 존재하지 않는 PR URL을 만들지 않습니다. 새 커밋 자신의 SHA는 다음 커밋 또는 최종 감사 결과에서 기록합니다.

## 개인 작업 기록

| R | 작성자 | 작업 | SHA | 검증 명령·결과 | PR URL | 대상 브랜치 반영 | 직접 설명 |
|---|---|---|---|---|---|---|---|
| R01 | Cerhovah | 계약·ignore·증빙 기반 구성 | `617cff6` | ignore 15/15·추적 가능 예시·비밀 패턴 검사 | 없음 | 로컬 기능 브랜치 | 예정 |
| R01 보정 | Cerhovah | S02/S04/S05/S06/S07/S09~S11 원문과 조정 복원 | `67bcb89` | 원문 prefix·모델·C05 검사, 11개 원문 해시 일치 | 없음 | 로컬 기능 브랜치 | 예정 |
| R02 | Cerhovah | FastAPI 기동과 SQLite 초기화 | `bc1091e` | `pytest tests/test_bootstrap.py -q` → 8 passed | 없음 | 로컬 기능 브랜치 | 예정 |
| R03 | Cerhovah | 회원가입과 비밀번호 검증 | `c637a8c` | `pytest tests/test_auth.py -q` → 22 passed | 없음 | 로컬 기능 브랜치 | 예정 |
| R03 보강 | Cerhovah | 인증 저장 트랜잭션·해시 장애·공통 오류 경계 강화 | `02e40a3` | 전체 `pytest` → 34 passed | 없음 | 로컬 기능 브랜치 | 예정 |
| R04 | Cerhovah | 로그인 JWT와 보호 API 인증 | `d8174f0` | 전체 `pytest` → 55 passed | 없음 | 로컬 기능 브랜치 | 예정 |
| R05 | Cerhovah | 최근 문맥 Mock 채팅·저장·기록·표준 로그 | `2d0b576` | 전체 `pytest` → 93 passed | 없음 | 로컬 기능 브랜치 | 예정 |
| R06 | Cerhovah | 채팅 화면 기본 구조와 상태 영역 | `3ad456c` | frontend/bootstrap 17 passed, 전체 101 passed | 없음 | 로컬 기능 브랜치 | 예정 |
| R07 | Cerhovah | 로그인 모달·토큰 저장·API 통신 경계 | `262319d` | frontend 14 passed, 전체 107 passed, JS 구문 검사 PASS | 없음 | 로컬 기능 브랜치 | 예정 |
| R08 | Cerhovah | 회원가입 모달·검증 오류·로그인 전환 | `5515811` | frontend/auth 44 passed, 전체 111 passed, JS 구문 검사 PASS | 없음 | 로컬 기능 브랜치 | 예정 |
| R09 | Cerhovah | 질문 전송·안전한 메시지 렌더링·첫 브라우저 E2E | `cacad06` | frontend/chat 59 passed, 전체 115 passed, 실제 브라우저·DB·로그 확인 | 없음 | 로컬 기능 브랜치 | 예정 |
| R10 | Cerhovah | 내 대화 이력 조회·빈 목록·새로고침 복원 | `4c15d37` | frontend/chat 62 passed, 전체 118 passed, 브라우저 재로그인·새로고침 확인 | 없음 | 로컬 기능 브랜치 | 예정 |
| R11 | Cerhovah | 공통 API 오류·비JSON·보호 API 401 처리 | `16fe125` | Node API 10 passed, frontend 26 passed, 전체 119 passed, 브라우저 401 확인 | 없음 | 로컬 기능 브랜치 | 예정 |
| R12 | Cerhovah | 로딩 상태·중복 전송 차단·오류 뒤 폼 복구 | `df791be` | Node API 10 passed, frontend 28 passed, 전체 121 passed, 브라우저 504·500·비JSON·복구 확인 | 없음 | 로컬 기능 브랜치 | 예정 |
| R13 | Cerhovah | 로그아웃·사용자 전환·다중 탭 응답 격리 | `db33fd3` | frontend 30 passed, 전체 123 passed, 브라우저 A→B·늦은 401·두 탭 동기화 확인 | 없음 | 로컬 기능 브랜치 | 예정 |
| R14 | Cerhovah | 모바일 입력·키보드·IME·포커스 접근성 | `5d46119` | Node 15 passed, frontend 34 passed, 전체 127 passed, 360×640·XSS·키보드 브라우저 확인 | 없음 | 로컬 기능 브랜치 | 예정 |
| R15 | Cerhovah | 프론트 API·OpenAPI 회귀와 실행·이식 경계 문서 | `6733915` | Node 18 passed, frontend/contract 38 passed, 전체 131 passed, 새 사용자 브라우저 E2E | 없음 | 로컬 기능 브랜치 | 검토용 설명 작성·본인 확인 대기 |
| R15 보강 | Cerhovah | health/login 정확한 200과 문서 endpoint별 계약 검사 | `5885a19` | Node 18 passed, frontend/contract 39 passed, 전체 132 passed | 없음 | 로컬 기능 브랜치 | 검토용 설명 작성·본인 확인 대기 |
| R15 이후 백엔드 보강 | Cerhovah | SQLite PRAGMA 초기화 실패·취소 시 연결 정리 | `daa1592` | bootstrap 12 passed, 전체 135 passed | 없음 | 로컬 기능 브랜치 | 예정 |
| R16 | Cerhovah | lifespan HTTPX 실제 AI adapter·전체 timeout·안전한 오류 분류 | `0d53a87` | AI/bootstrap/chat 92 passed, 전체 178 passed, Node 18 passed, 외부 호출 0회 | 없음 | 로컬 기능 브랜치 | 예정 |
| R17 | Cerhovah | 실제 SQLite INSERT·COMMIT 실패 rollback·로그·복구 검증 | 다음 기록에서 갱신 | DB 실패 2 passed, 전체 180 passed | 없음 | 로컬 기능 브랜치 | 예정 |

## 팀 역할과 실제 이력

| 팀원 | 첨부 계획의 예정 영역 | 실제 SHA 수 | PR/최종 브랜치 증거 | 상태 |
|---|---|---:|---|---|
| 고준석 | 인증 / PM | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |
| 박범규 | 백엔드 / DB | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |
| 이준혁 | 프론트 UI/UX | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |
| 차종민 | AI 파이프라인 | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |

개인 기준 구현의 커밋 수는 팀원 4명 각각의 10개 요건이나 실제 PR merge를 대체하지 않습니다. 원격 검증은 별도 승인 후 평가 대상 저장소·기준 SHA·최종 브랜치를 확정하여 수행합니다.

기준 SHA 이후 본인 로컬 기능 커밋은 R08에서 10개가 되었습니다. 이는 개인 학습 저장소의 작업 이력이며 팀원별 10개 및 팀 PR 병합 증거와 구분합니다.
