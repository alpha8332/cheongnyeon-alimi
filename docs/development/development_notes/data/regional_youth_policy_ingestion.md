# Data 05 Regional Youth Policy Ingestion Forest 개발 기록

## 작업 정보

- 작업일: `2026-08-11`
- 작업 영역: Data
- 상태: in-progress
- 브랜치: `feature/data/regional-youth-policy-ingestion`
- 시작 커밋: `ee23bc80e642e3b4dccd1f803abf61d2a02fc0b8`
- 관련 계획: [Data 05 Regional Youth Policy Ingestion](../../develop_plan/data/05_regional_youth_policy_ingestion.md)

## 목적

광역자치단체 청년정책 포털 후보를 검증 가능한 repository inventory로 고정하고,
승인 전 후보와 실제 운영 Source를 구분할 실행 계약을 만든다.

## Forest 범위

- 17개 지역 포털 후보 inventory와 상태 관리
- Source preflight와 승인된 목록·상세 경로
- 지역 고유성·신청 가능성·온통청년/복지로 중복 판정
- 제한 actual 수집과 PostgreSQL·API·Browser 인수

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| RYP0 | completed | 17개 후보 JSON·Schema·계약 테스트 14개와 39개 subtest 통과 |
| RYP1 | 대기 | 홈페이지 탐색·Source 승인 |
| RYP2 | 대기 | 공통 실행 경계·Source Adapter |
| RYP3 | 대기 | 지역 고유성·신청 가능성 |
| RYP4 | 대기 | 온통청년·복지로 중복 제외 |
| RYP5 | 대기 | 대표 Source actual |
| RYP6 | 대기 | 지역별 확대·전체 판정 |

## 구현 내용

### RYP0 - 실행 inventory

- `광역자치단체별 청년정책사이트 정리.xlsx`의 `Sheet1!A2:C18`을 읽어
  17개 포털 후보를 repository JSON으로 변환했다.
- 입력 파일명·시트·범위와 SHA-256을 evidence로 기록하고 XLSX binary를
  Runtime 계약으로 사용하지 않는다.
- 모든 Source를 `candidate`로 시작하며 `source_id`, 승인 목록·상세 경로와
  요청 예산은 RYP1 승인 전까지 비워 둔다.
- `청년정책_데이터수집_완료.xlsx` 32행의 부산 상세 공고는 구현·승인 Source가
  아니라 RYP1 탐색을 돕는 `detail_candidate` seed로만 보존했다.

## 주요 변경 파일

- `data/reference/regional_youth_policy_sources.json`
- `data/schema/regional_youth_policy_source_inventory.schema.json`
- `tests/test_regional_source_inventory.py`
- `docs/development/develop_plan/data/05_regional_youth_policy_ingestion.md`
- `docs/development/develop_plan/data/06_supplemental_official_policy_ingestion.md`

## 설계 결정

### Source 관할 라벨과 canonical 지역 분리

XLSX는 광주와 전남을 나눈 17개 포털을 제공하지만 현재
`kr-bjd-20260803`은 `전남광주통합특별시(1200000000)`를 활성 지역으로 두고
광주 `2900000000`과 전남 `4600000000`을 `2026-07-01` 퇴역으로 보존한다.

포털 후보 수를 임의로 15개로 줄이거나 두 후보를 활성 통합 코드로 자동
치환하지 않았다. 17개 Source 관할 라벨은 그대로 보존하고 광주·전남 mapping을
`historical_review_required`, `active_code=null`로 격리했다. 실제 정책의 지역
rule은 RYP1~RYP3에서 공식 원문과 현행 관할을 확인한 뒤 결정한다.

### 후보와 승인 Source 분리

홈 URL과 상세 seed는 Source 발견의 입력일 뿐 승인 목록·상세 endpoint가 아니다.
운영 주체·robots·약관·라이선스·기술 접근과 요청 예산을 확인하기 전에는
`approved`나 `implemented`로 기록하지 않는다.

## 검증 결과

2026-08-11에 다음 검증을 실행했다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests\test_administrative_regions.py tests\test_regional_source_inventory.py -q
```

- 결과: `14 passed, 39 subtests passed`
- inventory JSON Schema, 17개 관할 라벨·URL 유일성, HTTPS·비밀 없는 URL,
  candidate-only 초기 상태, 활성·퇴역 행정구역 code 보존과 부산 탐색 seed를
  확인했다.

```powershell
.\.venv\Scripts\python.exe scripts\validate_docs.py
git diff --check
```

- 결과: 문서 검증 통과, whitespace 오류 없음
- 테스트는 외부 웹 요청이나 PostgreSQL을 사용하지 않았다. Source 접근·승인과
  actual 적재는 실행하지 않았으며 RYP1 이후 결과로 기록한다.

## 남은 작업

- RYP1에서 17개 홈의 운영 주체·목록·상세·robots·약관·요청 예산 확인
- RYP1에서 승인 상태·Source ID·allowlist·요청 예산·지역 mapping의 교차 필드
  조합을 검사하는 domain validator 추가
- 광주·전남 Source의 현행 관할과 정책별 지역 evidence mapping 결정
- 승인 Source만 RYP2 Adapter 구현 대상으로 전달
