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
Frontend가 같은 의미로 구현하도록 공통 계약을 먼저 고정하고, 같은 Integration
브랜치에서 담당별 Conventional Commit 경계를 유지하며 실제 저장·API·UI로
연결한다.

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
| DTL4-4B / ES1 actual 인계 | 완료 | Source dispatcher·정책 identity 기반 5건 소비 fixture 완료 |
| ES2 Backend 상세 API | 완료 | NormalizedProgram 1.2.0·Migration 0006·JSONB·상세 DTO·PostgreSQL actual 완료 |
| ES3~ES4 | 미착수 | Frontend UI와 actual Browser E2E 대기 |

## 구현 내용

### Coverage와 호환 경계

- Release snapshot 3,156건을 외부 호출 없이 다시 재생해 accepted 3,156,
  invalid 0과 기존 신청기간 safety 통과를 확인했다.
- DTL4-1 inventory의 `eligibility_text` coverage는 온통청년 2,695건 중
  1,024건, 복지로 461건 중 5건이며 기존 required·preferred·excluded 및
  education·employment 구조화 배열은 두 Source 모두 0건이다.
- 기존 값에서 새 조건 종류를 추정해 채우지 않고, 새 mapper도 안전하게
  분류할 수 없는 `ptcpPrpTrgtCn`·`slctCritCn`은 `unknowns`로 보낸다.
- DTL4-4A 당시 `NormalizedProgram 1.1.0`은 Backend ORM·Importer·API와 exact
  field parity를 검사했다. 새 필드는 독립 nested 계약으로 먼저 고정했고
  ES2에서 Data·Backend parity를 함께 1.2.0으로 올렸다.

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

### DTL4-4B 소비 인계

- Source ID에 따라 승인 mapper만 선택하고 미등록 Source는 오류로 거부하는
  공통 dispatcher를 추가했다.
- canonical Seed에 포함되는 온통청년 2건·복지로 2건과 승인 웹 Source 합성
  표본 `notice:674` 1건을 `source_id + external_id`와
  `eligibility_summary`로 묶었다. invalid 정책은 인계에서 제외했다.
- 이 인계 envelope는 nested 소비 검토용이며 `NormalizedProgram`·DB·공개 API
  전체 계약으로 가장하지 않는다. ES2에서는 같은 nested 객체를 실제 1.2.0
  Schema·canonical Seed·DB·상세 API에 편입했다.
- 기존 Frontend 검색 문구 `조건 일치`·`조건 불일치`·`정보 미확인`은 Release 1
  검색 표시 계약이다. Eligibility UI가 이를 그대로 재사용하면 승인 문구인
  `조건상 일치`·`조건상 불일치`·`추가 확인 필요`와 달라지므로 FE 소비 검토
  항목으로 남겼다.
- Backend DTO parity는 ES2에서 완료했다. Frontend 타입·Mock parity와 추천
  비확률화 검토는 ES3에서 수행한다.

승인 공지 `notice:674`를 임시 Runtime 디렉터리에서 actual 재검증했다. 공개
요청 2회로 Raw 3건·정책 1건을 만들었고, mapper 결과는 `partial`, requirements
1건·exclusions 4건·documents 5건·unknowns 6건·institutional contacts 2건이었다.
모든 항목은 공식 상세 URL과 `#bo_v_con` evidence를 가지며 Schema issue는
0건이었다. 연락처 값과 HTML은 출력·Git에 남기지 않았고 임시 디렉터리는
검증 종료와 함께 제거했다. 이번 확인은 Data actual이며 DB·API·Browser
완료를 뜻하지 않는다.

### ES2 Normalized 1.2·DB·상세 API

- `NormalizedProgram`을 1.2.0·37 required 필드로 올리고 등록 Source는 승인
  mapper를 호출하도록 연결했다. 미등록 generic Source와 1.0.0·1.1.0 legacy
  입력은 근거를 추정하지 않고 빈 unknown 요약을 사용한다.
- Migration `20260810_0006`은 `policies.eligibility_summary` non-null JSONB를
  추가한다. 기존 행은 unknown 요약으로 backfill하되 기존 `schema_version`은
  소급 변경하지 않는다.
- Importer·ORM은 요약 전체를 저장한다. 동일 내용을 새 시각에 재수집한 경우
  evidence `collected_at`만으로 update하지 않고, 조건·서류·문의처·locator 변화는
  update로 분류한다.
