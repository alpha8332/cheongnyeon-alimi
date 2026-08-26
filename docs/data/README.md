# 데이터 문서

이 디렉터리는 현재 정책 데이터의 출처, Schema, 수집·정규화, 공개 범위와
생명주기 계약을 관리한다.

## 핵심 문서

- [데이터 소스](data_sources.md): 등록 수집기 11개와 공개 Source 3개의 차이
- [데이터 수집 정책](collection_policy.md): HTTP, Raw, 비밀정보와 실패 경계
- [데이터 Schema](data_schema.md): Raw·Extracted·Normalized 필드 계약
- [정규화 규칙](normalization_rules.md): 날짜·지역·연령·분야 판정
- [Eligibility Summary](eligibility_summary_contract.md): 자격 조건과 evidence
- [Fixture와 Seed](fixture_seed_contract.md): 합성 개발 데이터와 재생성
- [행정구역 기준](administrative_regions.md): 법정동 code·별칭·상하위 관계
- [Review Admission](review_admission_rules.md): 웹 정책 검토·승격 규칙
- [정책 생명주기](policy_lifecycle.md): active·inactive·재등장·종료일
- [공개 정책 dataset](public_policy_dataset.md): 재배포 allowlist와 artifact
- [환경 간 동등성](public_dataset_parity.md): 활성 membership과 identity hash

## 실행 가능한 계약

| 계약 | 경로 |
| --- | --- |
| Raw envelope | `data/schema/raw_policy_document.schema.json` |
| 정규화 정책 | `data/schema/normalized_program.schema.json` |
| 자격요건 요약 | `data/schema/eligibility_summary.schema.json` |
| 공개 Source allowlist | `data/reference/public_policy_dataset_sources.json` |
| 공개 manifest | `data/schema/public_policy_dataset_manifest.schema.json` |
| latest pointer | `data/schema/public_policy_dataset_pointer.schema.json` |
| 행정구역 | `data/seeds/administrative_regions.json` |
| 행정구역 별칭 | `data/seeds/administrative_region_aliases.json` |

## 데이터 범위 구분

| 범위 | 설명 | Git 포함 |
| --- | --- | --- |
| 합성 Fixture·Seed | 테스트와 개발용 결정적 데이터 | 포함 |
| Runtime Raw·rejected | 실제 수집 원문과 처리 산출물 | 제외 |
| PostgreSQL 전체 정책 | 로컬 수집·과거 정책 포함 가능 | 제외 |
| 공개 dataset | 허용 Source·필드와 안전 Gate를 통과한 normalized 정책 | GitHub Release |

현재 공개 수치는 [공개 정책 dataset](public_policy_dataset.md)과 함께 받은
manifest를 따른다. PostgreSQL 전체 row 수나 CollectionRun 수를 공개 정책
수로 사용하지 않는다.
