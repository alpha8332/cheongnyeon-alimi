# 청년정책알리미 문서

이 문서는 현재 공개 저장소의 문서 탐색 시작점이다. 과거 주차별 계획과 구현
일지는 제출본에서 제외하고, 현재 동작·계약·운영 절차와 재사용 가능한 문제 해결
기록만 유지한다.

## 처음 읽을 문서

| 독자 | 시작 문서 |
| --- | --- |
| 일반 사용자·심사자 | [README](../README.md), [제품 기능 총정리](product/system_features.md) |
| 기능을 자세히 확인할 사람 | [제품 기능 문서 안내](product/README.md) |
| 설치·실행 담당자 | [Windows Docker 최초 실행](operations/docker_first_run.md) |
| 운영 관리자 | [운영 문서](operations/README.md) |
| 개발 기여자 | [아키텍처 개요](architecture/overview.md), [개발 문서](development/README.md) |
| 대회 제출 검토자 | [제출 문서](contest/README.md) |

## 제품

- [기능 총정리](product/system_features.md): 사용자·관리자·데이터 기능 요약
- [기능별 상세 설명](product/README.md): 검색, 상세, 추천, 개인 기능, 관리자와
  공개 dataset의 작동 원리

## 아키텍처

- [시스템 아키텍처 개요](architecture/overview.md)
- [현재 컨테이너 구조](architecture/container_structure.md)
- [데이터·요청 흐름](architecture/system_flow.md)
- [정책 DB 매핑](architecture/policy_database_mapping.md)
- [CollectionRun DB 계약](architecture/collection_run_database.md)
- [아키텍처 결정 기록](architecture/decisions/README.md)

## API

- [API 문서 안내](api/README.md)
- [정책 검색·상세 API](api/policies.md)
- [맞춤 추천 API](api/recommendation.md)
- [관리자 인증](api/admin_access.md)
- [관리자 수집기 상태](api/admin_collectors.md)
- [CollectionRun](api/admin_collection_runs.md)
- [관리자 정책 조회](api/admin_policies.md)
- [관리자 로그](api/admin_logs.md)

## 데이터

- [데이터 문서 안내](data/README.md)
- [공개 정책 dataset](data/public_policy_dataset.md)
- [환경 간 공개 결과 동등성](data/public_dataset_parity.md)
- [데이터 소스](data/data_sources.md)
- [정규화 규칙](data/normalization_rules.md)
- [정책 생명주기](data/policy_lifecycle.md)
- [행정구역 기준](data/administrative_regions.md)

## 운영과 문제 해결

- [운영 문서 안내](operations/README.md)
- [Collector 실행](operations/collector.md)
- [Production 배포와 dataset 발행](operations/production_delivery.md)
- [실제 문제 해결 기록](troubleshooting/README.md)

## 기여와 프로젝트 운영

- [개발 환경·검증 안내](development/README.md)
- [거버넌스 문서](governance/README.md)
- [브랜치 전략](governance/branch_strategy.md)
- [커밋 규칙](governance/commit_convention.md)
- [코드 리뷰](governance/code_review.md)
- [문서화 정책](governance/documentation_policy.md)
- [역할과 책임](governance/role_assignment.md)

## 대회 제출

- [제출 자료 안내](contest/README.md)
- [최종 제출 체크리스트](contest/open_source_submission_checklist.md)

## 문서의 권위

문서와 실제 동작이 충돌하면 실행 코드, Migration, Compose 구성과 자동화된
계약 테스트를 먼저 확인한다. 확인된 차이는 같은 변경에서 기준 문서에 반영한다.
과거 장애 수치와 실행 환경은 `docs/troubleshooting/`의 역사적 재현 근거이며,
현재 공개 정책 수와 설치 기준은 `docs/data/public_policy_dataset.md`와 함께
배포되는 latest manifest를 따른다.
