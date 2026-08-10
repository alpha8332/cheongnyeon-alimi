# Eligibility Evidence and Summary Forest 개발 기록

## 작업 정보

- 기간: `2026-08-10`~
- 상태: in-progress
- 담당 영역: Data, Team Leader - Integration
- 브랜치: `feature/schema/eligibility-evidence-contract`
- 병합 대상: `develop`
- 시작 기준: `951fc61` (`merge crawling web policy data into develop`)
- 계획:
  [Integration 08 Eligibility Evidence and Summary](../../develop_plan/integration/08_eligibility_evidence_summary.md)
- 기준 계약:
  [Eligibility Summary 공통 계약](../../../data/eligibility_summary_contract.md)

## 목적

제외 조건·필요 서류·시설 연락처와 각 항목의 Source evidence를 Data·Backend·
Frontend가 같은 의미로 구현하도록 공통 계약을 먼저 고정한다. 기존 BE·FE
개발 파일을 동시에 수정하지 않고 계약 산출물을 먼저 병합한다.

## Forest 범위

- 조건·서류·시설 연락처의 필드·배열·enum·coverage 의미
- 공개 evidence와 내부 Raw provenance 경계
- 온통청년·복지로·천안청년센터 Source mapping
- 정상·경계·긴 문장·누락·충돌 합성 fixture
- 후속 DB → API → Browser 실제 인수

## Slice 진행 현황

| Slice | 상태 | 결과 |
| --- | --- | --- |
| DTL4-4A / ES0 | 완료 | Eligibility Summary 1.0.0 계약·Schema·Python 모델·fixture 승인 |
| DTL4-4A / ES1 기반 | 완료 | API 두 Source와 승인 웹 Source의 보수적 mapping·evidence 검증 |
| DTL4-4B / ES1 actual 인계 | 미착수 | Normalized 편입과 BE·FE fixture/type parity 대기 |
| ES2~ES4 | 미착수 | Backend DB·API, Frontend UI와 actual E2E 대기 |

## 구현 내용

### Coverage와 호환 경계

- Release snapshot 3,156건을 외부 호출 없이 다시 재생해 accepted 3,156,
  invalid 0과 기존 신청기간 safety 통과를 확인했다.
- DTL4-1 inventory의 `eligibility_text` coverage는 온통청년 2,695건 중
  1,024건, 복지로 461건 중 5건이며 기존 required·preferred·excluded 및
  education·employment 구조화 배열은 두 Source 모두 0건이다.
- 기존 값에서 새 조건 종류를 추정해 채우지 않고, 새 mapper도 안전하게
  분류할 수 없는 `ptcpPrpTrgtCn`·`slctCritCn`은 `unknowns`로 보낸다.
- 현재 `NormalizedProgram 1.1.0`은 Backend ORM·Importer·API와 exact field
  parity를 검사한다. DTL4-4A에서 새 필드를 직접 추가하면 BE 작업을 동시에
  수정해야 하므로 독립 nested 계약으로 먼저 고정했다.

### Eligibility Summary 1.0.0

- `coverage`, `requirements`, `exclusions`, `preferences`, `documents`,
  `unknowns`, `institutional_contacts` 7개 필드를 required로 고정했다.
- 복수 값은 항상 배열이고 값이 없으면 `[]`이다. `null`이나 필드 생략은
  허용하지 않는다.
- condition은 category·원문 text·evidence, document는 text·evidence,
  시설 연락처는 kind·label·value·evidence를 가진다.
- 공개 evidence는 source ID·URL·수집 시각·source field 또는 CSS selector만
  포함하고 Raw ID·hash·경로는 노출하지 않는다.
- complete는 unknown이 없을 때만, unknown은 조건·서류 원문이 전혀 없을 때만
  허용하도록 Python 의미 검증을 추가했다.

### Source mapping과 개인정보

- 온통청년은 명시 연령과 `addAplyQlfcCndCn`을 requirements,
  `sbmsnDcmntCn`을 documents로 보존한다. 실제 값이 대상·제외 의미를 함께
  가질 수 있는 `ptcpPrpTrgtCn`은 unknowns로 둔다.
