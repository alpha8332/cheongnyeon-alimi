# Docs System Forest 개발 계획

## 계획 정보

- 번호: 01
- 담당 영역: 데이터 담당 선행 기반
- 상태: in-progress
- 관련 브랜치:
  - `docs/governance/documentation-system`
  - `docs/governance/collaboration-policy`
- 개발 기록: [`docs_system.md`](../development_notes/docs_system.md)
- 참고 계획:
  `opensource_plan/개발 계획/1. docs 구조 설계.docx`

## 목적

데이터 파이프라인 개발을 시작하기 전에 프로젝트의 문서 구조, 협업 규칙,
아키텍처·데이터 기준선, 개발 계획·기록과 검증 체계를 구축한다. 코드 변경과
함께 문서가 정확하게 갱신되고, 계획과 실제 구현 결과가 섞이지 않도록 한다.

## 범위

- 문서 역할과 갱신 규칙
- docs 디렉터리 구조와 탐색 진입점
- 브랜치, 커밋, 코드 리뷰와 역할 정책
- 시스템 아키텍처와 컨테이너 기준선
- 데이터 소스, Schema, 정규화와 수집 기준선
- Forest 기반 개발 계획과 개발 기록
- 문서 품질 자동 검증

## 범위 밖

- 실제 Collector, Backend와 Frontend 구현
- 실행 가능한 JSON Schema와 Fixture·Seed
- Docker Compose와 서비스 health check
- GitHub 브랜치 보호와 CODEOWNERS 설정
- 대회 결과보고서와 최종 제출 자료 작성

## 선행 조건

- 저장소명은 `cheongnyeon-alimi`를 사용한다.
- `opensource_plan/`은 참고 전용이며 개발 작업에서 수정하지 않는다.
- 모든 문서 변경은 작업 브랜치에서 검토 후 `develop`으로 병합한다.
- 구현되지 않은 시스템은 완료된 것처럼 문서화하지 않는다.

## 공통 설계 원칙

- 빈 문서와 빈 디렉터리를 미리 만들지 않는다.
- 계획과 실제 개발 기록은 Forest당 각각 하나의 문서로 관리한다.
- Forest 내부의 Slice는 문서 내부 섹션과 진행 표로 구분한다.
- 기준 문서는 현재 계약, develop plan은 미래 작업, development notes는 실제
  구현 결과를 설명한다.
- 의미 있는 변경만 `CHANGELOG.md`에 기록한다.
- 실제 발생하고 해결된 문제만 troubleshooting에 기록한다.
- 실행한 검증만 결과로 기록한다.
- 비밀키, 개인정보와 재배포할 수 없는 원문을 저장하지 않는다.

## Slice 계획

### D0 - 문서 시스템 규칙 확정

- 상태: completed
- 목적: 변경 유형별 문서 갱신 기준과 문서 역할 확정
- 주요 산출물: `docs/index.md`, 문서화 정책, `CHANGELOG.md`
- 완료 기준:
  - 계획, 개발 기록, 변경 이력과 troubleshooting 역할 구분
  - AI Agent 작업 전후 체크리스트 제공

### D1 - docs 디렉터리 골격 및 진입점

- 상태: completed
- 목적: GitHub에서 탐색 가능한 문서 영역 구축
- 주요 산출물: 영역별 안내 문서와 루트 `README.md` 진입 링크
- 완료 기준:
  - 영역별 책임이 중복되지 않음
  - 빈 세부 문서를 대량 생성하지 않음

### D2 - 협업·거버넌스 문서 이관

- 상태: completed
- 목적: 여러 Word 계획의 협업 규칙을 하나의 정책 체계로 정규화
- 주요 산출물: 브랜치, 커밋, 코드 리뷰, 문서화와 역할 정책
- 완료 기준:
  - 브랜치 이름은 `<type>/<domain>/<task>`
  - 작업 브랜치 PR 대상은 `develop`
  - Conventional Commits와 최소 리뷰 기준 연결

