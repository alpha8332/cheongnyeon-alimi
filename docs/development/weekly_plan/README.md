# 주차별 상세 실행 계획

이 디렉터리는 Release·Forest 로드맵을 실제 주차의 작업 순서, 병렬 실행,
역할별 책임과 검증 Gate로 구체화한다.

## 문서 역할

- `develop_plan/`은 Forest별 목표, Slice와 완료 기준을 관리한다.
- 이 디렉터리는 한 주에 여러 Forest를 어떤 순서와 역할로 실행할지 조정한다.
- `development_notes/`는 실제 구현 내용과 실행한 검증 결과를 기록한다.
- 주차 문서는 구현 결과나 개발 기록을 대신하지 않는다.

주차는 고정된 달력 날짜가 아니라 실행 순서를 뜻한다. 선행 Gate를 충족하지
못하면 다음 단계나 릴리스로 넘어가지 않으며, 실행하지 않은 항목을 일정상
완료로 처리하지 않는다.

## 현재 상세 계획

| 주차 | 목표 | 문서 상태 | 상세 계획 |
| --- | --- | --- | --- |
| 3주차 | 실데이터 정책 검색과 `v0.1.0` | in-progress (`G4 pass`, 병합 대기) | [3주차 상세 계획](week_03_release_1.md) |

## 현재 역할별 실행 계획

| 주차 | 역할 | 문서 상태 | 실행 계획 |
| --- | --- | --- | --- |
| 3주차 | Data·Team Leader | completed | [Data·Team Leader 계획](week_03_data_team_leader.md) |

## 현재 인수인계

| 주차 | Gate | 상태 | 인수인계 |
| --- | --- | --- | --- |
| 3주차 | DT2·Gate G1 | completed | [Backend 06·Frontend 04 검색 계약 인수인계](week_03_search_contract_handoff.md) |

1·2주차는 완료된 Forest 계획과 개발 기록이 권위 자료이므로 별도 주차 파일을
소급 생성하지 않았다. 4~6주차는 해당 주차의 선행 Release 결과와 상세 Forest
범위가 확인된 뒤 생성한다.

## 문서 상태

- `draft`: 역할·의존성 또는 완료 기준 검토 전
- `approved`: 실행 순서와 Gate가 합의됨
- `in-progress`: 해당 주차의 하나 이상의 작업이 시작됨
- `completed`: 연결된 Forest와 Release Gate가 실제 검증을 통과함
- `superseded`: 일정 또는 Release 계획 변경으로 다른 주차 문서가 대체함

주차 문서를 `completed`로 바꾸는 것만으로 Forest나 Release가 완료되지 않는다.
대응하는 개발 기록, 테스트 결과와 Release 완료 조건이 함께 충족돼야 한다.

## 상세 계획 필수 항목

```markdown
# N주차 - 목표

## 계획 정보
## 목표
## 시작 조건
## 현재 기준선
## 범위
## 범위 밖
## 실행 원칙
## 선행 관계와 Critical Path
## 단계별 Gate
## 역할별 작업
## 산출물
## 테스트와 검증
## 위험과 결정 필요 사항
## 인계사항 발생 조건
## 완료 체크리스트
## 관련 문서
```

## 운영 규칙

1. 다음 주차 파일을 미리 빈 문서로 만들지 않는다.
2. 상세 Forest 계획이 필요한 작업은 주차 문서만으로 구현을 시작하지 않는다.
3. 주차 문서의 작업 ID는 일정 추적용이며 Forest Slice를 대체하지 않는다.
4. 병렬 작업과 반드시 기다려야 하는 선행 작업을 구분한다.
5. API·Schema·DB·Fixture·Seed 계약을 바꾸면 담당 기준 문서와 소비자 검토를
   같은 작업에서 갱신한다.
6. 실제 영역 간 차단 문제가 생겼을 때만 `docs/index.md` 인계 보드에
   등록한다. 미래 계획 자체는 인계사항이 아니다.
7. 실행 결과와 검증 수치는 대응하는 `development_notes/`에 기록한다.
8. 의미 있는 완료 결과만 `CHANGELOG.md`에 기록한다.

## 관련 문서

- [주차별 실행 계획 요약](../develop_plan/weekly_delivery_plan.md)
- [Release와 Milestone 계획](../develop_plan/release_roadmap.md)
- [전체 Forest 로드맵](../develop_plan/forest_roadmap.md)
- [역할과 책임](../../governance/role_assignment.md)
- [개발 기록 안내](../development_notes/README.md)

