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
| R03 | Cerhovah | 회원가입과 비밀번호 검증 | 다음 기록에서 갱신 | `pytest tests/test_auth.py -q` → 22 passed | 없음 | 로컬 기능 브랜치 | 예정 |

## 팀 역할과 실제 이력

| 팀원 | 첨부 계획의 예정 영역 | 실제 SHA 수 | PR/최종 브랜치 증거 | 상태 |
|---|---|---:|---|---|
| 고준석 | 인증 / PM | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |
| 박범규 | 백엔드 / DB | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |
| 이준혁 | 프론트 UI/UX | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |
| 차종민 | AI 파이프라인 | 미확인 | 미확인 | NEEDS_TEAM_REVIEW |

개인 기준 구현의 커밋 수는 팀원 4명 각각의 10개 요건이나 실제 PR merge를 대체하지 않습니다. 원격 검증은 별도 승인 후 평가 대상 저장소·기준 SHA·최종 브랜치를 확정하여 수행합니다.
