# Frontend React Router Advisory Review Forest 개발 기록

## 작업 정보

- 작업 일자: 2026-07-30
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `fix/backend/week2-hardening`
- 관련 계획:
  [React Router Advisory Review Forest 개발 계획](../../develop_plan/frontend/02_react_router_advisory.md)
- 현재 Slice: F0 completed

## 목적

현재 lockfile에서 보고되는 React Router RSC advisory를 재현하고, 취약
package 경로와 현재 client-only 앱의 실제 실행 경로를 구분한다.

## Forest 범위

F0에서는 공식 advisory와 package metadata, 현재 설치 트리와 Frontend
소스를 확인한다. 호환 버전 결정, manifest·lockfile 변경과 회귀 검증은
각각 후속 F1~F3 범위다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| F0 | completed | high 2건 재현, package 경로와 현재 앱의 RSC 도달 불가 확인 |
| F1 | completed | `react-router@8.3.0` package 교체와 공식 import migration 결정 |
| F2 | draft | 의존성 또는 보호 조치 반영 예정 |
| F3 | draft | 자동·브라우저 회귀와 최종 문서 동기화 예정 |

## 구현 내용

### F0 - Advisory 재현

- 로컬 실행 환경은 Node.js 24.18.0, npm 11.16.0이다. Node.js는 PATH에
  등록되지 않았지만 `C:\Program Files\nodejs`의 기존 설치를 사용했다.
- 현재 직접 의존성은 `react-router-dom@7.18.1`이고, 이 package가
  `react-router@7.18.1`을 정확히 전이 의존한다.
- `npm audit --json`과 `npm audit --omit=dev --json`은 모두 high 2건을
  보고했다. 하나는 전이 의존성 `react-router`, 다른 하나는 그 영향을 받는
  직접 의존성 `react-router-dom` 항목이다.
