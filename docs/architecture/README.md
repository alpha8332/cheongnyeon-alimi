# 아키텍처 문서

이 디렉터리는 현재 구현된 시스템 경계와 장기적으로 유지해야 하는 설계
결정을 설명한다.

## 기준 문서

- [시스템 아키텍처 개요](overview.md): 구성요소와 책임 경계
- [현재 컨테이너 구조](container_structure.md): Acceptance·Production Compose,
  네트워크, Volume과 시작 순서
- [시스템 흐름](system_flow.md): 중앙 수집부터 공개 dataset, 사용자 검색과
  관리자 수동 수집까지의 데이터 흐름
- [정책 DB 매핑](policy_database_mapping.md): 논리 Schema와 PostgreSQL 매핑
- [CollectionRun DB 계약](collection_run_database.md): 수집 실행 상태와 집계
- [아키텍처 결정 기록](decisions/README.md): 채택된 주요 설계 판단

## 문서 경계

- API 요청·응답은 `docs/api/`를 따른다.
- 정규화·공개 범위·생명주기는 `docs/data/`를 따른다.
- 실행·복구 절차는 `docs/operations/`를 따른다.
- 기능의 사용자 관점 설명은 `docs/product/`를 따른다.

실제 서비스 구성은 `compose.yaml`, `compose.production.yaml`, Dockerfile과
Migration이 최종 실행 기준이다. 구조를 바꾸면 이 디렉터리와 관련 계약
테스트를 같은 변경에서 갱신한다.