- 복지로는 `tgtrDtlCn`을 requirements, 선정 의미를 추가 해석해야 하는
  `slctCritCn`을 unknowns로 둔다.
- 천안 웹 Source의 승인 section은 requirements·exclusions·documents·unknowns로
  매핑하고 모두 `#bo_v_con` evidence와 공식 상세 URL·수집 시각을 가진다.
- 공개 시설 대표전화와 공식 채널만 `phone`·`official_channel`로 승격한다.
  개인 휴대전화와 이메일은 Python 계약에서 거부하며 담당자 성명 필드 자체를
  제공하지 않는다.

### 대표 fixture

정상 완전 계약, partial 웹 경계, 완전 누락 unknown, 긴 가구 조건, API·웹 충돌의
5개 비밀 없는 합성 사례를 고정했다. 충돌 사례는 서로 다른 원문과 evidence를
모두 유지하며 수집 시각이 늦은 값을 정답으로 선택하지 않는다.

## 주요 변경 파일

- `collectors/eligibility.py`
- `collectors/eligibility_mapping.py`
- `collectors/validation.py`
- `data/schema/eligibility_summary.schema.json`
- `data/fixtures/contracts/eligibility_evidence_cases.json`
- `tests/test_eligibility_contract.py`
- `tests/test_cheonan_youthcenter_web.py`
- `docs/data/eligibility_summary_contract.md`
- `backend/requirements.txt`
- `backend/app/api/v1/endpoints/policy_search.py`
- `docs/development/develop_plan/forest_roadmap.md`
- `docs/development/develop_plan/README.md`

## 설계 결정

- 독립 nested 계약을 먼저 병합하고 `NormalizedProgram`·DB·API·TypeScript
  편입은 담당 영역별 후속 구현으로 분리한다.
- 새 공통 객체가 편입돼도 기존 `eligibility_text`와 조건 문자열 배열을
  제거하거나 자동 변환하지 않는다.
- Source field 이름만으로 필수·제외·우대를 단정하지 않고 실제 의미가
  혼재하면 unknown으로 보존한다.
- 시설 문의에 필요한 기관 연락처는 제공하되 개인 식별 가능 연락처는
  Schema 바깥에서 차단한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| 전체 Data 단위·통합 pytest (`tests`) | 통과: 166건, subtest 27건, warning 0건 |
| 전체 Backend pytest (`backend/tests`) | 통과: 125건, warning 0건 |
| Backend exact field parity pytest | 통과: 4건, 현재 Normalized·ORM·Importer·API 계약 회귀 없음 |
| Release snapshot strict offline replay | 통과: accepted 3,156, invalid 0, period safety pass |
| PostgreSQL 통합 경계 | 통과: 임시 pgpass와 전용 `cheongnyeon_alimi_test`로 천안 Runtime 적재 포함 전체 Data integration 실행 |
| 결정적 Fixture 재생성 검사 | 통과: 관리 대상 15개와 생성 결과 일치 |
| 문서 검증 | 통과: `scripts/validate_docs.py` |
| diff 검사 | 통과: `git diff --check` (Windows CRLF 안내만 출력) |

Starlette 1.3.1 `TestClient`가 우선 사용하는 `httpx2`를 테스트 의존성에 추가했다.
운영 수집 HTTP client인 `httpx`는 그대로 유지했으며, Integration 05의 Forest·계획 색인
상태는 개별 승인 문서의 `approved`와 일치시켰다.

## 남은 작업

- DTL4-4B에서 계약을 `NormalizedProgram`에 호환 편입할 version과 Data actual
  output을 확정한다.
- Backend는 계약 병합 뒤 DB·Migration·상세 API와 PostgreSQL 테스트를
  구현한다.
- Frontend는 Backend API 병합 뒤 상세 화면의 제외 조건·필요 서류·문의처와
  접근성 검증을 구현한다.
- Team Leader는 세 결과가 병합된 `develop`에서 실제 DB → API → Browser를
  대조한다.