- `GET /api/v1/policies/{id}`는 공개 evidence만 포함한 요약을 반환한다. 목록·
  검색 DTO는 새 필드를 제외해 기존 payload와 비용을 유지한다.
- 실제 PostgreSQL에서 Migration 0005→0006 보존, canonical Seed→API, 천안
  Runtime Raw→DB→상세 API와 멱등 재수집을 검증했다.

## 주요 변경 파일

- `collectors/eligibility.py`
- `collectors/eligibility_mapping.py`
- `collectors/validation.py`
- `data/schema/eligibility_summary.schema.json`
- `data/fixtures/contracts/eligibility_evidence_cases.json`
- `tests/test_eligibility_contract.py`
- `tests/test_cheonan_youthcenter_web.py`
- `docs/data/eligibility_summary_contract.md`
- `scripts/build_data_fixtures.py`
- `docs/data/fixture_seed_contract.md`
- `backend/requirements.txt`
- `backend/app/api/v1/endpoints/policy_search.py`
- `collectors/normalized.py`
- `collectors/normalizer.py`
- `data/schema/normalized_program.schema.json`
- `backend/app/models/policy.py`
- `backend/app/services/seed_importer.py`
- `backend/app/schemas/policy.py`
- `backend/app/api/v1/endpoints/policies.py`
- `backend/alembic/versions/20260810_0006_policy_eligibility_summary.py`
- `tests/integration/test_seed_to_policy_api.py`
- `tests/integration/test_cheonan_web_runtime_to_database.py`
- `backend/tests/test_postgresql_migration.py`
- `docs/development/develop_plan/forest_roadmap.md`
- `docs/development/develop_plan/README.md`

## 설계 결정

- 독립 nested 계약을 먼저 승인하고 `NormalizedProgram`·DB·API 편입은 ES2의
  한 통합 변경으로 검증한다. TypeScript·UI는 ES3에서 같은 계약을 소비한다.
- 새 공통 객체가 편입돼도 기존 `eligibility_text`와 조건 문자열 배열을
  제거하거나 자동 변환하지 않는다.
- Source field 이름만으로 필수·제외·우대를 단정하지 않고 실제 의미가
  혼재하면 unknown으로 보존한다.
- 시설 문의에 필요한 기관 연락처는 제공하되 개인 식별 가능 연락처는
  Schema 바깥에서 차단한다.

## 검증 결과

| 검증 | 결과 |
| --- | --- |
| 전체 Data 단위·통합 pytest (`tests`) | 통과: 168건, subtest 27건, warning 0건 |
| 전체 Backend pytest (`backend/tests`) | 통과: 126건, warning 0건 |
| Backend exact field parity pytest | 통과: Normalized 37필드·ORM·Importer·목록/상세 API 계약 회귀 없음 |
| DTL4-4B Source 소비 fixture | 통과: 승인 Source 3종·적재 후보 5건, Schema issue 0건 |
| 천안 승인 공지 actual mapper | 통과: 요청 2회, Raw 3건, 정책 1건, Schema issue 0건 |
| Release snapshot strict offline replay | 통과: accepted 3,156, invalid 0, period safety pass |
| PostgreSQL 통합 경계 | 통과: Migration 0005→0006 기존 행 보존, canonical Seed→상세 API, 천안 Runtime 적재·재수집 멱등성 검증 |
| 결정적 Fixture 재생성 검사 | 통과: 관리 대상 15개와 생성 결과 일치 |
| 문서 검증 | 통과: `scripts/validate_docs.py` |
| diff 검사 | 통과: `git diff --check` (Windows CRLF 안내만 출력) |

Starlette 1.3.1 `TestClient`가 우선 사용하는 `httpx2`를 테스트 의존성에 추가했다.
운영 수집 HTTP client인 `httpx`는 그대로 유지했으며, Integration 05의 Forest·계획 색인
상태는 개별 승인 문서의 `approved`와 일치시켰다.

## 남은 작업

- Data output과 Backend DTO·DB·Migration·상세 API는 ES2에서 확정했다.
- Frontend는 상세 API를 기준으로 화면의 제외 조건·필요 서류·문의처와
  접근성 검증을 구현한다.
- Team Leader는 ES3 결과가 반영된 현재 Integration 브랜치에서 실제 DB → API → Browser를
  대조한다.
