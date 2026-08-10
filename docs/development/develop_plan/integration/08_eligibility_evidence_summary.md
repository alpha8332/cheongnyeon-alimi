# Integration 08 Eligibility Evidence and Summary Forest 개발 계획

## 계획 정보

- 번호: Integration 08
- 담당 영역: Data·Backend·Frontend
- 상태: draft
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Integration 05 Contract Baseline
- 병렬·보강 Forest: Data 04 Public HTTPS Policy Ingestion
- 후속 Forest: Integration 06 Recommendation, Integration 07 Release 2 Acceptance
- 권장 브랜치: 영역별 구현 브랜치와 병합 순서를 W4-G0에서 확정

## 목적

정책 상세에서 긴 원문을 그대로 읽지 않아도 누가 신청할 수 있는지 빠르게
파악하도록, 신청 조건·제외 조건·필요 서류와 확인 필요 사항을 출처 근거가 있는
구조로 제공하고 읽기 쉬운 UI까지 연결한다. 데이터가 부족한 경우 신청 가능·불가를
단정하지 않으며 원문 확인 경로를 유지한다.

## 범위

- 기존 API 원문의 소득·추가 자격·참여 대상·필요 서류 필드 재매핑
- 웹 Source가 제공하는 상세 조건의 같은 계약 편입
- 연령·거주지·소득·자산·취업·학력·주거·가구·기타 조건 분류
- 필수 조건, 제외 조건, 우대 조건, 필요 서류와 확인 필요 항목 구분
- 각 항목의 source ID·URL·수집 시각과 source field 또는 selector evidence
- 정책 상세 API의 구조화된 자격요건 응답
- 정책 상세 UI의 `핵심 신청 조건` 카드와 원문·공식 신청 페이지 연결
- 사용자 로컬 조건이 있을 때 `일치`, `불일치`, `확인 필요` 비교
- partial·unknown·충돌 데이터와 긴 조건의 표시
- Data·Backend·Frontend 단위 테스트와 실제 DB → API → Browser E2E

## 범위 밖

- 수혜·선정 가능성 예측과 법적·행정적 자격 확정
- Source에 없는 조건·수치·예외 추정
- LLM이 원문 근거 없이 생성하는 요약
- OCR·첨부 PDF·이미지 문서 자동 해석
- 일반 사용자 개인정보의 서버 저장
- 모든 Source의 자유문장을 완전한 계산식으로 변환

## 선행 조건

- W4-G0에서 구조화 필드, `null`·빈 배열·partial 의미와 UI 문구를 승인해야 한다.
- 기존 `eligibility_text`를 폐기할지 원문 호환 필드로 유지할지 소비자 검토가
  필요하다.
- 현재 API가 이미 제공하는 소득·추가 자격·참여 대상·필요 서류 원문 필드의
  실제 coverage를 먼저 측정해야 한다.
- 웹 Source 값은 Data 04가 완료된 항목부터 점진적으로 소비하며, Data 04 전체를
  기다리지 않고 API Source 기반 세로 연결을 먼저 검증할 수 있다.

## 공통 설계 원칙

- 화면 제목은 `핵심 신청 조건`을 기본으로 하고 `신청 가능`·`신청 불가`를
  무조건 단정하지 않는다.
- 개인 조건 비교 결과는 `조건상 일치`, `조건상 불일치`, `추가 확인 필요`로
  표현하며 최종 판단 주체와 공식 원문 링크를 함께 제공한다.
- 요약 항목에서 원문 근거로 이동할 수 있어야 하며 수치와 단위는 임의로
  반올림하거나 바꾸지 않는다.
- Source별 Extractor가 원문을 구조화하고 공통 계층은 Source selector를 알지
  않는다.
- 구조화할 수 없는 조건을 삭제하지 않고 확인 필요 원문으로 보존한다.

## W4-G0 계약 후보

다음은 승인 전 제안이며 현재 API·DB 계약이 아니다.

| 필드 | 의미 |
| --- | --- |
| `eligibility_summary.status` | `complete`, `partial`, `unknown` |
| `requirements[]` | 신청자가 충족해야 하는 구조화 또는 원문 조건 |
| `exclusions[]` | 해당하면 제외될 수 있는 조건 |
| `preferences[]` | 우대·가점 조건이며 필수 조건과 구분 |
| `required_documents[]` | Source에 명시된 제출 서류 |
| `unknown_conditions[]` | 자동 비교 또는 구조화가 불가능한 확인 필요 조건 |
| 항목 `category` | age·region·income·asset·employment·education·housing·household·other |
| 항목 `evidence` | source ID·URL·수집 시각·원문·source field 또는 selector |

