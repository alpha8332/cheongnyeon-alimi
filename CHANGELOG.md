# 변경 이력

이 파일은 `cheongnyeon-alimi`의 사용자와 팀에 의미 있는 변경 사항을
기록한다.

형식은 [Keep a Changelog](https://keepachangelog.com/ko/1.1.0/)를 따르며,
프로젝트는 [Semantic Versioning](https://semver.org/lang/ko/)을 사용한다.

## [Unreleased]

### Added

- 개발 계획·기록과 문제 해결 문서를 Data, Backend, Frontend, Integration
  담당 영역으로 분류하는 규칙
- 공통 데이터 기준과 주차별 실행 범위를 분리한 Data Pipeline Forest 계획
- 문서 탐색, 갱신 기준과 작업 전후 체크리스트를 제공하는 문서 시스템 기반
- 계획, 개발 기록, 변경 이력과 문제 해결 기록을 구분하는 문서화 정책
- 아키텍처, API, 데이터, 거버넌스, 개발, 계획, 문제 해결, 운영과 대회
  문서의 책임을 구분하는 기본 디렉터리 구조
- 루트 `README.md`에서 프로젝트 문서 진입점으로 연결하는 안내
- 브랜치, 커밋, 코드 리뷰와 역할 분담을 하나의 협업 흐름으로 연결한
  거버넌스 정책
- 외부 정책 소스부터 React UI까지의 계층, 데이터 흐름과 책임 경계를
  정의한 시스템 아키텍처 기준선
- 초기 3개 컨테이너 구성과 향후 실행 단위 변경을 관리하는 ADR 규칙
- 온통청년 API와 대표 HTTPS 웹 소스의 등록·검증 기준
- Raw, Extracted와 Normalized 데이터 계약, 정규화 및 안전한 수집 기준선
- 개발 계획과 실제 구현 기록을 Forest별 문서로 대응시키는
  `develop_plan/` 및 `development_notes/` 구조
- 문서 링크, 필수 파일, 비밀값 패턴과 Forest 문서 구조를 검사하는 문서
  품질 검증기 및 단위 테스트
