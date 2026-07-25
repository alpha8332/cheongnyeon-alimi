# Data Pipeline Forest 개발 계획

## 계획 정보

- 담당 영역: Data
- 상태: draft
- 대상 기간: 데이터 파이프라인 기반 구축 Forest
- 관련 브랜치: 미정
- 개발 기록: 구현 시작 시
  `docs/development/development_notes/data/data_pipeline.md` 생성

## 목적

공식 API와 대표 공개 웹 소스에서 제한된 샘플을 수집하고, Raw 원문 보존부터
정규화·검증·Fixture 및 Seed 생성까지 이어지는 데이터 파이프라인 기준선을
구현한다. Backend와 Frontend가 합의된 샘플 데이터 계약을 사용해 후속 개발을
시작할 수 있게 한다.

## 범위

- 온통청년 공식 API 한 개의 제한된 Raw 수집
- 대표 HTTPS 웹사이트 한 개 또는 고정된 공개 HTML 샘플 검증
- 공통 HTTP Client와 기본 오류 처리
- Raw 원문, 수집 메타데이터와 SHA-256 Hash 보존
- 소스별 Extractor와 공통 Normalizer 및 Validator 기반
- 검토된 Fixture와 Seed 생성

초기 검증 목표:

- 온통청년 API 정책 10건 이상 Raw 수집
- 대표 웹 소스 상세 사례 3~5건 또는 고정 HTML 샘플 검증

## 범위 밖

- 온통청년 전체 데이터 수집
- 여러 웹사이트 동시 지원
- 정기 Scheduler
- 수정·삭제 자동 감지와 완전한 변경 이력
- 정교한 중복 판정
- LLM 기반 자격 조건 추출
- 운영 DB 직접 적재 자동화

## 선행 조건

- 온통청년 API의 공식 endpoint, 인증 방식과 이용 조건 확인
- 대표 HTTPS 웹 소스 선정
- `application_status` 등 미확정 데이터 계약 공동 검토
- 실제 비밀값을 제외한 로컬 실행 환경 준비

## 공통 설계 원칙

- Collector는 정규화하지 않는다.
- Raw 원문은 손실 없이 보존한다.
- 소스별 의미 해석은 Extractor가 담당한다.
- 공통 형식 변환은 Normalizer가 담당한다.
- Validator는 Schema 위반을 정상 데이터와 분리한다.
- 실제 운영 Raw와 비밀정보는 Git에 포함하지 않는다.
- 공통 기준은 `docs/data/` 문서를 따르고 이 계획에는 Forest 실행 범위만 둔다.

## Slice 계획

### Data 1 - 공통 모델과 HTTP 기반

- 상태: pending
- 목적: Collector가 공유할 Raw 계약과 HTTP 동작을 구현한다.
- 완료 기준: Timeout, 제한된 재시도, 요청 간격과 오류 구분을 테스트한다.

### Data 2 - 소스별 수집과 추출

- 상태: pending
- 목적: 공식 API와 대표 웹 샘플의 Raw 수집 및 Extractor를 구현한다.
- 완료 기준: 계획된 대표 사례를 Raw 손실 없이 수집·추출한다.

### Data 3 - 정규화와 검증

- 상태: pending
- 목적: 공통 `NormalizedProgram` 변환과 Schema 검증을 구현한다.
- 완료 기준: 정상·경계·실패 Fixture의 결과를 검증한다.

### Data 4 - Fixture와 Seed 계약

- 상태: pending
- 목적: Backend와 Frontend가 사용할 검토된 샘플 데이터를 제공한다.
- 완료 기준: 비밀정보·개인정보·재배포 조건을 확인하고 계약 문서와 동기화한다.

## 검증 계획

- HTTP Client와 Collector 단위 테스트
- XML, JSON과 HTML Fixture 기반 Extractor 테스트
- Normalizer 정상·경계·실패 테스트
- JSON Schema 검증 테스트
- Fixture와 Seed의 비밀정보 및 개인정보 검토
- `python scripts/validate_docs.py`

실제 외부 API 호출은 별도 통합 검증으로 구분하고 실행 조건과 결과를 기록한다.

## Forest 완료 기준

- Raw → Extracted → Normalized → Validated 흐름이 대표 샘플로 검증됨
- Backend와 Frontend가 사용할 Fixture 또는 Seed가 제공됨
- Schema와 `docs/data/` 기준 문서가 실제 구현과 일치함
- 실행한 테스트와 알려진 제약이 Data 개발 기록에 기록됨
- 의미 있는 변경이 `CHANGELOG.md`에 요약됨

## 위험과 미확정 사항

- 온통청년 API의 실제 endpoint, 응답 형식과 호출 제한
- 대표 HTTPS 웹사이트와 Selector
- 원문 저장 및 재배포가 가능한 라이선스 범위
- `application_status`와 카테고리 다중값 계약
- 실제 runtime Raw 저장 경로와 중복 판정 도입 시점

미확정 사항은 공식 자료와 실제 샘플을 확인하기 전까지 현재 동작으로 표현하지
않는다.

## 관련 문서

- [개발 계획 안내](../README.md)
- [데이터 문서 안내](../../../data/README.md)
- [데이터 소스](../../../data/data_sources.md)
- [데이터 Schema 기준선](../../../data/data_schema.md)
- [데이터 정규화 규칙](../../../data/normalization_rules.md)
- [데이터 수집 정책](../../../data/collection_policy.md)
