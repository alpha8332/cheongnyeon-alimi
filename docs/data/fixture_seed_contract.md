# Fixture와 Seed 계약

## 문서 상태

- 상태: 기술 기준선
- Data 검증: 완료
- Backend 승인: 완료
- Frontend 승인: 완료
- 기준 Schema: `NormalizedProgram` 1.2.0

이 문서는 외부 네트워크 없이 Raw부터 Seed까지 재현하는 개발 데이터와
Backend·Frontend 소비 규칙을 정의한다. 실제 API 응답을 배포하는 자료가
아니며 모든 정책 내용과 식별자는 합성 데이터다.

## 담당자 착수 안내

Backend와 Frontend는 현재 Schema와 Seed로 기능 구현을 시작할 수 있다.
다만 구현 시작 가능 상태와 공동 계약 승인 완료는 다르다.

1. 담당 Agent는 이 문서의 소비 계약과 영역별 검토 항목을 먼저 읽는다.
2. Backend는 importer·API 테스트, Frontend는 타입·Mock 소비 테스트로
   실제 사용 가능성을 확인한다.
3. 확인 결과와 변경 요청을 아래 공동 검토 기록에 남긴다.
4. 두 영역이 승인한 뒤에만 Data 6와 Data Pipeline Forest를 완료 처리한다.

계약 변경이 필요하면 Python 모델, JSON Schema, Fixture, Seed와 영향 문서를
같은 변경에서 동기화한다.

## 산출물

| 경로 | 역할 | 레코드 |
| --- | --- | ---: |
| `data/fixtures/raw/` | 두 소스의 합성 Raw envelope | 8 |
| `data/fixtures/extracted/policies.json` | Extractor 결과 | 5 |
| `data/fixtures/normalized/programs.json` | valid·partial 결과 | 4 |
| `data/fixtures/rejected/programs.json` | invalid와 실패 사유 | 1 |
| `data/fixtures/contracts/policy_search_region_cases.json` | 검색 범위·지역 관계 경계 사례 | 7 |
| `data/fixtures/contracts/recurrent_quality_cases.json` | 반복·수정·중복·실패 판정 사례 | 6 |
| `data/fixtures/contracts/eligibility_evidence_cases.json` | 자격요건 계약 사례와 Source 소비 인계 | 5+5 |
| `data/fixtures/regional/regional_policy_gate_cases.json` | 지역 고유성·신청 상태 Gate 합성 사례 | 12 |
| `data/fixtures/regional/cross_source_duplicate_cases.json` | aggregator 교차 Source 판정 합성 사례 | 7 |
| `data/seeds/initial_programs.json` | canonical 개발 Seed | 4 |
| `data/seeds/administrative_regions.json` | versioned 지역 Seed | 538 |
| `data/seeds/administrative_region_aliases.json` | 지역 별칭 Seed | 1,080 |

Normalized Fixture와 canonical Seed는 byte가 같은 JSON 배열이다. rejected는
정상 Seed에 포함하지 않는다. 현재 Backend가 CSV importer를 요구하지 않았고
CSV는 배열·null 표현을 약화하므로 생성하지 않는다.

지역 교차 Source fixture는 실제 aggregator 응답이나 정책을 복제하지 않는다.
합성 identity로 exact 제외 3종, fingerprint·근거 부족 review 2종과 동일 제목
다른 사업·신규 정책 승인 2종을 결정적으로 검증하며 canonical Seed에는 넣지
않는다.

## 합성 Raw 경계

Raw Fixture는 실제 응답에서 확인한 JSON·XML 문서 역할과 필드 이름만
재현한다.

- 모든 external ID는 `SYN-`으로 시작한다.
- URL은 네트워크에서 사용되지 않는 `fixture.invalid` host만 사용한다.
- 정책명·기관·지원 내용은 실제 정책을 복사하지 않은 합성 문구다.
- 인증 파라미터, 인증키, 개인정보와 실제 API 응답 byte를 포함하지 않는다.
- 고정된 문서 ID·수집 시각·payload로 Hash와 provenance를 결정적으로 만든다.

운영 `runtime/raw/`는 생성 입력이나 fallback으로 사용하지 않는다. 따라서
로컬에 운영 Raw가 없어도 같은 결과를 만들 수 있다.

## 대표 사례

| ID | Source | 품질 | 대표 계약 |
| --- | --- | --- | --- |
| `SYN-YOUTH-001` | 온통청년 | valid | 연령 범위, 서울, 특정 기간, closed |
| `SYN-YOUTH-002` | 온통청년 | valid | 연령 제한 없음, 전국, 다중 category, always·open |
| `SYN-BOK-001` | 복지로 | partial | 목록·상세 결합, 다중 관심주제, 지역·연령·기간 null |
| `SYN-BOK-002` | 복지로 | partial | 목록만 존재, category·지역 배열 비어 있음 |
| `SYN-YOUTH-REJECTED` | 온통청년 | invalid | 필수 제목 누락과 `$.title` 오류 |

