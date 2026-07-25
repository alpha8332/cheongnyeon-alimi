# 개발 계획 안내

이 디렉터리는 아직 완료하지 않은 작업의 범위, 의존성, 수행 순서와 완료
기준을 Forest 단위로 관리한다. 실제 구현과 검증 결과는
[`development_notes/`](../development_notes/README.md)에 기록한다.

## 현재 개발 계획

| 번호 | Forest | 계획 | 상태 |
| --- | --- | --- | --- |
| Integration 01 | Docs System | [개발 계획](integration/01_docs_system.md) | completed |
| Data 01 | Data Pipeline | [개발 계획](data/01_data_pipeline.md) | draft |

새 Forest 계획을 추가하면 이 표와 [`docs/index.md`](../../index.md)를 함께
갱신한다.

## Forest 기준

- 하나의 목표와 결과 흐름을 공유하는 작업 집합을 Forest로 관리한다.
- Forest마다 개발 계획 문서 하나를 둔다. 실제 구현을 시작하면 같은 담당
  영역에 개발 기록 문서 하나를 만든다.
- Forest 안의 Slice는 계획 문서 내부에서 순서, 의존성과 완료 기준을
  구분한다.
- Slice마다 별도 계획 파일을 만들지 않는다.
- 독립적인 목표, 산출물과 완료 기준이 생길 때 새 Forest 계획을 만든다.

담당 영역이 명확한 Forest는 다음 경로를 사용한다.

| 영역 | 경로 | 사용 기준 |
| --- | --- | --- |
| Data | `data/` | 수집, 추출, 정규화, 검증과 Fixture·Seed |
| Backend | `backend/` | API, 서비스, DB 연동과 Backend 기능 |
| Frontend | `frontend/` | 화면, 상태 관리와 사용자 상호작용 |
| Integration | `integration/` | 둘 이상의 영역 또는 팀 공통 기반 |

실제 계획 문서가 생길 때만 해당 디렉터리를 생성한다. 담당 영역이 불명확하면
임의로 분류하지 않고 범위를 먼저 합의한다.

예:

```text
data/01_data_pipeline.md
backend/01_favorites.md
frontend/01_calendar.md
integration/01_policy_delivery.md
```

현재 데이터·API 계약 자체는 Forest 계획에만 적지 않고 각각 `docs/data/`와
`docs/api/`의 기준 문서에도 반영한다.

## 상태

| 상태 | 의미 |
| --- | --- |
| `draft` | 검토 전 초안 |
| `approved` | 범위와 완료 기준이 합의됨 |
| `in-progress` | 하나 이상의 Slice를 구현 중 |
| `completed` | Forest 전체 완료 기준과 검증을 충족함 |
| `superseded` | 다른 계획으로 대체됨 |

Forest가 `completed`가 되면 관련 개발 기록과 커밋 또는 PR을 연결한다.
`superseded`가 되면 대체 계획과 변경 이유를 기록한다.
`draft`와 `approved` 계획은 아직 구현 결과가 없으므로 개발 기록을 요구하지
않는다. `in-progress`로 변경할 때 대응하는 개발 기록을 생성한다.

## 계획 문서 필수 항목

```markdown
# Forest 이름

## 계획 정보
## 목적
## 범위
## 범위 밖
## 선행 조건
## 공통 설계 원칙
## Slice 계획
## 검증 계획
## Forest 완료 기준
## 위험과 미확정 사항
## 관련 문서
```

각 Slice에는 목적, 산출물, 선행 조건과 완료 기준을 포함한다. Issue, 브랜치나
구현 파일이 확정되지 않았다면 `미정`으로 표시한다.

## 운영 규칙

1. Forest 시작 전에 목적, 범위, 범위 밖과 전체 완료 기준을 검토한다.
2. Slice를 시작할 때 선행 조건과 미확정 사항을 확인한다.
3. 구현 중 설계가 바뀌면 계획의 결정과 이유를 갱신한다.
4. 완료한 Slice의 결과와 검증은 Forest 개발 기록에 상세히 남긴다.
5. 계획과 개발 기록에 같은 내용을 장문으로 중복하지 않고 서로 연결한다.
6. 완료된 계획을 삭제하지 않고 추적 정보를 유지한다.
7. 비밀키, 개인정보와 비공개 원문을 기록하지 않는다.
8. 실제 내용이 없는 계획 파일과 빈 디렉터리를 만들지 않는다.
