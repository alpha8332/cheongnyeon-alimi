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
확정했다. 현재 `NormalizedProgram 1.1.0`, Policy DB·Migration, 공개 API와
Frontend 타입에는 아직 이 객체를 편입하지 않았다. 이 계약을 병합한 뒤
Backend와 Frontend가 각 소유 브랜치에서 구현하고, Data의 정규화 편입은
`NormalizedProgram 1.2.0` 호환 추가로 검토한다. 기존 `eligibility_text`,
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
