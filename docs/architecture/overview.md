# 시스템 아키텍처 개요

## 현재 상태

- 대상 Release 기준: `v1.0.2`과 현재 공개 저장소
- 구현 상태: Docker 기반 사용자·관리자 Web UI와 중앙 데이터 파이프라인 운영
- 사용자 실행 기준: Windows 10/11, Docker Desktop, `run_docker.bat`

청년정책알리미는 공식 API와 공개 웹 Source의 정책을 중앙에서 수집·정규화하고,
검증된 공개 dataset을 사용자 PC에 설치해 검색·추천·관리자 기능을 제공한다.
사용자 PC는 원본 Source API key 없이 실행하며, 사용자 API는 활성 공개 dataset
membership에 포함된 정책만 반환한다.

## 전체 구조

```text
공식 API·공개 웹 Source
        ↓ 중앙 수집
Collector → Extractor → Normalizer → Validator
        ↓
격리 PostgreSQL 검증 → versioned 공개 dataset → GitHub Release
                                             ↓ HTTPS + SHA-256
사용자 PC: PostgreSQL ← dataset bootstrap
              ↑
React UI ← FastAPI ← 검색·추천 Repository
              ↑
관리자 UI ← 인증·수집기·CollectionRun·품질·로그 API
              ↓ enqueue
       Redis → Celery worker ← Celery beat
```

## 주요 구성요소

### Frontend

`frontend/`의 React·TypeScript 애플리케이션이 일반 사용자와 관리자 화면을
제공한다. 사용자 프로필, 즐겨찾기와 폴더는 서버 계정 대신 브라우저
`localStorage`에 저장한다. 관리자 access token은 브라우저 메모리에만 둔다.

### Backend

`backend/app/`의 FastAPI 애플리케이션이 정책 목록·검색·상세·추천과 관리자
API를 제공한다. Route는 HTTP 경계, Service는 업무 규칙, Repository는
PostgreSQL 조회와 영속화를 담당한다.

### PostgreSQL

정규화 정책, 공개 dataset 설치·membership, 행정구역, CollectionRun, 관리자
인증 상태와 감사 이벤트를 저장한다. 정책 전체 row 수와 사용자에게 공개되는
정책 수는 다를 수 있으며, 공개 projection은 활성 membership으로 결정한다.

### 데이터 파이프라인

`collectors/`가 외부 요청, Raw envelope, source별 추출, 공통 정규화와 검증을
담당한다. 실제 Raw와 rejected 결과는 Git에 넣지 않고 Runtime Volume 또는
중앙 실행 환경에 둔다.

### 비동기 수집

Redis가 collection queue broker 역할을 하고 Celery worker가 실제 수집·import를
수행한다. Celery beat는 선택적으로 정기 실행을 enqueue한다. Policy와
CollectionRun의 권위 상태는 Redis가 아니라 PostgreSQL에 남는다.

### 공개 dataset 배포

중앙 Workflow가 허용된 Source만 완전 수집하고 격리 DB에서 row·Schema·hash·
검색 projection을 검증한다. 성공한 artifact는 불변 Release로 발행하고
`dataset-latest` pointer를 마지막에 승격한다.

## 고정된 책임 경계

- Collector는 원문 획득과 provenance를, Extractor는 source 의미 해석을 담당한다.
- Normalizer는 날짜·지역·연령·분야를 공통 형식으로 변환한다.
- Validator는 `valid`, `partial`, `invalid`를 구분하고 invalid를 공개 후보에서
  제외한다.
- 수동 수집 결과는 DB에 보존되지만 공개 dataset 승격 전에는 사용자 검색에
  포함되지 않는다.
- 확인되지 않은 조건은 전국·연령 무관·자격 충족으로 추정하지 않는다.
- API key, PIN, token, DB 비밀번호와 Raw payload는 Frontend bundle·로그·
  공개 문서·Release asset에 포함하지 않는다.

## 관련 문서

- [현재 컨테이너 구조](container_structure.md)
- [시스템 흐름](system_flow.md)
- [공개 dataset 계약](../data/public_policy_dataset.md)
- [API 문서](../api/README.md)
- [운영 문서](../operations/README.md)