- 두 항목의 실제 원인은 하나의 GitHub-reviewed advisory
  [`GHSA-qwww-vcr4-c8h2`](https://github.com/advisories/GHSA-qwww-vcr4-c8h2)다.
  확인 시점의 영향 범위는 `react-router >=7.12.0 <8.3.0`, patched
  version은 8.3.0이며, 공식 설명은 unstable RSC API를 사용하는
  애플리케이션만 영향받는다고 명시한다.
- npm의 자동 수정 제안은 `react-router-dom@7.11.0` downgrade이고
  `isSemVerMajor: true`로 표시된다. F0에서는 제안의 안전성이나 채택 여부를
  결정하지 않고 F1로 넘겼다.

### F0 - 현재 앱 도달 가능성

- 앱은 Vite client-only entry에서 `createBrowserRouter`와
  `RouterProvider`를 사용한다.
- `frontend/src`, manifest와 Vite 설정에는 unstable RSC API, RSC server
  entry, server action, `react-server` condition 또는 route
  `action`·`loader`가 없다.
- 설치된 `react-router` package 자체에는 RSC export가 포함되지만 현재 앱은
  해당 export나 실행 조건을 참조하지 않는다.
- 따라서 취약 버전은 설치되어 audit 대상이지만, 현재 배포 구성과 코드
  경로에서는 advisory가 요구하는 unstable RSC action 실행 경로에 도달할 수
  없다. RSC mode 또는 server action을 도입하면 이 판정을 다시 검토해야 한다.

### F1 - 호환 버전 결정

- 공식 v8 migration guide와 npm registry를 2026-07-30에 다시 확인했다.
  `react-router@8.3.0`은 배포되어 있지만 `react-router-dom@8.3.0`은
  존재하지 않으며 `react-router-dom` 최신 dist-tag는 7.18.2다.
- 이는 registry 누락이 아니라 v8의 의도된 package 경계 변경이다. 공식
  guide는 `react-router-dom` re-export package가 v8에서 제거됐으며,
  일반 API는 `react-router`, DOM 전용 `RouterProvider`는
  `react-router/dom`에서 import하도록 안내한다.
- v8 최소 요건은 Node.js 22.22 이상과 React·React DOM 19.2.7 이상이다.
  현재 검증 환경의 Node.js 24.18.0, manifest의 React·React DOM 19.2.7,
  Vite 8.x는 이 기준을 충족한다.
- 현재 사용하는 `createBrowserRouter`, `Link`, `Outlet`, `useNavigate`,
  `useParams`, `useRouteError`, `useSearchParams`는 v8 API에 유지된다.
  `RouterProvider`만 공식 DOM export 경로로 변경하면 된다.
- 현재 앱에는 v8에서 변경된 `useMatches().data`, Framework mode,
  loader·action context, Cloudflare adapter 사용이 없어 해당 breaking
  change의 적용 대상이 아니다.

F1 결정은 `react-router@8.3.0`으로 upgrade하는 것이다. F2에서
`react-router-dom`을 제거하고 `react-router@8.3.0`을 직접 의존성으로
추가하며, source import와 lockfile을 함께 변경한다. v8이 요구하는 Node.js
최소 버전 22.22도 Frontend 실행 문서에 반영한다.

다음 대안은 선택하지 않았다.

- `react-router-dom@7.11.0` downgrade: advisory 영향 범위 전이지만 npm이
  major 성격의 변경으로 판정하고 최신 v7 수정에서 멀어지므로 선택하지 않음
- 한시적 위험 수용: 현재 RSC 경로는 도달 불가지만 audit high를 계속
  유지하며 안전한 공식 upgrade 경로가 존재하므로 선택하지 않음

## 주요 변경 파일

- `docs/development/develop_plan/frontend/02_react_router_advisory.md`
- `docs/development/development_notes/frontend/react_router_advisory.md`
- `docs/development/develop_plan/README.md`
- `docs/development/development_notes/README.md`
- `docs/index.md`

F0는 조사·문서화 Slice이므로 Frontend 코드, `package.json`과 lockfile은
변경하지 않았다.

## 설계 결정

- audit의 package 설치 여부와 실제 취약 실행 경로를 별도로 기록한다.
- 현재 도달 불가 판정만으로 advisory를 종료하거나 위험 수용하지 않는다.
- npm의 downgrade 제안을 자동 적용하지 않고 공식 patched version인
  `react-router@8.3.0`으로 전환한다.
- v8 package 경계 변경에 필요한 import 수정만 허용하고 Router 구조는
  재작성하지 않는다.
- Node.js 최소 버전 변경은 Frontend 실행 계약에 해당하므로 F2에서
  manifest·lockfile과 실행 문서를 함께 동기화한다.

## 검증 결과

- `npm ls react-router react-router-dom --all`: 통과. 직접
  `react-router-dom@7.18.1` → 전이 `react-router@7.18.1` 경로 확인
- `npm explain react-router`: 통과. 동일 전이 경로 확인
- `npm audit --json`: 예상된 non-zero 종료, high 2건 재현
- `npm audit --omit=dev --json`: 예상된 non-zero 종료, production
  의존성에서도 동일 high 2건 재현
- `npm view react-router@7.18.1`, `react-router@8.3.0`,
  `react-router-dom@7.18.1`: package version·의존성·engine metadata 확인
- Frontend source·manifest·Vite 설정 정적 검색: RSC·server action 사용
  없음
- F1 `npm view`: `react-router@8.3.0`의 Node·React 최소 버전과 exports,
  `react-router-dom@8.3.0` 미배포, 최신 v7 dist-tag 7.18.2 확인
- F1 source 정적 검색: Router import 10개와 v8의 다른 breaking API
  미사용 확인
- `npm test`: 소비 계약 테스트 7건 통과
- `npm run lint`: 오류·경고 없이 통과
- `npm run build`: TypeScript와 Vite production build 통과
- Vite 개발 서버 `http://127.0.0.1:3000/`: HTTP 200과 client entry HTML
  응답 확인
- 브라우저 직접 회귀: 현재 실행 환경에 제어 가능한 브라우저가 없어 미실행.
  공식 제품 경계상 Codex CLI·VS Code Codex에서는 Browser를 사용할 수
  없고, 현재 브라우저 런타임의 사용 가능 목록도 비어 있음을 확인했다.
  성공으로 처리하지 않는다.
- `python scripts/validate_docs.py`: 통과
- `git diff --check`: 통과

F0 상태에서 자동 테스트·lint·build는 기준선으로 통과했지만, F2에서
의존성이나 보호 조치를 반영한 뒤 F3에서 다시 실행해야 한다. F3의 자동
검증과 빌드가 끝나면 ChatGPT 데스크톱 앱의 Browser에서 직접 회귀를
수행하고, 그 결과까지 기록한 뒤 F3를 완료 처리한다.

## 남은 작업

- F2에서 `react-router-dom`을 `react-router@8.3.0`으로 교체하고
  manifest·lockfile·source import·Node.js 최소 버전 문서를 동기화한다.
- F3에서 `npm ci`, test, lint와 build를 먼저 수행한 뒤 ChatGPT 데스크톱
  앱의 Browser에서 `http://localhost:3000` 주요 route 회귀를 수행한다.
- RSC mode, RSC server entry 또는 server action 도입 시 현재 도달 불가
  판정을 즉시 재검토한다.
