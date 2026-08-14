# Integration 08 Eligibility Evidence and Summary Forest 개발 계획

## 계획 정보

- 번호: Integration 08
- 담당 영역: Data·Backend·Frontend
- 상태: completed
- 진행: `ES0`~`ES4` 완료
- 계획일: `2026-08-07`
- 대상 Release: `v0.5.0`
- 선행 Forest: Integration 05 Contract Baseline
- 병렬·보강 Forest: Data 04 Public HTTPS Policy Ingestion
- 후속 Forest: Integration 06 Recommendation, Integration 07 Release 2 Acceptance
- 역할·브랜치 분담: `2026-08-10` 승인, 같은 날 단일 Integration 브랜치로 조정
- 계약 상태: Eligibility Summary `1.0.0` 공통 Schema·Source 소비 fixture 승인,
  NormalizedProgram `1.2.0`·DB·상세 API·Frontend UI 편입 완료
- 구현 브랜치: `feature/schema/eligibility-evidence-contract`

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

## DTL4-4A 승인 계약

다음 nested 구조를 Eligibility Summary `1.0.0` 공통 계약으로 승인했다. 실행
Schema와 세부 의미는
[Eligibility Summary 공통 계약](../../../data/eligibility_summary_contract.md)을
따른다. 현재 Policy DB·공개 API·Frontend 완료 기능을 뜻하지 않는다.

| 필드 | 의미 |
| --- | --- |
| `eligibility_summary.coverage` | `complete`, `partial`, `unknown` |
| `requirements[]` | 신청자가 충족해야 하는 구조화 또는 원문 조건 |
| `exclusions[]` | 해당하면 제외될 수 있는 조건 |
| `preferences[]` | 우대·가점 조건이며 필수 조건과 구분 |
| `documents[]` | Source에 명시된 제출 서류 |
| `unknowns[]` | 자동 비교 또는 구조화가 불가능한 확인 필요 조건 |
| `institutional_contacts[]` | 공개 시설 대표전화·공식 문의 채널; 개인 연락처 제외 |
| 항목 `category` | age·region·income·asset·employment·education·housing·household·other |
| 항목 `evidence` | source ID·URL·수집 시각·source field 또는 selector |

condition의 원문은 `text`에 두고 evidence는 공개 가능한 근거 포인터만 가진다.
내부 Raw ID·hash·경로는 공개 evidence에서 제외한다. 모든 복수 필드는 required
배열이고 값이 없으면 `[]`이며 `null`·생략은 허용하지 않는다. 개인 조건 비교
상태는 정책 데이터의 coverage와 별개로 관리한다.

## 역할 분담과 충돌 방지

Integration 08은 Slice마다 브랜치를 늘리지 않고
`feature/schema/eligibility-evidence-contract` 한 브랜치에서 완료한다. 담당별
변경은 Conventional Commit 경계와 파일 소유권으로 구분한다. Backend·Frontend
담당자가 별도 작업 브랜치에서 구현한 경우에도 계약 이름을 독자 변경하지 않고,
Team Leader가 해당 commit을 이 Integration 브랜치에 반영해 전체 회귀를 확인한다.

| 담당 | Conventional Commit 경계 | 책임 | 이번 작업에서 건드리지 않는 영역 |
| --- | --- | --- | --- |
| Data·Team Leader | `feat(data): ...` | 제외조건·필요서류·시설 연락처의 공통 계약, Source mapping·provenance·fixture·Schema 검증 | Frontend 화면 |
| Backend | `feat(backend): ...` | 승인 계약의 DB 저장·Migration·상세 DTO·직렬화·호환·PostgreSQL 테스트 | Source selector·Data 추정, Frontend 컴포넌트 |
| Frontend | `feat(frontend): ...` | 승인 TypeScript·Mock·API 소비와 `제외 조건`·`필요 서류`·`문의처` UI·접근성 테스트 | Data mapping, Backend DB·API 구현 |
| Team Leader | `test(integration): ...`, `docs(integration): ...` | Schema parity와 실제 DB → API → Browser E2E 대조 | 승인 계약의 임의 재작성 |

시설 연락처는 Data 04에서 추출한 공개 시설 대표전화와 공식 채널만 대상으로
한다. 개인 휴대전화·개인 이메일·성명은 공통 계약과 UI에 포함하지 않는다.
연락처를 기존 `required_conditions` 또는 자유문자열에 섞지 않고 ES0에서
`institutional_contacts[]`의 type·label·value·evidence와 빈 배열 의미를
Backend·Frontend와 함께 확정한다.

### 통합 순서

1. ES0·ES1 Data 계약과 fixture를 기준 commit으로 고정한다.
2. ES2 Backend 저장·Migration·상세 API를 같은 브랜치의 별도 Conventional
   Commit으로 반영하고 PostgreSQL에서 검증한다.
3. ES3 Frontend는 승인된 상세 응답과 fixture를 소비하며, 별도 작업 결과가
   있으면 commit 단위로 현재 Integration 브랜치에 반영한다.
4. Team Leader는 한 브랜치의 최종 결과에서 ES4 실제 DB → API → Browser를
   대조한다.

새 브랜치는 Integration 08과 독립된 목표·완료 기준이 생기거나 현재 브랜치와
병렬 유지가 반드시 필요한 경우에만 제안한다.

## Slice 계획

### ES0 - 원문 coverage와 계약 Gate (`DTL4-4A` 완료)

