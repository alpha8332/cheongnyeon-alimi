# Backend 07 v0.5.0 Backend Stabilization Forest 개발 계획

## 계획 정보

- 번호: Backend 07
- 담당 영역: Backend
- 상태: in-progress
- 현재 단계: 5주차 Slice BE5-01 완결 (W5-B1 인수 검토 중)
- 계획일: `2026-08-17`
- 대상 Release: `v0.5.0`
- 상위 통합 Forest: [Integration 07 Release 2 Feature Acceptance](../integration/07_release_2_feature_acceptance.md)
- 관련 주차 계획: [5주차 상세 실행 계획](../../weekly_plan/week_05_release_2.md)
- 선행 Forest: Backend 01·02·03·04·05·06, Data 03·04·05·06, Integration 05·06·08·09
- 권장 브랜치: `feature/backend/week-05-stabilization`

## 목적

4주차 미드포인트(`W4-G4_MIDPOINT_PASS`, SHA `f0d3dd3`)에서 병합된 백엔드 API, PostgreSQL 데이터베이스 모델, 마이그레이션, 관리자 인증 및 로그 시스템을 실제 환경에서 종합적으로 회귀 검증하고, 5주차 Data 06 적재 신규 정책의 API 노출 대조, 사용성 리뷰어 및 QA 독립 검증에서 발견된 결함을 수정하여 Release 2 (`v0.5.0`) Gate를 안전하게 통과한다.

## 범위

1. **DB 및 마이그레이션 회귀**:
   - Alembic Migration 단일 Head (`20260810_0006`) 적용 및 Rollback 정합성 확인.
   - DB Transaction Rollback 시 자원 격리, 데이터 손실/중복 방지 및 정합성 유지 검증.
2. **사용자 정책 API (Search, Detail, Recommendation) 회귀**:
   - `GET /api/v1/policies` 및 `GET /api/v1/policies/search` 자연어 파서, 지역/연령/카테고리/신청상태 필터, 페이징, 정렬 계약 검증.
   - 정책 상세 자격요건 DTO (`EligibilitySummary`) 및 원문 evidence 출처 정보 응답 확인.
   - 결정적 맞춤 추천 API (`GET /api/v1/recommendations`) 부합도 점수, 사유 코드(Reason Code), 비단정 안내 문구 계약 검증.
3. **관리자 및 수집/로그 API (Admin Access, CollectionRun, Policy Table, Logs) 회귀**:
   - Admin 4자리 PIN 세션 생성 (`POST /api/v1/admin/auth/session`), Rate Limit (`429`), 미인증/권한 부족 (`401`/`403`) Fail-closed 검증.
   - CollectionRun 수동 실행 (`POST /api/v1/admin/collection-runs/trigger`, `202 Accepted`), 이력 목록/상세 및 Stale 상태 판정 검증.
   - 관리자 읽기 전용 정책 데이터 표 목록/상세 API, 페이징 및 Allowlist 정렬 안전성 검증.
   - 관리자 구조화 파일 로그 조회/검색, Correlation ID 추적, 회전 archive 삭제 경로 보안(경로 이탈 차단 Fail-closed) 및 Audit 감사 기록 검증.
4. **오류 응답 계약 & Exception Handling**:
   - Partial/Invalid 데이터 처리 시 `401`, `403`, `404`, `409`, `422`, `500` HTTP 상태 코드 및 표준 Error DTO 응답 일치 확인.
5. **Data 06 신규 정책 수용 대조**:
   - Data 06 (최소 4개 승인 공식 Source) 적재 정책의 PostgreSQL DB ➔ API 노출 DTO 검증.
6. **결함 수정 및 릴리스 Hardening**:
   - 리뷰어 및 QA 검증 결과 접수된 Blocker/High 결함 수정 및 백엔드 단위/통합 회귀 재실행.

## 범위 밖

- 승인되지 않은 신규 API 엔드포인트나 데이터 계약 확장
- Frontend UI 컴포넌트 구현 및 CSS 스타일링
- Production Dockerfile, Compose, Nginx 및 CI/CD 배포 파이프라인 구축 (6주차 범위)
- 이메일 발송 또는 외부 캘린더 서비스 직접 연동

## 선행 조건

