# Eligibility Summary 공통 계약

## 계약 정보

- 상태: approved
- 승인일: `2026-08-10`
- 계약 버전: `1.0.0`
- 실행 Schema:
  [`eligibility_summary.schema.json`](../../data/schema/eligibility_summary.schema.json)
- 대표 사례:
  [`eligibility_evidence_cases.json`](../../data/fixtures/contracts/eligibility_evidence_cases.json)
- 관련 Forest:
  [Integration 08 Eligibility Evidence and Summary](../development/develop_plan/integration/08_eligibility_evidence_summary.md)

## 목적과 현재 경계

이 계약은 정책 상세의 `eligibility_summary`에 들어갈 신청 조건·제외 조건·
우대 조건·필요 서류·확인 필요·시설 문의처의 공통 의미를 고정한다. Data의
Source mapper, Backend의 DB·API와 Frontend의 TypeScript·UI가 같은 필드명과
빈 값 의미를 사용한다.

DTL4-4A에서는 독립 Schema와 Python 모델, Source mapping 및 합성 fixture를
확정했다. DTL4-4B에서는 DB에 적재 가능한 합성 정책 4건과 승인 웹 Source
`notice:674` 합성 표본 1건의 mapper 결과를 정책 identity와 묶은
`source_handoff`를 대표 fixture에 추가했다. ES2에서는 이 객체를
`NormalizedProgram 1.2.0`의 37번째 required 필드로 편입하고 PostgreSQL
`policies.eligibility_summary` JSONB와 정책 상세 API까지 연결했다. 기존 1.0.0·
1.1.0 객체는 compatibility adapter가 조건을 추정하지 않고 `coverage=unknown`과
빈 배열만 추가해 1.2.0으로 승격한다. 기존 `eligibility_text`,
`required_conditions`, `preferred_conditions`, `excluded_conditions`는 제거하거나
새 구조로 추정 변환하지 않는다.

## 객체 구조

`eligibility_summary`는 다음 7개 필드를 항상 가진다.

| 필드 | 타입 | 의미 |
| --- | --- | --- |
| `coverage` | enum | `complete`, `partial`, `unknown` |
| `requirements` | condition 배열 | 신청자가 충족해야 하는 조건 |
| `exclusions` | condition 배열 | 해당하면 제외·지원 종료가 될 수 있는 조건 |
| `preferences` | condition 배열 | 우대·가점 조건 |
| `documents` | document 배열 | Source에 명시된 제출·구비 서류 |
| `unknowns` | condition 배열 | 의미 분류나 자동 비교가 안전하지 않은 원문 |
| `institutional_contacts` | contact 배열 | 공개 시설 대표전화·공식 문의 채널 |

복수 값은 누락 시에도 `[]`이며 `null`, 필드 생략과 단일 문자열은 허용하지
않는다. `[]`는 수집 시 해당 Source에서 승격 가능한 값을 찾지 못했다는 뜻이며,
조건·서류·연락처가 실제로 존재하지 않는다는 행정적 확정이 아니다.

### coverage

- `complete`: Source가 필요한 조건 영역을 명시적으로 제공했고 `unknowns=[]`인
  경우에만 사용한다. mapper가 단순히 필드 몇 개를 찾았다는 이유로 추정하지
  않는다.
- `partial`: 하나 이상의 조건·서류 원문은 있으나 누락·미분류·충돌이 남는다.
- `unknown`: 조건·제외·우대·서류·unknown 원문이 모두 없다. 시설 문의처만
  존재해도 자격 coverage를 `partial`로 올리지 않는다.

## condition과 document

`requirements`, `exclusions`, `preferences`, `unknowns`의 각 condition은 다음
필드를 가진다.

| 필드 | 타입 | 기준 |
| --- | --- | --- |
| `category` | enum | `age`, `region`, `income`, `asset`, `employment`, `education`, `housing`, `household`, `other` |
| `text` | string | 의미를 생성하거나 수치·단위를 바꾸지 않은 Source 원문 |
| `evidence` | evidence 배열 | 최소 1개, 중복 금지 |

