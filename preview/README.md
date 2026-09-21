# 정적 UI 시연

저장소 루트에서 `node scripts/build_frontend_preview.mjs`를 실행하면 GitHub Pages에 올릴 `preview-dist/`가 생성됩니다. Pages에는 이 디렉터리의 **내용**을 루트로 게시합니다. `.nojekyll`, `index.html`, `static/`, `preview-demo.css`가 포함됩니다.

이 빌드는 기존 `static/` 화면을 복사해 브라우저 전용 데모 API와 데모 인증 모듈로 교체합니다. 공개 페이지에는 자격증명 입력 폼이 없고, **데모로 시작** 버튼만 있습니다. 요청을 외부로 보내지 않도록 `connect-src 'none'`을 적용합니다. 질문과 답변은 현재 브라우저 탭의 `sessionStorage`에만 남고, **시연 초기화** 또는 **데모 종료**로 지울 수 있습니다. 실제 AI, 계정, 서버, 영구 데이터베이스는 연결되지 않습니다.

실제 서비스의 기준 구현은 저장소 루트의 FastAPI와 원본 `static/`입니다. 이 시연 빌드는 프론트 레이아웃과 채팅 동작을 공개 URL에서 확인하기 위한 별도 산출물입니다.
