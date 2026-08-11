# Integration 06 Recommendation Vertical Slice Forest 개발 기록

## 작업 정보

- 기간: `2026-08-11`
- 담당 영역: Backend·Frontend
- 상태: in-progress
- 브랜치: `feature/backend/policy-recommendation`
- 선행 Forest: Integration 05 Contract Baseline
- 관련 계획: [Integration 06 Recommendation Plan](../../develop_plan/integration/06_recommendation_vertical_slice.md)
- 현재 Slice: R0, R1 completed (`2026-08-11`)

## 목적

사용자 조건(연령, 거주지, 관심 분야, 신청 상태 등)을 기존 결정적 검색 엔진 기반에 적용하여 맞춤 정책 목록, 추천 사유 코드(`reasons[]`), 미확정 조건(`unknown_conditions[]`) 및 비단정 안내 문구(`disclaimer`)를 반환하는 추천 API 기준선을 구축하기 위한 개발 기록이다.

## Forest 범위

- 승인된 사용자 조건과 추천 request·response DTO (`RecommendationRequest`, `RecommendationResponse`, `RecommendationItem`)
- 연령·거주지·관심분야·신청상태 판정 및 부합도 점수(`score`) 계산
- 추천 사유 코드(`MATCHED_CATEGORY`, `MATCHED_REGION`, `MATCHED_AGE`, `MATCHED_STATUS`) 매핑
- 결정적 정렬(`score DESC`, `id ASC`) 및 유효성 검사 (`422 Unprocessable Entity`)
- API 엔드포인트 (`POST /api/v1/recommendations`, `GET /api/v1/policies/recommendations`)
- 단위·통합·성능 회귀 테스트 및 문서화

## Slice 진행 현황

| Slice | 목표 | 상태 | 검증 내용 |
| --- | --- | --- | --- |
| **R0** | **계약 소비와 평가 표본 (Contract & Evaluation Samples)** | **completed** | `RecommendationRequest`, `RecommendationItem` DTO 정의 및 API 명세서(`recommendation.md`) 작성 완료 |
| **R1** | **Backend 결정적 추천 (Deterministic Recommendation API)** | **completed** | `recommend_policies_service`, `evaluate_policy_recommendation`, `POST /api/v1/recommendations`, `GET /api/v1/policies/recommendations` 엔드포인트, 4개 테스트 100% 통과 |
| **R2** | Frontend 추천 UI | draft | Frontend 05 및 추천 화면 연결 예정 |
| **R3** | 실제 세로 인수 | draft | 실제 DB -> FastAPI -> React 세로 연결 및 인수 검증 예정 |

## 구현 내용

### Slice R0 & R1 - DTO 명세 및 Backend 결정적 추천 API

1. **맞춤 추천 DTO 정의 ([recommendation.py](../../../../backend/app/schemas/recommendation.py))**
   - `RecommendationRequest`: `age`, `region`, `category`, `status`, `include_partial`, `limit` 필드 및 수치 범위 검증.
   - `RecommendationReason`: `code`, `label` 추천 사유 단위 DTO.
   - `RecommendationItem`: 정책 메타데이터 + `score`, `reasons[]`, `unknown_conditions[]`, `disclaimer` 비단정 안내 문구.

2. **결정적 추천 서비스 ([recommendation.py](../../../../backend/app/services/recommendation.py))**
   - 부합도 점수 계산 규칙: `category` 일치 +30점, `region` 일치 +30점, `age` 일치 +30점, `status == 'open'` +10점.
   - 2차 결정적 정렬: `score DESC`, `id ASC` 적용으로 동일 조건/스냅샷에서 100% 결정적 결과 보장.
   - 미확정 조건(`unknown_conditions`) 및 자격 비단정 안내 문구(`disclaimer`) 동시 제공.

3. **추천 API 엔드포인트 ([recommendation.py](../../../../backend/app/api/v1/endpoints/recommendation.py))**
   - `POST /api/v1/recommendations` 및 `GET /api/v1/policies/recommendations` 라우터 구현 및 `api.py` 등록.

## 주요 변경 파일

- `backend/app/schemas/recommendation.py`: 맞춤 추천 DTO 스키마 정의
- `backend/app/services/recommendation.py`: 추천 평가 및 결정적 정렬 서비스 구현
- `backend/app/api/v1/endpoints/recommendation.py`: 추천 POST/GET 엔드포인트 구현
- `backend/app/api/v1/api.py`: `/recommendations` 라우터 등록
- `backend/tests/test_recommendation_api.py`: 추천 API 결정성, Score, 사유, 422 테스트 (4 passed)
- `docs/api/recommendation.md`: 맞춤 추천 API 계약 명세서 작성

## 설계 결정

1. **결정적 2차 정렬 (Deterministic Ordering)**:
   - 동일 부합도 점수(`score`)를 가진 정책이 여러 건인 경우 `id ASC` (오름차순)를 2차 정렬 기준으로 강제하여, 동일한 입력 요청 시 서버 응답의 순서가 변하지 않도록 함.
2. **비단정 안내 문구 보장 (Non-assertive Disclaimer Guarantee)**:
   - 추천 API는 자격 충족 여부를 최종 확정하지 않으므로 모든 아이템에 "본 추천 결과는 자격을 확정하지 않으며..." 안내 문구를 보장하여 유저 오해를 방지함.

## 검증 결과

- **추천 API 단위/통합 테스트**: `pytest backend/tests/test_recommendation_api.py` 실행 -> **4 Passed**
- **백엔드 전체 회귀 테스트**: `pytest backend/tests` 실행 -> **145 Passed, 15 Skipped**
- **문서화 무결성 검증**: `python scripts/validate_docs.py` 실행 -> **Pass**

## 남은 작업

- Frontend 추천 화면 UI 연결 (`Slice R2`) 및 actual 통합 검증 (`Slice R3`)