검색 계약 Fixture 7건은 전국, 상위 지역, 정확 지역, 제외 지역, 지역 미확인,
동명이인, 폐지 코드를 합성 정책과 원문 근거로 표현한다. PSF2 이후 canonical
지역 identity는 실제 `kr-bjd-20260803` code를 사용하며 정책 내용과 Source
응답은 계속 합성이다.

partial도 JSON Schema를 통과한 정상 전달 객체다. 검색 정보가 일부
부족하다는 품질 상태를 보존하며, invalid만 정상 Fixture와 Seed에서
분리한다.

반복 품질 계약 Fixture는 canonical Seed의 0·1번 합성 정책을 참조하고 실제
정책 객체를 복제하지 않는다. 동일 snapshot, 수집 metadata만 변경, business
field 1개 변경, 실행 내 duplicate, invalid batch와 persist 실패의 기대 집계를
고정한다. 외부 네트워크와 Runtime Raw를 사용하지 않는다.

자격요건 계약 Fixture의 `cases`는 정상·경계·긴 문장·누락·충돌 의미를,
`source_handoff`는 canonical Seed에 포함되는 API 정책 4건과 승인 웹 Source
합성 표본 1건의 mapper 출력을 고정한다. `source_handoff` envelope는
`NormalizedProgram`·공개 API DTO 전체가 아니며 `eligibility_summary` nested
객체의 Backend·Frontend 소비 대조에만 사용한다. canonical Seed 자체에는 같은
객체가 1.2.0 required 필드로 포함된다.

## canonical JSON 소비 계약

`initial_programs.json`의 root는 `NormalizedProgram` 객체 배열이다.

- 모든 객체는 Schema의 37개 key를 가진다.
- 선택 단일 값 없음은 `null`, 복수 값 없음은 `[]`이다.
- enum과 `YYYY-MM-DD` 날짜는 JSON string으로 유지한다.
- `source_id + external_id`를 source-scoped 식별 경계로 사용한다.
- `data_quality_status`가 `valid` 또는 `partial`인 객체만 포함한다.
- Raw document ID·역할·Hash·시각·안전 URL provenance를 그대로 보존한다.
- 배열을 단일 string으로, null을 빈 문자열로 바꾸지 않는다.
- 검색 문자열 배열은 값이 없으면 `[]`, 범위를 확인하지 못하면
  `coverage_scope=unknown`, 지역 rule이 없으면 `region_rules=[]`이다.
- `eligibility_summary`는 7개 required 필드를 가지며 근거가 없는 Source는
  `coverage=unknown`과 빈 배열을 사용한다.

PSF4 canonical Seed는 합성 Source 원문에서 확인되는 summary·keywords와
복지로 life stages·target groups를 채운다. 합성 온통청년의 명시적 `전국`은
`coverage_scope=nationwide`, 그 밖에 근거가 없는 범위는 `unknown`이다.
기존 1.0.0 입력은 compatibility adapter가 안전한 빈 배열·`unknown`만 보완하고
검색 조건을 추정하지 않는다. Backend importer는 검색 배열·coverage,
`region_rules` 관계와 versioned projection을 Policy와 같은 transaction에
저장한다.

### Backend 검토 항목

- JSON 배열을 적재 입력으로 받을지 별도 importer를 둘지 결정
- `source_id + external_id` uniqueness와 upsert 경계 확인
- partial 적재 여부와 품질 필터 동작 확인
- provenance의 DB 보존 범위와 외부 API 노출 여부 결정
- 날짜 string을 DB date로 바꿀 때 null과 원문 text 보존 확인

### Frontend 검토 항목

- `categories`, `regions`와 조건 필드를 항상 배열로 처리
- 선택 단일 필드를 nullable로 처리하고 빈 문자열로 치환하지 않음
- `application_schedule`과 `application_status`를 다른 의미로 표시
- partial 표시 또는 누락 필드 fallback 정책 확인
- provenance를 일반 화면에 노출할지 관리자 화면에만 사용할지 결정

### Frontend D0 인계 항목

Frontend가 타입과 Mock을 구현할 때 canonical Seed를 공개 API DTO로 그대로
간주하지 않는다. 다음 경계를 기준으로 실제 소비 가능 여부를 확인한다.