### D3 - 시스템 아키텍처 기준선

- 상태: completed
- 목적: 데이터 개발 전 공통 용어와 계층 책임 확정
- 주요 산출물: 시스템 개요, 흐름, 컨테이너 구조와 ADR 안내
- 완료 기준:
  - Collector, Extractor, Normalizer와 Validator 경계 구분
  - JSON Schema를 팀 간 계약으로 정의
  - 목표 구조와 현재 구현 상태 구분

### D4 - 데이터 문서 기준선

- 상태: completed
- 목적: 1주차 데이터 개발이 참조할 선행 원칙 마련
- 주요 산출물: 데이터 소스, Schema, 정규화와 수집 정책
- 완료 기준:
  - Raw·Extracted·Normalized 단계 구분
  - null과 빈 배열 규칙
  - 원문·출처·수집 시각·Hash 보존 정책
  - Schema와 설명 문서 동기화 규칙
  - 확정값과 미확정 사항 구분

### D5 - Forest 기반 develop plan 구축

- 상태: in-progress
- 목적: Docs Forest와 첫 Data Forest의 계획을 저장소 문서로 관리
- 현재 결과:
  - Forest 기반 `develop_plan/`과 `development_notes/` 구조
  - 이 Docs System Forest 계획과 개발 기록의 상호 연결
- 남은 산출물:
  - 첫 Data Forest 개발 계획
- 완료 기준:
  - Forest마다 계획 문서와 개발 기록 문서가 대응함
  - Slice 의존성, 테스트와 완료 기준이 계획 안에서 확인 가능

### D6 - 문서 품질 검증 장치

- 상태: pending
- 목적: 문서 시스템의 핵심 규칙을 반복 가능하게 검사
- 검증 후보:
  - Markdown 링크
  - 필수 문서 존재 여부
  - 저장소명 오기
  - 비밀정보 패턴
  - 계획·기록 상태와 필수 항목
- 완료 기준:
  - 로컬 명령으로 문서 검증 가능
  - CI 도입 가능 구조
  - 임시 산출물 없이 반복 실행 가능

## 검증 계획

- 모든 Markdown 상대 링크 확인
- docs 필수 영역과 Forest 계획·기록 대응 확인
- 문서 내 프로젝트명 통일 확인
- 확정·미확정·미구현 상태 구분 확인
- 비밀정보와 실제 운영 Raw 포함 여부 확인
- 빈 파일·빈 디렉터리와 임시 파일 확인
- `git diff --check`
- `opensource_plan/` 사용자 변경 보존 확인

## Forest 완료 기준

- D0~D6이 모두 completed
- `docs/index.md`에서 모든 기준 문서와 Forest 계획·기록 탐색 가능
- 코드 변경 유형별 문서 갱신 기준이 명확함
- 계획과 실제 개발 결과가 Forest 단위로 분리됨
- 아키텍처와 데이터 기준선이 첫 Data Forest 구현에 사용 가능
- 문서 품질 검증을 로컬에서 반복 실행 가능
- 실행하지 않은 테스트나 미구현 기능을 완료로 기록하지 않음

## 위험과 미확정 사항

- `application_status`의 `always`와 `open` 의미가 충돌하며 Data Schema 구현
  전에 공동 결정이 필요하다.
- 온통청년 API의 공식 endpoint, 응답 형식, 호출 제한과 이용 조건은 실제
  Collector 구현 전에 확인해야 한다.
- 대표 HTTPS 웹사이트와 실제 source ID가 아직 확정되지 않았다.
- GitHub 브랜치 보호와 문서 검증 CI는 아직 구현되지 않았다.

## 관련 문서

- [`docs/index.md`](../../index.md)
- [문서화 정책](../../governance/documentation_policy.md)
- [Docs System Forest 개발 기록](../development_notes/docs_system.md)
- [시스템 아키텍처 개요](../../architecture/overview.md)
- [데이터 문서 안내](../../data/README.md)
