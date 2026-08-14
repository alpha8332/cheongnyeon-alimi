# Frontend

React·TypeScript·Vite 기반 사용자 및 관리자 화면이다. 정책 화면은
[`Policy API 계약`](../docs/api/policies.md)의 공개 `PolicyDto`와
`PolicyListResponse`를 소비한다.

## 로컬 실행

Node.js는 React Router v8이 요구하는 `>=22.22.0` 범위를 사용한다.

```powershell
cd frontend
npm ci
npm run dev
```

개발 서버는 Backend 기본 CORS 허용 origin과 맞춘
`http://127.0.0.1:3000`에서 실행한다.

기본값은 canonical Seed를 공개 Policy DTO로 변환한 Mock을 사용한다. 실제
Backend API를 사용할 때는 다음 환경변수를 설정한다.

```powershell
$env:VITE_USE_MOCK = 'false'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run dev
```

Mock과 실제 API는 모두 `/api/v1/policies`의 pagination, 숫자 `id` 상세와
partial opt-in 계약을 따른다. 기본 목록은 valid만 표시하며 목록 화면의
“정보가 일부 누락된 정책 포함”을 선택하면 목록·상세에
`include_partial=true`를 사용한다.

관리자 CollectionRun UI(FE3)도 동일한 Mock 토글을 사용한다. 기본값은 Mock
admin session·run list·trigger이며, Backend Admin API(Backend 04·05) merge
후 아래처럼 Real API 모드로 전환한다.

```powershell
$env:VITE_USE_MOCK = 'false'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run dev
```

## E2E (Playwright)

Chromium 설치(최초 1회):

```powershell
npm run test:e2e:install
```

Mock-first admin flow(FE3-05):

```powershell
npm run test:e2e -- e2e/admin-collection-run.spec.ts
```

Week 4 Frontend regression matrix (FE9-02, W4-F10·W4-I3 Mock-first):

```powershell
npm run test:e2e -- e2e/week4-regression.spec.ts
```

Real API 수동 Browser 검증 절차는
[Frontend Real API 수동 테스트 가이드](../docs/development/frontend_real_api_manual_testing_guide.md)를
참고한다.

Real API admin golden은 Backend admin path가 `:8000`에 노출된 환경에서만
실행한다.

```powershell
$env:VITE_USE_MOCK = 'false'
$env:VITE_API_BASE_URL = 'http://127.0.0.1:8000'
npm run test:e2e -- e2e/admin-collection-run.spec.ts
```

## 검증

```powershell
npm test
npm run lint
npm run build
```

`npm test`는 추가 테스트 라이브러리 없이 TypeScript 컴파일러와 Node 내장
테스트 러너를 사용해 canonical Seed → 공개 DTO 변환, provenance·invalid
비노출, pagination, 필터, 숫자 ID와 partial opt-in을 검증한다.