| 항목 | 소비 계약 |
| --- | --- |
| 타입 기준 | 목록의 `items` 원소와 상세 응답은 `docs/api/policies.md`의 동일한 Policy DTO를 사용 |
| nullable | 선택 단일 값과 `application_schedule`·`application_status`는 `null`을 허용하고 빈 문자열로 바꾸지 않음 |
| 배열 | `categories`, `regions`와 5개 조건 배열은 값이 없어도 `[]`이며 nullable로 만들지 않음 |
| 일정·상태 | 신청 방식인 `application_schedule`과 현재 상태인 `application_status`를 별도 필드와 의미로 표시 |
| partial | 기본 목록·상세에서는 제외하고 명시적인 `include_partial=true` 요청에서만 소비 |
| provenance | canonical Seed와 DB에는 보존하지만 일반 사용자 Policy DTO에는 포함하지 않음 |
| 시각 | `collected_at`, `created_at`, `updated_at`의 offset 표현이 아니라 절대 시각으로 해석 |
| Mock | canonical Seed의 4개 대표 사례를 사용하되 공개 DTO에 없는 `provenance`는 제거하고 DB 생성 필드를 API 예시에 맞게 추가 |

Frontend 승인 증거는 위 경계를 반영한 TypeScript 타입·Mock 소비 테스트 또는
담당자 명시적 검토 기록이다. `feature/frontend/policy-discovery`의 FE 2A에서
공개 DTO·endpoint, pagination, partial 기본 노출과 상세 ID 계약을 코드와
소비 테스트에 반영했다. 테스트 7건·lint·build와 실제 PostgreSQL API HTTP
검증을 통과했고, 실제 API 모드 브라우저 캡처에서 기본 valid 2건과 공개
필드 렌더링을 확인해 D0의 Frontend 승인을 완료했다.

현재 저장소에는 Backend `Policy` 모델, Seed importer와 정책 목록·상세 API
기준선이 있고 Backend 소비 검토는 완료됐다. Backend 02 B2에서 최초 Alembic
revision과 PostgreSQL JSONB·enum·timezone 물리 매핑을 추가했으며 SQLite
단위 테스트, PostgreSQL offline SQL과 PostgreSQL 17.10 실제 Migration·왕복
검증을 완료했다. Backend 02 B3에서는 현재 두 공식 API의 비어 있지 않은
`external_id` admission과 `(source_id, external_id)` PostgreSQL 원자적
upsert를 구현했다. 같은 Seed의 반복·동시 입력은 중복 없이 unchanged로
분류하며 null ID는 확인 가능한 사유와 함께 적재하지 않는다. Normalized
Schema의 nullable 계약은 유지하고 향후 Source의 대체 ID는 별도로 결정한다.
Backend 02 B4에서는 기존 `NormalizedProgramValidator`로 전체 입력을 먼저
검증하고 `valid`·`partial`만 허용한다. invalid·Schema 위반·DB admission
거부·DB write 실패가 하나라도 있으면 canonical batch의 DB 변경은 0건이다.
`--dry-run`도 실제 upsert 경로를 실행한 뒤 rollback하며 결과는
validated·inserted·updated·unchanged·duplicate·skipped·rejected·failed로
구분한다. invalid는 검증 실패이면서 rejected에 포함되고, identity admission
거부는 rejected로 집계한다.
Backend 02 B5에서는 category·region을 정규화 배열의 정확한 원소로 검색하고
목록·상세 모두 기본 valid, `include_partial=true`일 때 valid·partial을
노출한다. provenance는 DB에 보존하되 공개 Policy DTO에는 포함하지 않는다.
Backend 02 B6의 PostgreSQL 18.4 종단 검증은 당시 canonical Seed 4건의 기존
31개 필드와 ORM 값을 비교해 null·빈 배열·enum·날짜·timezone
instant·provenance 손실 0건을 확인했다. PSF1의 1.1.0 canonical Seed는 새
검색 필드가 안전한 기본값일 때 호환된다. PSF3는 정책 검색 컬럼과 지역·규칙·
projection 구조의 PostgreSQL 왕복을 검증했다. PSF5는 실제 36개 입력의
관계형 transaction·idempotency·rollback을 검증했다.
ES2는 1.2.0의 37개 입력과 `eligibility_summary` JSONB·상세 API 왕복,
1.0.0·1.1.0 compatibility를 검증했다. 목록·검색 공개 DTO에는 새 요약을
추가하지 않는다.
Frontend TypeScript 타입·Mock 소비 코드는 별도 원격 브랜치에 있으나 D6
검토에서 현재 Policy API와의 계약 차이를 확인했다. Data 영역은 해당
Frontend 코드를 대신 수정하거나 승인하지 않으며,
[`Policy API 계약`](../api/policies.md)의 D6 인계 기준을 반영한 소비 테스트를
요구한다.

## 재생성과 검증

저장된 합성 사례로 전체 산출물을 다시 쓴다.

