# API 문서

이 디렉터리는 Frontend와 운영 도구가 사용하는 현재 HTTP 계약을 관리한다.

## 문서

- [정책 목록·상세·검색](policies.md)
- [맞춤 추천](recommendation.md)
- [관리자 인증·PIN 변경](admin_access.md)
- [관리자 수집기 상태](admin_collectors.md)
- [CollectionRun 목록·상세·수동 실행](admin_collection_runs.md)
- [관리자 정책 데이터 조회](admin_policies.md)
- [관리자 구조화 로그](admin_logs.md)

각 문서는 endpoint, 인증, 요청·응답 Schema, 페이지네이션·정렬과 오류 상태를
실제 FastAPI 구현에 맞춰 설명한다. Route가 바뀌면 OpenAPI, Pydantic Schema,
Frontend API client와 계약 테스트를 같은 변경에서 갱신한다.

수집 원문·정규화 규칙은 `docs/data/`, 내부 계층과 컨테이너 책임은
`docs/architecture/`, 운영 절차는 `docs/operations/`를 따른다.
