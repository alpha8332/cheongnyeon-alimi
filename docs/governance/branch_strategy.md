# 브랜치 전략

## 1. 목적

이 문서는 `cheongnyeon-alimi`의 브랜치 역할, 이름과 병합 흐름을 정의한다.
브랜치는 담당자 이름이 아니라 변경 영역과 하나의 논리적 작업 단위를
기준으로 만든다.

## 2. 기본 흐름

```text
main
└── develop
    └── <type>/<domain>/<task>
```

- 작업 브랜치는 최신 `develop`에서 생성한다.
- 작업 브랜치는 Pull Request를 통해 `develop`으로 병합한다.
- 릴리스 준비가 끝난 `develop`은 Pull Request를 통해 `main`으로 병합한다.
- 버전 태그는 `main`의 릴리스 커밋에 생성한다.

현재는 별도의 장기 release 브랜치를 사용하지 않는다. 안정화 전용 브랜치가
필요해지면 이 문서에서 생성 시점, 허용 변경과 병합 흐름을 먼저 정의한 뒤
도입한다.

## 3. 브랜치별 역할

### `main`

- 최종 배포와 릴리스의 기준이다.
- 항상 실행 가능한 상태를 유지한다.
- 직접 커밋하거나 작업 브랜치를 바로 병합하지 않는다.
- 릴리스 범위와 검증이 완료된 `develop`만 병합한다.
- `v0.1.0`, `v0.5.0`, `v1.0.0`과 같은 버전 태그를 생성한다.

### `develop`

- 다음 릴리스를 준비하는 통합 브랜치다.
- 모든 작업 브랜치의 기본 PR 대상이다.
- 직접 커밋하지 않는다.
- 최소 1명의 승인과 필요한 검증을 통과한 변경만 병합한다.

### 작업 브랜치

- 하나의 Issue 또는 독립적으로 리뷰 가능한 논리적 작업 단위를 다룬다.
- 완료되지 않은 여러 기능을 장기간 누적하지 않는다.
- 병합 후 로컬과 원격 작업 브랜치를 삭제한다.

## 4. 이름 규칙

기본 형식은 다음과 같다.

```text
<type>/<domain>/<task>
```

모든 구간은 영어 소문자와 숫자, 하이픈만 사용한다.

### Type

| Type | 용도 |
| --- | --- |
| `feature` | 새로운 기능 |
| `fix` | 오류 수정 |
| `refactor` | 기능 변화 없는 구조 개선 |
| `test` | 테스트 추가 또는 수정 |
| `docs` | 문서 추가 또는 수정 |
| `chore` | 패키지, 설정과 파일 정리 |
| `perf` | 성능 개선 |
| `ci` | CI 설정 변경 |

### Domain

| Domain | 범위 |
| --- | --- |
| `collector` | 외부 데이터 수집과 공통 정제 파이프라인 |
| `backend` | FastAPI와 서버 비즈니스 로직 |
| `frontend` | React 사용자·관리자 UI |
| `schema` | Raw, 정규화와 API 데이터 계약 |
| `database` | PostgreSQL, ERD, Seed와 Migration |
| `deploy` | Docker, Nginx, 환경 설정과 배포 |
| `governance` | 협업과 오픈소스 운영 정책 |
| `docs` | 여러 영역에 걸친 문서 시스템 |

영역 하나에 명확히 속하는 문서는 해당 domain을 사용한다.

```text
docs/schema/data-contract
docs/deploy/local-setup
docs/governance/collaboration-policy
docs/docs/system-bootstrap
```

CI 브랜치는 type 자체가 목적을 분명히 나타내므로 다음과 같이 두 구간으로
단순화할 수 있다.

```text
ci/backend-test
ci/docker-build
```

### Task

- 브랜치 이름만 보고 작업 목적을 알 수 있게 작성한다.
- 지나치게 넓은 `feature/backend`, `feature/data` 같은 이름은 사용하지 않는다.
- 담당자 이름, Issue 제목 전체와 불필요한 날짜를 넣지 않는다.

## 5. 생성과 Pull Request

```powershell
git switch develop
git pull --ff-only origin develop
git switch -c feature/collector/youthcenter-api
```

작업을 커밋한 후 원격 브랜치를 생성한다.

```powershell
git push -u origin feature/collector/youthcenter-api
```

PR 방향은 다음과 같다.

```text
feature/collector/youthcenter-api → develop
```

리뷰, 테스트와 문서 갱신 기준은
[코드 리뷰 정책](code_review.md)을 따른다.

## 6. 의존 작업

공통 기반이 필요한 경우 기반 작업을 먼저 `develop`에 병합한 뒤, 최신
`develop`에서 후속 브랜치를 각각 생성한다.

후속 브랜치를 미병합 작업 브랜치에서 파생하는 것은 가능한 한 피한다.
불가피했다면 기반 작업이 병합된 후 `origin/develop`을 반영하고 PR에서
의존 관계를 명시한다. 반영 방식은 팀에서 선택한 merge 또는 rebase 방식을
따르며, 공유 브랜치의 공개 이력을 임의로 다시 작성하지 않는다.

## 7. 실제 저장소 우선 원칙

계획 문서는 의도를 설명하지만 현재 적용 상태는 Git 브랜치, 보호 규칙,
워크플로와 저장소 설정으로 확인한다. 문서와 실제 설정이 다르면 임의로
설정을 바꾸지 않고 차이를 알린 뒤, 합의된 작업에서 둘을 함께 수정한다.