개인 조건 비교 상태는 정책 데이터의 완전성과 별개로 관리한다. 필드 이름과
중첩 구조는 Backend OpenAPI·Frontend TypeScript·Data Schema 초안을 함께
검토한 뒤 확정한다.

## Slice 계획

### ES0 - 원문 coverage와 계약 Gate

- 현재 snapshot에서 자격·소득·추가 조건·제외·서류 원문 coverage를 측정한다.
- 대표 정상·부분·미상·충돌 사례를 고정하고 세 영역이 구조 초안을 대조한다.
- 사용자에게 허용할 문구와 금지할 단정 표현을 승인한다.

### ES1 - Data 구조화와 provenance

- 기존 API Source의 풍부한 조건 필드를 우선 매핑한다.
- 확실한 category와 원문 조건을 분리하고 필드별 evidence를 보존한다.
- Data 04 웹 Source의 승인 필드를 같은 추출 계약으로 연결한다.

### ES2 - Backend 상세 API

- 정책 상세 DTO에 승인된 요약 구조를 추가하고 기존 소비 호환성을 검토한다.
- complete·partial·unknown, 빈 배열과 누락 의미를 결정적으로 직렬화한다.
- Source·수집 시각·원문 링크와 민감하지 않은 evidence만 노출한다.

### ES3 - Frontend 핵심 신청 조건 UI

- 필수·제외·우대·서류·확인 필요를 시각적으로 구분한다.
- 모바일·키보드·긴 문장·빈 값·partial·error 상태를 제공한다.
- 로컬 사용자 조건이 있으면 비교 상태를 표시하되 최종 자격을 단정하지 않는다.
- 세부 Slice: [Frontend 07 Eligibility Summary UI](../frontend/07_eligibility_summary_ui.md) FE7-xx;
  회귀: [Frontend 09 Integration and Regression](../frontend/09_integration_and_regression.md) FE9-xx

### ES4 - actual 세로 인수

- 실제 PostgreSQL → 정책 상세 API → Browser에서 대표 사례를 검증한다.
- UI 항목이 DB evidence와 일치하고 공식 원문으로 이동 가능한지 대조한다.
- 기존 목록·상세·검색과 Release 1 golden 회귀를 실행한다.

## 검증 계획

- Data field mapping·분류·provenance·partial 단위 테스트
- Backend Schema·직렬화·호환·404·partial PostgreSQL 테스트
- Frontend normal·partial·unknown·긴 조건·오류·모바일·키보드 테스트
- 실제 DB → API → Browser 대표 정책 E2E
- 기존 검색·상세와 Release 1 golden 회귀
- `python scripts/validate_docs.py`
- `git diff --check`

## Forest 완료 기준

- 정책 상세에서 필수·제외·우대·서류·확인 필요가 구분돼 표시됨
- 각 요약 항목이 Source 근거와 수집 시각을 추적할 수 있음
- 데이터가 부족할 때 신청 가능·불가를 단정하지 않고 partial·unknown을 표시함
- API Source 기반 대표 사례와 승인 웹 Source 보강 사례가 실제 E2E로 검증됨
- 기존 `eligibility_text` 소비와 검색·상세 회귀가 깨지지 않음
- 변경된 Schema·API·DB·UI 계약과 개발 기록이 실제 구현에 맞게 갱신됨

## 위험과 미확정 사항

- 현재 정규화 계약은 자격 원문을 재작성하지 않으므로 구조화 필드 추가는
  W4-G0 소비자 승인과 Schema version 검토가 필요하다.
- 조건 문장은 예외·가구 단위·기준연도에 따라 복잡해 단순 숫자 비교가 잘못된
  결론을 낼 수 있다. 계산 불가능한 조건은 확인 필요로 남긴다.
- API와 웹 원문이 충돌하면 최신이라고 추정해 덮어쓰지 않고 Source·수집 시각을
  함께 보존한 뒤 우선순위 계약을 별도 결정한다.
- 첫 v0.5.0 범위에서 모든 정책을 `complete`로 만들 수 없으므로 coverage와
  partial 비율을 Release 2 근거에 명시해야 한다.

## 관련 문서

- [v0.5.0 Contract Baseline](05_v0_5_0_contract_baseline.md)
- [Public HTTPS Policy Ingestion](../data/04_public_https_policy_ingestion.md)
- [Recommendation Vertical Slice](06_recommendation_vertical_slice.md)
- [Policy API 계약](../../../api/policies.md)
- [데이터 Schema](../../../data/data_schema.md)
- [Policy DB 매핑](../../../architecture/policy_database_mapping.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
