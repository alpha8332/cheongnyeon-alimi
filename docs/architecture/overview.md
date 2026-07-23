# 시스템 아키텍처 개요

## 문서 상태

- 상태: 기준선
- 대상: `cheongnyeon-alimi`
- 현재 구현 상태: 문서 기반 구축 단계

이 문서는 팀이 구현 과정에서 따라야 할 목표 아키텍처와 책임 경계를
정의한다. 현재 저장소에 실행 코드나 컨테이너가 존재한다는 의미는 아니다.
구현이 시작되면 실제 코드와 배포 구성이 이 기준선과 일치하는지 함께
검증한다.

## 시스템 목적

`cheongnyeon-alimi`는 공공기관의 청년정책을 수집하고 공통 형식으로 정제해,
사용자가 정책을 검색하고 추천받을 수 있도록 제공하는 오픈소스 웹
플랫폼이다. 데이터 출처와 수집 상태를 추적하고 관리할 수 있는 운영 기능도
같은 시스템에 포함한다.

## 전체 구조

```text
External Sources
→ Collector
→ RawPolicyDocument
→ Source Extractor
→ ExtractedPolicy
→ Normalizer
→ NormalizedProgram
→ Validator
→ Fixture / Seed 또는 PostgreSQL
→ FastAPI
→ React
```

자세한 데이터 흐름과 실패 처리는 [시스템 흐름](system_flow.md), 초기 실행
단위는 [컨테이너 구조](container_structure.md)에서 설명한다.

## 아키텍처 영역

### 외부 데이터 소스

공식 API와 공개 HTTPS 웹사이트가 대상이다. 각 소스의 응답 구조, 이용 조건과
변경 주기는 서로 다르므로 소스별 처리는 공통 계층과 분리한다.

### 데이터 파이프라인

최상위 `collectors/` 모듈이 수집, 소스별 추출, 공통 정규화와 검증을 담당한다.
데이터 파이프라인은 백엔드 API 라우터에 포함시키지 않는다.

### 데이터 계약과 개발 데이터

`data/schema/`의 JSON Schema가 데이터·백엔드·프론트엔드 사이의 논리적
계약이다. `data/fixtures/`와 `data/seeds/`는 실제 Collector나 DB가 준비되기
전에도 병렬 개발과 테스트를 가능하게 한다.

### Backend

FastAPI가 정책 조회, 검색, 추천, 사용자 기능과 관리자 기능의 HTTP 경계를
제공한다. API Route는 요청·응답을 담당하고, 비즈니스 로직과 DB 접근은
Service와 Repository 계층으로 분리한다.

### Database

PostgreSQL이 정규화된 서비스 데이터, 출처, 수집 실행과 사용자 기능 데이터를
저장한다. JSON Schema는 논리적 데이터 계약이고 DB Schema와 Migration은
물리적 저장 구조이므로 서로 대신하지 않는다.

### Frontend

React와 TypeScript가 사용자 및 관리자 웹 UI를 제공한다. 확정된 API 계약과
타입을 사용하며, 백엔드가 준비되지 않았을 때는 같은 계약을 따르는 Mock 또는
Fixture를 사용한다.

## 계층별 책임

| 계층 | 입력 | 책임 | 출력 |
| --- | --- | --- | --- |
| Collector | 외부 API·HTML | 요청, 응답 확인, 원문 추출, 출처 기록 | `RawPolicyDocument` |
| Raw Storage | `RawPolicyDocument` | 원문과 수집 메타데이터 보존 | 재처리 가능한 Raw |
| Source Extractor | 소스별 Raw | XML 태그·CSS Selector 등 소스 의미 해석 | `ExtractedPolicy` |
| Normalizer | `ExtractedPolicy` | 공통 필드 매핑과 날짜·지역·연령 변환 | `NormalizedProgram` |
| Validator | `NormalizedProgram` | JSON Schema와 품질 규칙 검증 | valid·partial 또는 rejected 결과 |
| Fixture·Seed | 검증된 데이터 | 병렬 개발과 초기 DB 구성 지원 | JSON Fixture·CSV Seed |
| PostgreSQL | 검증된 서비스 데이터 | 조회 가능한 영속 저장 | 프로그램과 관련 데이터 |
| FastAPI | DB 또는 합의된 Seed | 조회·검색·추천 및 운영 API | API 응답 |
| React | API 응답 또는 Mock | 사용자·관리자 상호작용 | Web UI |

## 고정된 책임 경계

### Collector는 정규화하지 않는다

Collector는 외부 요청과 원문 획득까지만 책임지고 `RawPolicyDocument`를
반환한다. 날짜, 지역, 연령과 카테고리 변환을 Collector에 넣지 않는다.

### Raw 원문은 손실 없이 보존한다

정규화 과정에서 사용하지 않는 필드도 Raw 단계에서 임의로 삭제하지 않는다.
출처 URL, 수집 시각, 응답 형식과 Hash 등 재현 및 변경 확인에 필요한
메타데이터를 함께 보존한다.

### 소스별 의미 해석은 Extractor가 담당한다

Extractor는 API 필드, XML 태그와 HTML Selector를 알고 있지만 공통 서비스
표현을 결정하지 않는다. 소스 구조가 바뀌면 해당 Extractor의 변경으로
격리한다.

### 공통 형식 변환은 Normalizer가 담당한다

Normalizer는 소스 구조를 알지 않고 `ExtractedPolicy`를 공통
`NormalizedProgram`으로 변환한다. 해석할 수 없는 원문은 임의로 추정하지
않고 원문과 누락 상태를 보존한다.

### JSON Schema는 팀 간 계약이다

필드명, 타입, 필수 여부, `null`, 빈 배열과 enum 변경은 데이터 담당자가
단독으로 확정하지 않는다. 백엔드와 프론트엔드 영향을 공동 검토하고 Schema,
Fixture, API와 관련 문서를 함께 갱신한다.

### 운영 Raw 데이터는 Git에 저장하지 않는다

Git에는 라이선스와 개인정보를 확인한 최소 테스트 Fixture만 포함한다. 실제
수집 원문과 런타임 처리 결과는 Docker Volume, DB 또는 운영 저장소에 둔다.

## 아키텍처 변경

계층 책임, 데이터 흐름, 서비스 경계나 실행 단위를 바꾸는 결정은
[아키텍처 결정 기록](decisions/README.md)에 ADR로 남긴다. 아직 합의되지 않은
대안은 현재 아키텍처 문서에 확정 사항처럼 반영하지 않는다.
