# W2W 직접 체험 — 2개 페이지 + AI/규칙 추출 + 이메일 자동화

## 사용자가 직접 검증하는 순서
1. **두 페이지 게시:** 이 폴더의 내용 전체를 개인 GitHub 저장소에 업로드. `Settings → Pages → Deploy from a branch → main → / (root)` 설정. `minutes/`와 `actions/`를 각각 엽니다. W40~W45 초기 상태이며 W46는 없습니다.
2. **W46 회의록 추가:** `W46_추가테스트/2026-W46.html`을 GitHub 웹의 `minutes/meetings/2026-W46.html` 경로에 업로드하고 Commit. 실제 확인할 대상은 `minutes/` 회의록 목록입니다.
3. **Action Item 자동 반영 확인:** `Actions → 회의록 자동 분석 및 Action Item 반영` 실행이 성공했는지 보고, `actions/` 페이지 새로고침 → 발생 주차 `W46` 필터 선택. 초기 8개 후보에서 W46 신규 3개를 포함해 11개가 예상됩니다(규칙 기반 모드). **AI를 사용하면 모델이 뽑는 후보 수는 달라질 수 있습니다.**
4. **실제 메일 수신 체험:** 먼저 아래 SMTP Secrets 등록. `Actions → W2W 테스트 및 주간 메일 발송 → Run workflow` 실행. GitHub Actions의 성공 로그를 확인하고 등록한 수신 메일함에서 `[W2W 테스트] W46 Action Item 현황` 메일을 확인합니다.
5. **예약 발송:** 위에서 수동 발송을 확인한 후에도 동일한 Workflow가 매주 월요일 오전 9시 10분(한국시간)에 실행을 *시도*합니다. GitHub의 예약 작업은 지연되거나 실행이 누락될 수 있어, 중요한 업무에 사용하려면 모니터링이 필요합니다.

## 최초 1회 설정
- `Settings → Actions → General → Workflow permissions`: JSON을 Commit하는 추출 Workflow에 **Read and write permissions** 필요(브랜치 보호 정책도 점검).
- `Settings → Secrets and variables → Actions → Repository secrets`:
  - `SMTP_HOST`: Gmail 테스트 시 `smtp.gmail.com`
  - `SMTP_PORT`: Gmail 테스트 시 `465`
  - `SMTP_USER`: 발신 개인 Gmail 주소
  - `SMTP_PASSWORD`: Gmail 앱 비밀번호(일반 Google 계정 비밀번호 아님). Google 2단계 인증과 앱 비밀번호 사용 가능 여부 확인. 사용할 수 없다면 승인된 SMTP 서비스로 설정.
  - `MAIL_TO`: 테스트 메일 수신 주소(여러 명은 쉼표 구분). 처음에는 본인 메일만 권장.
- 선택사항: `Repository variables`에 `W2W_ACTIONS_URL` = 실제 `https://.../actions/` 페이지 주소.
- **실제 Gemini 분석을 테스트하려면** `GEMINI_API_KEY`를 Secret에 추가합니다. 없으면 샘플 HTML의 명시적 구조(`li.action`)에서 과제를 추출하는 규칙 기반 테스트로 동작합니다. 키가 없는 테스트를 AI 분석 성공으로 오해하지 마세요.

## 주의
- 개인 GitHub에는 가상 회의록만 업로드. 실제 회사 회의록, 고객/영업정보, 회사 메일 비밀번호 업로드 금지.
- 이 버전은 **'회의록 추가 → 자동 후보 생성 → 수동 테스트메일 수신'** 검증용. 현재 담당자 공동 편집이나 관리자 권한 인증은 구현되어 있지 않습니다.
- 추출 결과는 관리자 확정 전 후보입니다. 메일도 후보를 '확정 과제'라고 표시하지 않습니다.
- `.github` 숨김 폴더까지 업로드하세요. ZIP 자체를 GitHub에 올리면 실행되지 않습니다.
- 메일 계정 인증정보를 `index.html`, `scripts/`, JSON 등에 입력하지 마세요. GitHub Secrets에서만 설정합니다.
