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
- [데이터 정규화 규칙](normalization_rules.md)
- [데이터 수집 정책](collection_policy.md)

## 실행 가능한 Schema

- [RawPolicyDocument JSON Schema](../../data/schema/raw_policy_document.schema.json):
  원본 byte와 목록·항목·상세 연결 메타데이터 계약

## 포함하지 않는 내용

- 미확정 데이터 설계: `docs/development/develop_plan/`
- PostgreSQL의 물리 테이블과 마이그레이션 구현 상세
- Collector 실행, 재시도와 장애 복구 절차: `docs/operations/`
- API 응답 계약: `docs/api/`

데이터 문서는 실제 JSON Schema, Fixture와 코드의 동작을 기준으로 유지한다.
미확정 규칙은 확정된 데이터 계약과 명확히 구분한다.
