# 데이터 문서

이 디렉터리는 정책 데이터의 출처, 계약, 수집과 정규화 기준을 관리한다.

## 포함하는 내용

- 공식 API와 공개 웹사이트 등 데이터 출처
- Raw, Extracted, Normalized 데이터의 책임과 Schema
- 날짜, 지역, 연령, 카테고리 등의 정규화 규칙
- 원문 보존, Hash, 중복, 누락값과 품질 상태 정책
- Fixture, Seed, 런타임 데이터의 구분
- 데이터 출처의 이용 조건과 개인정보 보호 기준

## 현재 문서

- [데이터 소스](data_sources.md)
- [API Source Profile](source_profiles.md)
- [데이터 Schema 기준선](data_schema.md)
- [Eligibility Summary 공통 계약](eligibility_summary_contract.md)
- [데이터 정규화 규칙](normalization_rules.md)
- [데이터 수집 정책](collection_policy.md)
- [Fixture와 Seed 계약](fixture_seed_contract.md)
- [행정구역 기준정보](administrative_regions.md)
- [Release 1 실데이터 품질 Profile](release_dataset_profile.md)

## 실행 가능한 Schema

- [RawPolicyDocument JSON Schema](../../data/schema/raw_policy_document.schema.json):
  원본 byte와 목록·항목·상세 연결 메타데이터 계약
- [NormalizedProgram JSON Schema](../../data/schema/normalized_program.schema.json):
  정규화 필드, null·배열·enum, provenance와 품질 상태 계약
- [EligibilitySummary JSON Schema](../../data/schema/eligibility_summary.schema.json):
  조건·서류·공개 시설 연락처와 항목별 Source evidence 계약
- [Regional Youth Policy Source Inventory JSON Schema](../../data/schema/regional_youth_policy_source_inventory.schema.json):
  17개 지역 포털 후보·preflight·승인 경로와 행정구역 mapping 상태 계약
- [Supplemental Official Policy Inventory JSON Schema](../../data/schema/supplemental_official_policy_inventory.schema.json):
  Data 06 XLSX 후보 lineage·오류 격리와 공식 Source preflight 계약
- [Supplemental Duplicate Audit JSON Schema](../../data/schema/supplemental_official_policy_duplicate_audit.schema.json):
  승인 aggregator snapshot·PostgreSQL 선행 중복 판정 계약
- [Review Admission 규칙](review_admission_rules.md):
  taxonomy v2, hard exclusion과 versioned review 승격 계약
- [Review Admission Audit JSON Schema](../../data/schema/review_admission_audit.schema.json):
  identity-only 판정 manifest와 hash 검증 계약

## 실행 가능한 개발 데이터

- [Normalized Fixture](../../data/fixtures/normalized/programs.json)
- [Eligibility Summary 계약 Fixture](../../data/fixtures/contracts/eligibility_evidence_cases.json)
- [Canonical 개발 Seed](../../data/seeds/initial_programs.json)
- [행정구역 Seed](../../data/seeds/administrative_regions.json)
- [행정구역 별칭 Seed](../../data/seeds/administrative_region_aliases.json)
- [지역 청년정책 Source inventory](../../data/reference/regional_youth_policy_sources.json)
- [Data 06 후보·Source inventory](../../data/reference/supplemental_official_policy_inventory.json)
- [Data 06 선행 중복 감사](../../data/reference/supplemental_official_policy_duplicate_audit.json)
- [Review Admission 계약 Fixture](../../data/fixtures/contracts/review_admission_cases.json)

Normalized Fixture와 canonical 개발 Seed는 결정적으로 재생성되는 같은 JSON
계약이며 실제 API 원문이 아닌 합성 데이터다. 행정구역 두 Seed는 잠긴 공식
법정동 snapshot에서 별도로 재생성한다. Raw·Extracted·rejected 경계와 명령은
[Fixture와 Seed 계약](fixture_seed_contract.md)을 따른다.

## 포함하지 않는 내용

- 미확정 데이터 설계: `docs/development/develop_plan/`
- PostgreSQL의 물리 테이블과 마이그레이션 구현 상세
- Collector 실행, 재시도와 장애 복구 절차: `docs/operations/`
- API 응답 계약: `docs/api/`

데이터 문서는 실제 JSON Schema, Fixture와 코드의 동작을 기준으로 유지한다.
미확정 규칙은 확정된 데이터 계약과 명확히 구분한다.