`documents` 항목은 `text`, `evidence`를 가진다. 한 Source field가 여러 서류를
긴 문자열로 제공하고 안전한 항목 경계를 확정할 수 없으면 원문 전체를 한
document item으로 보존한다. 계산할 수 없거나 필수·제외를 안전하게 판별할 수
없는 원문은 삭제하지 않고 `unknowns`로 보낸다.

## 공개 evidence

각 evidence는 다음 필드를 모두 가진다.

| 필드 | 타입 | 기준 |
| --- | --- | --- |
| `source_id` | string | 등록된 Source ID |
| `source_url` | HTTP(S) URL | 사용자 정보가 없는 공식 원문 또는 안전한 fixture URL |
| `collected_at` | timezone date-time | 해당 근거를 수집한 절대 시각 |
| `locator_type` | enum | `source_field`, `css_selector` |
| `locator` | string | 정확한 API field 또는 승인 DOM selector |

이 evidence는 사용자에게 공개 가능한 근거 포인터다. 내부 Raw
`raw_document_id`, content hash, 저장 경로와 전체 provenance payload는 이
객체에 포함하지 않는다. Backend가 내부 추적 정보를 저장하더라도 공개 API는
위 5개 필드만 노출한다.

## 시설 연락처와 개인정보 경계

`institutional_contacts` 항목은 `kind`, `label`, `value`, `evidence`를 가진다.

- 허용 `kind`: `phone`, `official_channel`
- `phone`: 공개 시설 대표번호·접수센터 등 기관 번호만 허용
- `official_channel`: 기관이 명시한 공식 웹·카카오 등 문의 채널
- 개인 휴대전화(`010`, `011`, `016`, `017`, `018`, `019` 계열), 개인 이메일,
  담당자 성명은 승격하지 않는다.
- 이메일은 공식 주소인지 자동 판별하지 않고 이번 `1.0.0` contact kind에서
  제외한다.
- 연락처가 없으면 `[]`이며 기존 조건 문자열에 섞지 않는다.

## Source mapping 1.0.0

| Source | 공통 필드 | Source locator | 결정 |
| --- | --- | --- | --- |
| 온통청년 | `requirements` age | `sprtTrgtAgeLmtYn`, `sprtTrgtMinAge`, `sprtTrgtMaxAge` | 명시 연령 원문만 승격 |
| 온통청년 | `requirements` other | `addAplyQlfcCndCn` | 추가 신청자격 원문 보존 |
| 온통청년 | `unknowns` other | `ptcpPrpTrgtCn` | 실제 응답에 대상·제외 문장이 함께 있어 자동 분류 금지 |
| 온통청년 | `documents` | `sbmsnDcmntCn` | 비어 있지 않은 원문 전체 보존 |
| 복지로 | `requirements` other | `tgtrDtlCn` | 상세 지원 대상 원문 보존 |
| 복지로 | `unknowns` other | `slctCritCn` | 선정 기준을 필수·우대로 추정하지 않음 |
| 천안청년센터 웹 | `requirements` other | `#bo_v_con`의 `eligibility` section | section text 보존 |
| 천안청년센터 웹 | `exclusions` other | `#bo_v_con`의 `excluded_conditions` section | section text 보존 |
| 천안청년센터 웹 | `documents` | `#bo_v_con`의 `required_documents` section | section text 보존 |
| 천안청년센터 웹 | `unknowns` other | `#bo_v_con`의 `other_conditions` section | 자동 비교 금지 |
| 천안청년센터 웹 | `institutional_contacts` | `#bo_v_con`의 `contact` section | 공개 대표전화·공식 채널만 승격 |

