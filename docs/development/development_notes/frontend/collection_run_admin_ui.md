# Frontend CollectionRun Admin UI Forest 개발 기록

## 작업 정보

- 작업일: 2026-08-11
- 담당 영역: Frontend
- 상태: in-progress
- 브랜치: `feature/frontend/bookmarks-calendar-admin`
- 관련 계획:
  [CollectionRun Admin UI Forest 개발 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- 현재 Slice: FE3-00 completed

## 목적

관리자 CollectionRun UI Forest(FE3)의 DTO·Mock·라우트 shell 기준선(FE3-00)을
구현한다.

## Forest 범위

이 기록은 Frontend 03 Slice 구현·검증 결과를 누적한다. W4-G0 승인 전
admin API path·DTO는 proposal로 문서화한다.

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| FE3-00 | completed | Admin DTO·Mock·`/admin` shell·contract tests |
| FE3-01 | pending | PIN login·session UI |
| FE3-02 | pending | 실행 기록 목록·필터 |

## 구현 내용

### FE3-00 — Admin DTO·라우팅·Mock 계약

- `frontend/src/types/adminSession.ts`
  - W4-G0 proposal `POST /api/v1/admin/session`
  - PIN은 JSON body only (URL query 금지)
- `frontend/src/types/collectionRun.ts`
  - list item vs detail DTO 분리 (`CollectionRunListItemDto` /
    `CollectionRunDetailDto`)
  - list envelope `page`·`size`·`pages`·`total`
  - manual trigger `POST /api/v1/admin/collection-runs` (FE3-04 선행 타입)
- `frontend/src/utils/adminApiErrors.ts`
  - `error.message`(session) · `detail`(protected route) 파싱
- `frontend/src/api/adminRequest.ts`
  - query `size`·`start_date`/`end_date`·`buildAdminAuthorizationHeader`
- `frontend/src/api/adminSession.ts`, `frontend/src/api/collectionRuns.ts`
  - `apiClient` + Real API path; `accessToken` 옵션(FE3-01 전 수동 전달)
- `frontend/tests/admin.contract.test.ts`, `adminApiErrors.test.ts`

### FE3-00 — Real API 정합 (2026-08-11)

Backend 04·05 구현 기준(`origin/feature/backend/collection-run-admin-api`,
`docs/api/admin_access.md`, `docs/api/admin_collection_runs.md`)에 맞춰
프론트 계약을 정렬했다.

| 영역 | 이전(FE3-00 초안) | Real API 기준 |
| --- | --- | --- |
| Session `token_type` | `Bearer` | `bearer` |
| List query | `limit`, `started_from/to` | `size`, `start_date`/`end_date`, `run_type`, `trigger_type` |
| List response | `limit` | `size`, `pages` |
| List item fields | full counts | subset + `is_stale` |
| Detail fields | DB counts only | + `duplicate_count`, `rejected_count` |
| Manual run path | `/collection-runs/manual` | `POST /collection-runs` |
| Auth header | 없음 | `Authorization: Bearer` (client 옵션) |
| Error body | `detail` only | session `error.message`, protected `detail` |

**로컬 Real API probe (`http://127.0.0.1:8000`, 2026-08-11):**

- OpenAPI paths: health·policies only — **admin endpoint 없음**
- `POST /api/v1/admin/session` → HTTP 404
- `GET /api/v1/admin/collection-runs` → HTTP 404

→ 현재 워크스페이스 Backend에는 admin Forest가 merge되지 않았다. Real E2E는
`feature/backend/collection-run-admin-api`(또는 develop merge 후) Backend
재기동 + `VITE_USE_MOCK=false` `VITE_API_BASE_URL=http://127.0.0.1:8000`
환경에서 FE3-05·FE3-01 이후 재검증.

## 설계 결정

| 항목 | 결정 | 근거 |
| --- | --- | --- |
| API prefix | `/api/v1/admin/*` | 기존 Policy API prefix 일관 |
| Collection run path | `/api/v1/admin/collection-runs` | Backend 05 OpenAPI |
| List vs detail DTO | list subset / detail full counts | Backend `AdminItem` vs `AdminDetail` |
| Error parsing | dual `error.message` + `detail` | admin_access.md 표준 |
| Session storage | FE3-00에서 미구현 | FE3-01; token 영구 localStorage 금지 |

## 주요 변경 파일

- `frontend/src/types/adminSession.ts`
- `frontend/src/types/collectionRun.ts`
- `frontend/src/api/adminRequest.ts`
- `frontend/src/api/adminApiError.ts`
- `frontend/src/api/adminSession.ts`
- `frontend/src/api/collectionRuns.ts`
- `frontend/src/mocks/adminSessionHandlers.ts`
- `frontend/src/mocks/collectionRunFixtures.ts`
- `frontend/src/mocks/collectionRunHandlers.ts`
- `frontend/src/layouts/AdminShellLayout.tsx`
- `frontend/src/pages/admin/AdminLoginPage.tsx`
- `frontend/src/pages/admin/CollectionRunDetailPage.tsx`
- `frontend/src/App.tsx`
- `frontend/src/styles/theme.css`
- `frontend/tests/admin.contract.test.ts`
- `frontend/tests/adminApiErrors.test.ts`
- `frontend/src/utils/adminApiErrors.ts`

## 검증 결과

```text
cd frontend && npm test   — passed (81 unit tests)
cd frontend && npm run lint — passed
cd frontend && npm run build — passed
python3 scripts/validate_docs.py — passed
curl Real API probe (127.0.0.1:8000) — admin paths 404 (Backend admin 미merge)
```

Browser·Playwright admin flow는 FE3-05·FE3-07 범위이며 FE3-00에서 실행하지
않았다.

## 남은 작업

- FE3-01: PIN login·session store·protected route
- FE3-02~03: list·detail UI
- Backend admin Forest를 로컬 `:8000`에 merge·재기동 후 Real API smoke (FE3-05)

## 관련 문서

- [CollectionRun Admin UI 계획](../../develop_plan/frontend/03_collection_run_admin_ui.md)
- [Backend Admin Access Control](../../develop_plan/backend/04_admin_access_control.md)
- [Backend CollectionRun Admin API](../../develop_plan/backend/05_collection_run_admin_api.md)
- [CollectionRun DB 계약](../../../architecture/collection_run_database.md)