- `develop` 병합 SHA `f0d3dd3` 및 Migration `20260810_0006` 적용 확인
- 전용 PostgreSQL 테스트 DB (`_test`) 준비 (`TEST_DATABASE_URL` 환경변수 설정)
- FastAPI `actual` API 모드 및 Uvicorn 로컬 로딩 확인

## 공통 설계 원칙

1. **Fail-Closed 보안**: 인증 실패, 미인가 경로 접근, 로그 archive 삭제 시 잘못된 파일 경로 입력 등에 대해 예외 발생 시 무조건 차단(`401`/`403`/`400`/`422`) 처리한다.
2. **계약 비파괴 정합성**: API 요청/응답 Schema, Enum, Date 및 `null`/빈 배열 규칙을 단독으로 변경하지 않으며, 기존 계약 문서([api/](../../../api/README.md))를 준수한다.
3. **결정성 및 재현 가능성**: 추천 알고리즘 및 검색 파서 동작은 동일한 조건에 대해 명확하고 결정적인 응답을 보장하며, 비단정 자격 안내문구를 반드시 포함한다.
4. **독립 테스트 환경 분리**: 테스트 실행 시 실제 운영/개발 DB를 오염시키지 않고 독립된 `_test` 데이터베이스 및 트랜잭션 rollback 구조를 사용한다.

## Slice 계획

### BE5-00 - 통합 기준선 재검증 및 환경 고정 (`W5-G0`)

- **목적**: 5주차 백엔드 작업을 진행하기 위한 공통 시작점과 DB/테스트 환경 고정.
- **수행 작업**:
  - `develop` SHA `f0d3dd3` 및 Migration `20260810_0006` 정상 상태 확인.
  - 전용 PostgreSQL 테스트 DB (`TEST_DATABASE_URL`) 생성 및 Alembic migration 정상 적용 확인.
  - `python -m unittest discover` 및 `pytest backend/tests` 실행하여 초기 0 failure 상태 확인.
- **종료 산출물**: 5주차 백엔드 기준선 통과 확인 (`W5-G0_PASS` 지원).

### BE5-01 - 백엔드 핵심 기능 & 영속성/인증/로그 회귀 검증 (`W5-B1`)

- **목적**: 백엔드 전체 기능(DB, 검색, 상세, 추천, 관리자 인증, 수집 이력, 로그 콘솔)의 회귀 결함 식별 및 상태 코드 검증.
- **수행 작업**:
  - **DB Transaction**: SQLAlchemy 세션 트랜잭션 중단/Rollback 시 리소스 누수 및 불완전 데이터 적재 방지 검증.
  - **Search & Detail**: `POST/GET /api/v1/policies/search` 및 `GET /api/v1/policies/{id}` 자연어 파서, 필터 조건 조합, pagination, `EligibilitySummary` DTO 및 evidence 구조 검증.
  - **Recommendation**: `GET /api/v1/recommendations` 결정적 가중치 산출, 부합도 점수 계산, 미확정 사유 코드, 비단정 경고 문구 확인.
  - **Admin Auth & Run**: PIN 4자리 세션 토큰 생성/검증, 만료/세션 무효화, 수동 수집 트리거 (`202 Accepted`), 이력 목록/상세 및 Stale 수집 처리 확인.
  - **Admin Data & Log**: 정책 데이터 표 읽기 전용 페이징/Allowlist 정렬, 구조화 로그 파일 읽기, Correlation ID 추적, 회전 archive 삭제 파라미터 경로 탈출 방지(Fail-closed), Audit 로그 기록 검증.
- **종료 산출물**: 백엔드 종합 회귀 테스트 결과 보고서 및 결함 목록.

### BE5-02 - Data 06 신규 정책 적재 연동 & actual E2E 지원 (`W5-D3` / `W5-I1`)

- **목적**: Data 06 (최소 4개 승인 공식 Source)의 신규 적재 데이터가 백엔드 API에 차단 없이 수용되는지 확인 및 실제 E2E 통과 지원.
- **수행 작업**:
  - Data 06 신규 적재 정책 데이터가 `GET /api/v1/policies` 목록/검색 및 상세 API에 정상 수용 및 노출되는지 DTO 검증.
  - CollectionRun 수동 실행 Trigger 시 Data 06 수집 작업 연동 및 이력 상태 전이 확인.
  - 실제 PostgreSQL ➔ FastAPI ➔ React actual E2E 통합 테스트 지원 (`W5-G1` 통과 지원).