- 현재 snapshot에서 자격·소득·추가 조건·제외·서류 원문 coverage를 측정한다.
- 대표 정상·부분·미상·충돌 사례를 고정하고 세 영역이 구조 초안을 대조한다.
- 제외조건·필요서류·시설 연락처의 필드·필수 여부·빈 배열·evidence와 개인
  연락처 제외 경계를 확정한다.
- 사용자에게 허용할 문구와 금지할 단정 표현을 승인한다.

### ES1 - Data 구조화와 provenance (`DTL4-4A`·`DTL4-4B` 완료,
ES2에서 actual 편입 완료)

- 기존 API Source의 풍부한 조건 필드를 우선 매핑한다.
- 확실한 category와 원문 조건을 분리하고 필드별 evidence를 보존한다.
- Data 04 웹 Source의 승인 필드를 같은 추출 계약으로 연결한다.
- 공개 시설 대표전화와 공식 문의 채널을 승인 연락처 계약으로 매핑하고 개인
  연락처는 승격하지 않는다.
- DB 적재 가능한 API 정책 4건과 승인 웹 Source 합성 표본 1건을 identity와
  `eligibility_summary`로 묶은 소비 fixture로 인계한다. 이 envelope는
  `NormalizedProgram`·공개 API DTO로 간주하지 않는다.

### ES2 - Backend 상세 API (완료)

- 정책 상세 DTO에 승인된 요약 구조를 추가하고 기존 소비 호환성을 검토한다.
- complete·partial·unknown, 빈 배열과 누락 의미를 결정적으로 직렬화한다.
- Source·수집 시각·원문 링크와 민감하지 않은 evidence만 노출한다.
- 필요 서류와 시설 연락처 저장 필드·Migration을 추가하고 기존 조건 배열과
  호환되는 정책 상세 응답을 검증한다.
- `NormalizedProgram 1.2.0`에 `eligibility_summary`를 required로 편입하고
  1.0.0·1.1.0 입력은 추정 없이 `unknown` 빈 요약으로 승격한다.
- PostgreSQL JSONB 저장과 Migration `20260810_0006`, 상세 API 노출을 구현한다.
  목록·검색 DTO에는 요약을 추가하지 않아 기존 목록 payload를 유지한다.
- evidence의 수집 시각만 달라진 재수집은 변경으로 세지 않되, 조건·근거 위치·
  연락처 내용 변화는 update로 처리한다.

### ES3 - Frontend 핵심 신청 조건 UI (완료)

- 필수·제외·우대·서류·확인 필요를 시각적으로 구분한다.
- 상세 화면에 `제외 조건`, `필요 서류`, `문의처` 영역을 추가하고 시설
  전화번호·공식 채널을 키보드와 모바일에서도 사용할 수 있게 한다.
- 모바일·키보드·긴 문장·빈 값·partial·error 상태를 제공한다.
- 로컬 사용자 조건이 있으면 비교 상태를 표시하되 최종 자격을 단정하지 않는다.
- 세부 Slice: [Frontend 07 Eligibility Summary UI](../frontend/07_eligibility_summary_ui.md) FE7-xx;
  회귀: [Frontend 09 Integration and Regression](../frontend/09_integration_and_regression.md) FE9-xx
- 목록 `PolicyDto`와 상세 `PolicyDetailDto`를 분리하고 1.2.0 상세 응답에서만
  Eligibility Summary를 소비한다.
- 빈 배열도 누락으로 숨기지 않고 원문에서 구조화된 값을 확인하지 못했다는
  문구로 표시한다. partial·unknown coverage는 신청 가능·불가로 바꾸지 않는다.
- 시설 전화번호는 `tel:` 링크와 44px 이상 터치 영역을 제공한다. 공식 채널은
  HTTP(S)일 때만 링크로 만들고 텍스트 채널명은 그대로 표시한다.
- 승인 웹 표본을 주입한 Chromium 검증으로 제외조건·서류·문의처·근거 링크·
  키보드 focus와 모바일 1열 배치를 확인한다.

### ES4 - actual 세로 인수 (완료)

- 실제 PostgreSQL → 정책 상세 API → Browser에서 대표 사례를 검증한다.
- UI 항목이 DB evidence와 일치하고 공식 원문으로 이동 가능한지 대조한다.
- 기존 목록·상세·검색과 Release 1 golden 회귀를 실행한다.

승인 천안 HTML fixture를 전용 PostgreSQL에 Runtime 적재한 뒤 상세 API와
Browser를 대조했다. partial 요약의 필수·제외·서류·unknown·시설 문의처와
6개 공개 evidence URL이 일치했고 공개 응답에는 내부 provenance가 없었다.
Release 1 승인 snapshot 3,156건도 같은 테스트 DB에 재생해 HTTP 기술 감사
2개 시나리오와 실제 Browser golden을 통과했다. 검증 뒤 Uvicorn을 종료하고
테스트 DB는 Alembic base로 되돌렸다.

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

- `NormalizedProgram 1.2.0`과 Backend 저장 계약은 37개 exact field parity로
  편입됐다. 1.0.0·1.1.0 compatibility adapter는 source 근거가 없는 기존 객체에
  조건을 추정하지 않고 `unknown` 빈 요약만 추가한다.
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
- [Eligibility Summary 공통 계약](../../../data/eligibility_summary_contract.md)
- [4주차 상세 실행 계획](../../weekly_plan/week_04_v0_5_0.md)