```powershell
uv run python -B scripts/build_data_fixtures.py --write
```

커밋된 파일이 결정적 재생성 결과와 같은지만 확인한다.

```powershell
uv run python -B scripts/build_data_fixtures.py --check
```

`--check`는 외부 API와 `runtime/raw/`를 사용하지 않는다. 이 생성기가 소유한
Fixture 13개와 `initial_programs.json`의 누락·추가·byte 차이가 있으면
실패한다. 행정구역 Seed는 별도 생성기의 `--check`로 검증한다.

```powershell
.\.venv\Scripts\python.exe -B scripts/build_administrative_regions.py `
  --snapshot-date 2026-08-03 --check
```

## 출처·개인정보·재배포 검토

2026-07-26에 다음 공식 자료를 확인했다.

- [복지로 중앙부처 복지서비스 API][bokjiro-api]는 이용허락범위를
  `제한 없음`으로 표시한다.
- [온통청년 OPEN API 이용방법][youth-api-guide]은 회원가입, 인증키 신청과
  담당자 승인을 요구한다.
- [온통청년 이용약관][youth-terms]은 대량 이용을 별도 계약 대상으로 두고,
  서비스에서 얻은 게시 자료의 무단 상업적 가공·판매를 제한한다.

온통청년 정책 API 원문의 저장·변환·Git 재배포 범위가 명시적으로 확인되지
않았으므로 실제 원문은 포함하지 않는다. 복지로도 소스 간 일관성, 최소성,
개인정보와 시점 의존성을 위해 실제 원문 대신 합성 Fixture를 사용한다. 이는
법률 판단이 아니라 저장소의 보수적인 재배포 경계다.

## 공동 검토 기록

| 영역 | 상태 | 확인 결과 또는 필요한 증거 |
| --- | --- | --- |
| Data | reviewed | 1.2.0 Schema·1.0.0/1.1.0 adapter·결정적 재생성·Eligibility mapping 테스트 완료 |
| Backend | reviewed | Eligibility JSONB·Migration·상세 DTO와 원자적 importer·idempotency·rollback 검증 완료 |
| Frontend | transitional | 목록 `PolicyDto`는 기존 공개 경계를 유지하며 1.2.0 union과 상세 `eligibility_summary` 소비는 ES3에서 반영 |

### Frontend 초기 Mock 검토 결과 (2026-07-28)

`feature/frontend/policy-discovery`의 `784a2a8`은 canonical Seed 4건을
TypeScript·Mock·와이어프레임 UI로 소비했다. 다음 표현 동작은 확인했다.

- nullable 단일 값은 표시 시점에만 fallback을 적용한다.
- 복수 값 필드는 배열로 처리하고 빈 배열의 안내 문구를 표시한다.
- 다중 `categories`를 태그 목록으로 표시한다.
- `application_schedule`과 `application_status`를 별도 의미로 표시한다.
- partial 배지와 구조화 값 누락 시 원문 text fallback을 제공한다.

다만 이 결과만으로 공개 API 소비를 승인하지 않는다. Frontend는 사용자
타입에서 `provenance`·`invalid`를 제외하고 `/api/v1/policies`의 pagination
envelope와 숫자 `id` 상세 경로를 사용해야 한다. 기본 조회에서는 valid만,
명시적인 `include_partial=true` 요청에서만 partial을 노출하도록 Mock과
API Client를 맞춘 뒤 소비 테스트 또는 담당자 재검토 기록을 남긴다.

### Frontend API 계약 반영 (2026-07-30)

FE 2A는 위 변경 요청을 타입·Mock·API Client와 화면에 반영했다. canonical
Seed의 provenance·invalid 입력 경계는 Mock adapter 내부에만 두고 공개
`PolicyDto`에서는 제거한다. 기본 valid 2건과 partial opt-in 4건,
pagination envelope와 숫자 `id` 목록·상세 경계를 같은 Mock contract로
구현했다. 소비 테스트 7건·lint·build, PostgreSQL 실제 API HTTP와 실제
API 모드 브라우저 렌더링을 확인해 Frontend 소비 승인을 완료했다.

기존 Data 6의 31개 필드 소비 계약은 승인 상태를 유지한다. PSF4는 새 검색
필드의 Source 값 채움과 합성 Seed 재생성을 완료했다. Backend의 배열·coverage
저장은 PSF3, 관계·projection의 원자적 저장은 PSF5에서 완료됐다. 별도 검색
응답 소비 승인은 후속 Slice에서 완료한다.

[bokjiro-api]: https://www.data.go.kr/data/15090532/openapi.do
[youth-api-guide]: https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiGuide
[youth-terms]: https://www.youthcenter.go.kr/cmnFooter/termsInfo