- **종료 산출물**: Data 06 DB ➔ API 연동 통과 증거.

### BE5-03 - 독립 리뷰/QA 결함 수정 및 Release 2 Hardening (`W5-FIX` / `W5-I2`)

- **목적**: 사용성 리뷰어 및 QA에서 전달된 백엔드 결함 수정 및 최종 Release 2 Gate 통과.
- **수행 작업**:
  - 접수된 Blocker/High 결함 원인 파악, 코드 수정 및 자체 회귀 테스트 수행.
  - 독립 QA 담당자의 결함 수정본 재검증 지원.
  - 백엔드 개발 기록(`docs/development/development_notes/backend/`) 갱신 및 API 문서 동기화.
  - `python scripts/validate_docs.py` 실행 및 통과.
- **종료 산출물**: 최종 결함 수정 완료 보고 및 Release 2 Gate (`W5-G2_PASS`) 백엔드 통과 지표.

## 검증 계획

### 자동화 단위/통합 테스트

```powershell
# 백엔드 단위 및 통합 테스트 실행
.\.venv\Scripts\python.exe -B -m unittest discover -s backend/tests -p "test_*.py" -v

# PostgreSQL 연동 전용 테스트 실행
$env:TEST_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/cheongnyeon_test"
.\.venv\Scripts\python.exe -B -m pytest backend/tests -q
```

### PostgreSQL DB Migration & Transaction 테스트

- Alembic head / downgrade / upgrade 반복 실행 테스트.
- DB 예외 발생 시 session.rollback() 정상 수행 여부 및 커넥션 풀 반환 검증.

### API 계약 및 DTO 대조 검증

- FastAPI OpenAPI schema 와 `docs/api/` 기준 문서(policies.md, admin_access.md, admin_collection_runs.md, admin_policies.md, admin_logs.md, recommendation.md) 요청/응답 구조 일치 확인.

### 문서 품질 및 비추적 검증

```powershell
.\.venv\Scripts\python.exe -B scripts\validate_docs.py
git status --short
```

## Forest 완료 기준

1. 백엔드 전체 단위/통합/PostgreSQL 회귀 테스트 통과 (실패 0건).
2. Admin PIN 인증, Session, 수동 수집 실행, 관리자 정책 표, 로그/감사 API 정상 동작 및 Fail-Closed 보장.
3. Data 06 적재 신규 정책의 DB ➔ API 노출 DTO 대조 완료.
4. QA 및 사용성 리뷰에서 발주된 Blocker/High 백엔드 결함 전건 수정 및 재검증 통과.
5. 비밀키, 개인정보, DB 파일 및 임시 산출물이 Git에 등록되지 않음.
6. `python scripts/validate_docs.py` 문서 검증 통과.

## 위험과 미확정 사항

- 외부 Data 06 수집 적재 지연 시 backend의 actual E2E(`W5-G1`) 테스트 일정 영향 가능성 ➔ 백엔드는 자체 DB fixture 기반으로 `BE5-01` 회귀 검증을 병렬 선행하여 블로킹 방지.
- Admin Log archive 삭제 시 시스템 보안 경로(Path traversal) 접근 시도 위험 ➔ Pydantic validator 및 os.path strict isolation으로 Fail-Closed 철저 적용.

## 관련 문서

- [5주차 상세 실행 계획](../../weekly_plan/week_05_release_2.md)
- [Integration 07 Release 2 Feature Acceptance](../integration/07_release_2_feature_acceptance.md)
- [Backend Admin Access Control](../backend/04_admin_access_control.md)
- [CollectionRun Admin API](../backend/05_collection_run_admin_api.md)
- [Backend Policy Search](../backend/06_policy_search.md)
- [Admin Data and Log Console](../integration/09_admin_data_log_console.md)
- [Recommendation Vertical Slice](../integration/06_recommendation_vertical_slice.md)
- [Eligibility Evidence and Summary](../integration/08_eligibility_evidence_summary.md)
- [문서화 정책](../../../governance/documentation_policy.md)
