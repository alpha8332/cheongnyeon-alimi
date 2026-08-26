# Frontend 실제 API 수동 테스트

## 목적

Mock이 아닌 `run_docker.bat`의 FastAPI·PostgreSQL과 React 화면을 함께 검증한다.
일반 사용자와 관리자 흐름은 현재 공개 dataset과 실제 API 응답을 기준으로 본다.

## 준비

```powershell
.\run_docker.bat -NoBrowser
```

- Frontend: `http://127.0.0.1:3000`
- Backend health: `http://127.0.0.1:8000/health`
- `.env.compose`에 생성된 관리자 PIN은 화면·문서·로그에 복사하지 않는다.
- clean-room이 필요하면 정확한 Compose project를 확인하고 별도 Volume을 사용한다.

## 사용자 흐름

1. 홈 예시 검색을 눌러 실제 결과가 열리는지 확인한다.
2. 양산·경남·인천·부산·제주 등 지역과 전국 정책이 계층 규칙대로 보이는지
   확인한다.
3. 검색어, 지역·연령·복수 분야·상태, 정렬과 페이지 이동 후 URL 조건이
   유지되는지 확인한다.
4. 정책 상세에서 목록과 같은 제목·기관·기간·분야, 미확정 안내와 공식 원문
   링크를 확인한다.
5. 프로필에 지역·연령·복수 관심 분야를 저장하고 홈·맞춤 추천의 순위와 이유를
   확인한다.
6. 즐겨찾기, 폴더, D-Day, 달력, 내부 알림과 `.ics` 다운로드를 확인한다.
7. 390×844 viewport에서 가로 overflow, focus, label과 키보드 이동을 확인한다.

## 관리자 흐름

1. 미인증 상태에서 `/admin`, `/admin/collectors`, `/admin/runs`가 로그인으로
   보호되는지 확인한다.
2. 올바른 PIN과 잘못된 PIN, 반복 실패 잠금, 로그아웃과 새로고침 세션 경계를
   확인한다.
3. 대시보드, 수집기 11개, queue·worker·credential boolean과 공개 정책 수를
   확인한다.
4. CollectionRun 목록·상세·필터·페이지·stale 표시를 확인한다.
5. 정책 데이터, 품질과 구조화 로그가 읽기 전용이며 비밀정보를 노출하지 않는지
   확인한다.
6. PIN 변경 후 기존 세션이 무효화되는지 확인한다. 분실 복구는
   `reset_admin_pin.bat` 문서를 따르고 DB 보존 여부를 대조한다.

수동 수집은 외부 요청과 DB 변경을 만들 수 있으므로 별도 검증 환경과 승인된
Source에서만 실행한다. 사용자 화면 검증에 수동 수집은 필요하지 않다.

## 자동 회귀

```powershell
cd frontend
npm test
npm run lint
npm run build
npm run test:e2e
```

실제 API E2E는 `VITE_USE_MOCK=false`와 실행 중인 Docker Backend가 필요할 수
있다. 환경 조건 때문에 skip된 테스트를 통과로 계산하지 않는다.

## 기록

결함은 화면 URL, 재현 절차, 기대·실제 결과, 안전한 스크린샷 또는 응답 집계와
회귀 방법을 남긴다. PIN, token, API key, DB URL과 정책 Raw 본문은 증거에
포함하지 않는다.
