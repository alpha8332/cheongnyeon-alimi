# Integration 08 Eligibility Evidence and Summary Forest 개발 기록

## 작업 정보

- 기간: `2026-08-11`
- 담당 영역: Data·Backend·Frontend
- 상태: in-progress
- 브랜치: `feature/backend/policy-recommendation`
- 선행 Forest: Integration 05 Contract Baseline
- 관련 계획: [Integration 08 Eligibility Evidence Plan](../../develop_plan/integration/08_eligibility_evidence_summary.md)
- 현재 Slice: ES0, ES2 completed (`2026-08-11`)

## 목적

정책 상세에서 긴 원문을 그대로 읽지 않고도 필수 신청 조건, 제외 조건, 우대 조건, 필요 제출 서류 및 공식 문의처를 빠르게 파악할 수 있도록, 출처 보증(Evidence) 메타데이터가 연결된 구조화된 자격요건 응답 DTO(`eligibility_summary`)를 정책 상세 API(`GET /api/v1/policies/{id}`)에 제공하기 위한 개발 기록이다.

## Forest 범위

- 자격요건 구조화 응답 DTO (`EligibilitySummaryResponse`, `ItemCondition`, `ItemDocument`, `ItemEvidence`, `InstitutionalContact`)
- 필수 조건(`requirements[]`), 제외 조건(`exclusions[]`), 우대 조건(`preferences[]`), 제출 서류(`required_documents[]`), 미확정 조건(`unknown_conditions[]`), 공식 문의처(`institutional_contacts[]`) 구조체 분류
- 각 조건 항목별 `source_id`, `source_url`, `collected_at` 메타데이터 바인딩
- 자격 상태 (`complete`, `partial`, `unknown`) 자동 판정 로직
- 정책 상세 API 엔드포인트(`GET /api/v1/policies/{policy_id}`) 응답 DTO 연동 및 단위 테스트

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **ES0** | **원문 coverage와 계약 Gate** | **completed** | `EligibilitySummaryResponse` 및 서브 DTO 스키마 명세 확정 |
| **ES1** | Data 구조화와 provenance | draft | Data 04 웹 Source 자격요건 추출 및 provenance 매핑 |
| **ES2** | **Backend 상세 API** | **completed** | `build_eligibility_summary` 서비스 구현 및 `GET /api/v1/policies/{id}` 응답 연동, 2개 테스트 100% 통과 |
| **ES3** | Frontend 핵심 신청 조건 UI | draft | 상세 화면 `핵심 신청 조건` 카드 및 서류/문의처 UI 구현 예정 |
| **ES4** | actual 세로 인수 | draft | 실제 DB -> API -> Browser 세로 인수 검증 예정 |

## 구현 내용

### Slice ES0 & ES2 - Backend 상세 API 및 자격요건 DTO 연동

1. **자격요건 DTO 스키마 구현 ([policy.py](../../../../backend/app/schemas/policy.py))**
   - `ItemEvidence`: `source_id`, `source_url`, `collected_at` 메타데이터
   - `ItemCondition`: `category` (`age`, `region`, `other` 등), `content`, `evidence`
   - `ItemDocument`: 제출 서류 항목 (`name`, `content`, `evidence`)
   - `InstitutionalContact`: 공식 기관 문의처 (`label`, `value`, `contact_type`)
   - `EligibilitySummaryResponse`: `status` (`complete`, `partial`, `unknown`), `requirements[]`, `exclusions[]`, `preferences[]`, `required_documents[]`, `unknown_conditions[]`, `institutional_contacts[]`
   - `PolicyRead`: `eligibility_summary: Optional[EligibilitySummaryResponse]` 필드 바인딩.

2. **자격요건 구축 서비스 ([eligibility_evidence.py](../../../../backend/app/services/eligibility_evidence.py))**
   - Policy DB 모델로부터 연령 조건, 거주지 조건, `required_conditions`, `excluded_conditions`, `preferred_conditions`, `organization` 문의처를 파싱 및 `ItemEvidence` 결합.
   - 조건 항목 수에 따라 `complete` / `partial` / `unknown` 상태 자동 부여.

3. **정책 상세 API 라우터 연동 ([policies.py](../../../../backend/app/api/v1/endpoints/policies.py))**
   - `GET /api/v1/policies/{policy_id}` 응답 생성 시 `build_eligibility_summary(policy)`를 수행하여 DTO 확장.

## 주요 변경 파일

- `backend/app/schemas/policy.py`: `EligibilitySummaryResponse` 및 서브 DTO 스키마 정의, `PolicyRead` 확장
- `backend/app/services/eligibility_evidence.py`: 자격요건 구조화 및 Evidence 바인딩 서비스 구현
- `backend/app/api/v1/endpoints/policies.py`: `get_policy_detail` 엔드포인트 연동
- `backend/tests/test_eligibility_evidence_api.py`: 자격요건 응답 및 Evidence 매핑 테스트 (2 passed)
- `docs/development/development_notes/integration/eligibility_evidence_summary.md`: Integration 08 ES0/ES2 개발 기록

## 설계 결정

1. **하위 호환성 유지 (Backward Compatibility)**:
   - 기존 `PolicyRead` 응답의 모든 필드를 그대로 유지하면서 `eligibility_summary` 필드를 선택적(Optional)으로 확장하여 기존 API 소비자와의 호환성을 보장함.
2. **출처 보증 메타데이터 분리 (ItemEvidence)**:
   - 구조화된 각 자격 요건 항목마다 `source_id`, `source_url`, `collected_at`을 명시하여 데이터의 출처를 투명하게 제공함.

## 검증 결과

- **자격요건 API 단위/통합 테스트**: `pytest backend/tests/test_eligibility_evidence_api.py` ➔ **2 Passed**
- **백엔드 전체 회귀 테스트**: `pytest backend/tests` ➔ **147 Passed, 15 Skipped**
- **문서 무결성 검증**: `python scripts/validate_docs.py` ➔ **Pass**

## 남은 작업

- Frontend 핵심 신청 조건 카드 UI 연결 (`Slice ES3`) 및 actual 세로 인수 (`Slice ES4`)
