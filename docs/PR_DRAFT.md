# 오프라인 PR 본문 초안

실제 평가 저장소, base 브랜치, Issue, 리뷰어가 아직 확정되지 않았으므로 이 파일은 로컬 초안입니다. 원격 push·PR 생성·merge는 수행하지 않았고, 존재하지 않는 PR URL이나 Issue 번호를 만들지 않습니다.

## 제목 초안

`feat: B7-1 AI Assistant 풀스택 기준 구현`

## 대상

- source 후보: `feat/fullstack-lee`
- base: 팀 평가 저장소에서 확인 필요
- 비교 시작 SHA: `6b2ff28ab3947884b5ffe6f54f3bf28b60107d42`
- 연결 Issue: 없음 / 팀 확인 필요

## 변경 요약

- FastAPI 기동, SQLite WAL 스키마와 사용자별 기록
- 가입·로그인, bcrypt_sha256 비밀번호 해시, HS256 JWT 보호 API
- 최근 5쌍 문맥, Mock/real AI 모드, HTTPX 실제 adapter와 8초 제한
- 실패 rollback·504/500 복구와 여섯 운영 로그 이벤트
- `static/` 안의 독립 Vanilla HTML/CSS/JS 로그인·채팅·기록 UI
- API/OpenAPI/프론트 계약, 브라우저·모바일·IME·세션 전환 회귀
- DB/smoke/Git 감사 도구와 Nginx/systemd 배포 템플릿·승인 경계

## 검증 결과

- Python 전체 테스트: 새 가상환경 205 passed, dependency warning 2건
- Node 프론트 테스트: 18 passed
- 로컬 브라우저: 가입 → 로그인 → 채팅 → 로그아웃 → 재로그인 기록 복원 PASS
- 실제 SQLite INSERT/COMMIT 실패: rollback·0행·후속 정상 요청 PASS
- 실제 AI: 미실행, 승인된 공급자·키·호출 범위 필요
- 외부 URL/AWS: 미실행, 계정·비용·보안그룹·TLS 승인 필요

## 리뷰가 필요한 결정

- C06: 팀 기존 순수 bcrypt와 개인 신규 DB의 bcrypt_sha256 포맷 합의
- C10: systemd 절대 배포 경로와 실제 운영 계정/디렉터리
- C11: 원안 HTTP 80 시연과 HTTPS 443/TLS 전환
- C13/C15: AWS 비용 조건과 실제 코디세이 provider URL·model·권한
- 개인 `static/`을 추후 팀 저장소로 옮길 때 다섯 API 계약과 같은-origin 경계 유지
- 팀원별 실제 SHA 10개 이상, PR 리뷰·merge, 최종 브랜치 포함 여부

## 확인 체크리스트

- [x] 로컬 Mock 풀스택과 자동 회귀
- [x] 비밀값·DB·로그 Git 제외 및 HTTP 비노출
- [x] 개인 기능 브랜치와 실제 작성자 이력 감사
- [ ] 승인된 실제 AI 두 턴
- [ ] 승인된 공개 URL의 다른 네트워크 검증과 재시작 보존
- [ ] 팀 평가 저장소의 실제 PR 리뷰·merge
- [ ] 학습자의 여섯 흐름 직접 설명 확인

## 승인 후에만 할 일

팀이 평가 remote/base와 merge 방식을 확정한 뒤 현재 diff·작성자·테스트를 다시 감사하고 push/PR을 생성합니다. squash가 강제되면 개인 커밋 증빙 보존 방식을 먼저 합의합니다. 실제 PR URL과 리뷰·merge 결과는 생성 후에만 `docs/CONTRIBUTIONS.md`에 기록합니다.