온통청년·복지로 현재 응답에는 승인된 시설 연락처 field가 없어 연락처를
추정하지 않는다. API와 웹의 source-scoped identity는 유지하며 서로 다른
원문이 충돌하면 최신 시각을 근거로 덮어쓰지 않고 각각의 evidence와 함께
`partial`·`unknowns` 사례로 보존한다.

## 소비자 인계 fixture

`eligibility_evidence_cases.json`의 `source_handoff`는 Backend DTO와 Frontend
TypeScript·Mock이 같은 Data JSON을 소비하는지 확인하기 위한 결정적 입력이다.
각 항목은 `source_id`, `external_id`, `title`, `eligibility_summary`를 가지며,
온통청년 2건·복지로 2건·천안청년센터 웹 1건을 포함한다. invalid 정책은
소비자 fixture에서 제외한다.

이 envelope는 여전히 `NormalizedProgram`이나 공개 API DTO 전체가 아니라 소비자
대조용 부분 fixture다. canonical Seed와 실제 정규화 출력은 동일한
`eligibility_summary` 객체를 1.2.0 Schema 안에 포함한다. Frontend는 이 파일의
바깥 필드를 API 응답으로 추정하지 않고 상세 API의 객체와 직접 대조한다.

## 저장과 공개 API 경계

- PostgreSQL은 Migration `20260810_0006`부터 요약 전체를 non-null JSONB로
  저장한다. 기존 행의 `schema_version`은 소급 변경하지 않고 빈 unknown 요약만
  backfill한다.
- `GET /api/v1/policies/{policy_id}` 상세 응답은 `eligibility_summary`를 항상
  노출한다. 목록·검색 응답은 payload 호환과 크기를 위해 이 필드를 노출하지 않는다.
- 공개 evidence에는 이 문서의 5개 필드만 포함한다. 내부 provenance의 Raw ID·hash·
  저장 경로는 상세 API에 노출하지 않는다.
- evidence의 `collected_at`만 달라지고 조건·문서·연락처·locator가 같은 재수집은
  정책 내용 변경으로 세지 않는다. 실제 요약 내용이나 근거 위치 변화는 update다.

## Frontend 표시 경계

- 상세 화면은 신청·제외·우대 조건, 필요 서류, 추가 확인 필요와 문의처를 각각
  구분한다. 빈 배열은 항목을 숨기지 않고 원문에서 구조화된 값을 확인하지
  못했다는 문구로 표시한다.
- `complete`·`partial`·`unknown`은 coverage 정보이며 신청 가능·불가 판정으로
  바꾸지 않는다. 개인 조건 비교 입력이 없으면 일치·불일치 상태도 만들지 않는다.
- 시설 대표전화만 `tel:` 링크로 제공한다. 공식 채널은 값이 HTTP(S) URL인
  경우에만 외부 링크로 만들고, 채널명 같은 텍스트는 그대로 표시한다.
- 각 항목의 공개 evidence는 새 창 원문 링크, Source ID, KST 수집 시각과 locator를
  표시한다. 모바일에서는 1열로 재배치하고 전화·근거 링크의 keyboard focus를
  유지한다.

## 소비자 문구

- 허용: `핵심 신청 조건`, `제외 조건`, `필요 서류`, `문의처`,
  `조건상 일치`, `조건상 불일치`, `추가 확인 필요`
- 금지: `신청 가능`, `신청 불가`, `선정 확률`, `수혜 확정`처럼 행정기관의
  최종 판단을 대신하는 단정
- 모든 요약은 공식 원문 링크와 함께 제공하고 `partial`·`unknown`을 숨기지
  않는다.

## 변경 규칙

필드 삭제·이름 변경·필수 여부 완화처럼 기존 객체를 무효화하는 변경은 major,
기존 객체를 계속 허용하는 추가는 minor로 올린다. Schema, Python 모델, 대표
fixture, Backend OpenAPI와 Frontend TypeScript 소비 검토를 같은 Integration
Forest에서 갱신한다.
