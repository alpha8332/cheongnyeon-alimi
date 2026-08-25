# 관리자 데이터 품질과 감사

## 기능 목적

수집·정규화 결과가 사용자에게 공개되기 전에 품질 문제와 실행 실패를 추적하고,
DB 정책과 서버 로그를 비밀정보 없이 읽게 한다. 현재 관리자 데이터 화면은
관찰과 감사가 목적이며 정책 내용을 직접 편집하는 CMS가 아니다.

## 사용하는 화면

| 화면 | 주소 | 역할 |
| --- | --- | --- |
| 대시보드 | `/admin` | 최신 실행과 주요 품질 지표 요약 |
| 데이터 품질 | `/admin/quality` | 최근 CollectionRun별 품질 count 비교 |
| 정책 데이터 | `/admin/policies` | PostgreSQL 정책 목록·상세 읽기 전용 조회 |
| 구조화 로그 | `/admin/logs` | 허용된 로그 파일·이벤트 조회와 archive 정리 |

모든 API는 공통 관리자 인증을 다시 검사한다.

## 데이터 품질의 원리

수집 파이프라인은 한 정책을 단순 성공·실패로만 나누지 않는다. 추출과 정규화,
Schema 검증, 중복 판정과 생명주기 결과를 서로 다른 count로 기록한다.

| 지표 | 의미 |
| --- | --- |
| raw | Source에서 보존한 원문 문서 수 |
| extracted | source extractor가 정책 후보로 변환한 수 |
| accepted | DB 반영 후보로 승인된 수 |
| partial | 일부 필드가 미확정이지만 공개 계약상 사용할 수 있는 수 |
| invalid | Schema·품질 규칙을 통과하지 못한 수 |
| duplicate | 같은 identity 또는 승인된 중복 근거로 분리한 수 |
| rejected | Source·지역·청년 대상 등 admission Gate에서 제외한 수 |
| inserted·updated·unchanged | DB write 결과 |
| skipped·failed | 의도적 미처리와 실행 실패 수 |

이 count는 CollectionRun의 같은 실행 범위에서 해석해야 한다. 서로 다른 source와
요청 수의 실행을 단순 합계만으로 비교하지 않는다.

## 데이터 품질 화면

`/admin/quality`는 최근 실행을 기준으로 failed, invalid, duplicate 등 운영자가
확인해야 하는 지표를 비교한다. 값이 있는 품질 card는 해당 CollectionRun
상세로 이동해 전체 count와 오류 유형을 확인하게 한다.

품질 화면의 `partial`과 `invalid`는 다르다.

- `partial`: 일부 조건이 미확정이지만 계약상 보수적으로 사용할 수 있음
- `invalid`: 공개 Schema 또는 안전 규칙을 통과하지 못해 사용자 API에서 제외

품질 집계는 원인을 찾는 시작점이며 Raw 원문이나 개인 정보를 그대로 화면에
복사하지 않는다.

## 정책 데이터 조회 원리

`/admin/policies`는 일반 공개 API보다 넓은 로컬 DB 범위를 읽기 전용으로 조회한다.
따라서 다음 정책도 감사 목적으로 볼 수 있다.

- 활성 공개 dataset에 포함된 정책
- membership 밖 로컬 수집 정책
- inactive 정책
- 종료일 경과 정책
- valid·partial·invalid 품질 상태

일반 사용자 API가 이 전체 범위를 반환한다는 뜻은 아니다. 공개 여부는 별도의
활성 membership과 생명주기 조건으로 결정한다.

## 정책 목록과 상세

목록은 허용된 column만 응답한다.

- DB 정책 ID, source ID·name과 external ID
- 제목과 기관
- 분야와 지역
- 데이터 품질 상태
- 수집·생성·갱신 시각
- 생명주기 검증·비활성 시각

정렬 필드는 allowlist로 제한하고 page·size 경계를 검증한다. 행 상세도 관리자
DTO가 허용한 정규화 필드만 반환한다.

현재 화면은 정책을 수정·삭제·공개 승격하지 않는다. 화면상 버튼이나 query를
조작해도 write endpoint가 없으므로 읽기 전용 경계를 유지한다.

## 일반 정책 수와 다른 이유

관리자 DB 전체 수와 사용자 공개 정책 수는 다음 이유로 다를 수 있다.

- 로컬 개발·수동 수집 정책 보존
- 공개 재배포 허용 밖 source
- 개인정보·비밀 pattern 안전 경계 제외
- inactive·종료일 경과 정책
- 아직 승격하지 않은 새 dataset 후보

관리자 화면의 DB 수가 크다는 사실만으로 일반 사용자에게 더 많은 정책을
노출해서는 안 된다.

## 구조화 로그 원리

Backend는 UTF-8 JSON Lines 구조화 이벤트를 파일에 기록한다. 관리자 API는 파일
전체를 내려주지 않고 안전한 event 필드만 parsing해 반환한다.

허용 정보 예:

- timestamp와 level
- component와 event 이름
- request ID
- CollectionRun ID와 source ID
- 처리 시간
- 오류 유형

비허용 정보 예:

- request·response body
- stack trace와 traceback 전체
- SQL과 parameter
- PIN, token, API key와 password
- Raw 정책 본문
- 서버 파일 절대 경로

## 로그 파일 경계

파일 목록은 basename 기반의 안전한 file ID, 활성 여부, 크기와 수정 시각만
제공한다. 사용자가 임의 경로를 입력해 다른 서버 파일을 읽지 못하도록 허용된
로그 root와 filename 경계를 검증한다.

활성 로그는 실행 중 삭제할 수 없다. archive만 명시적 확인 뒤 정리할 수 있으며
삭제 작업 자체를 별도 감사 event로 기록한다.

현재 로그를 정리하는 작업은 다음 순서를 따른다.

1. 활성 파일을 안전하게 회전
2. 새 활성 로그 생성 확인
3. 방금 만든 archive를 승인된 경계에서 삭제
4. 정리 감사 event 기록

## 오류 추적 흐름

권장 조사 순서는 다음과 같다.

```text
대시보드 경고
→ 데이터 품질 count
→ CollectionRun 상세와 error_type
→ 같은 run_id·source_id 구조화 로그
→ 필요 시 Git 제외 Runtime Raw 조사
```

화면에서 Raw를 직접 보여주지 않으므로 상세 원문 조사가 필요하면 서버 권한이
있는 운영자가 Git 제외 Runtime 영역에서 별도 보안 절차로 수행한다.

## 보안 원리

- 모든 화면과 API에 관리자 인증 적용
- 목록·상세 DTO의 field allowlist
- 파일 root와 basename 검증
- archive 삭제 typed confirmation과 감사 기록
- 비밀 key 이름과 민감 payload의 응답 제외
- 오류 시 예외 message 전체 대신 안전한 오류 유형 사용

## 현재 제한사항

- 관리자 정책 화면은 편집·삭제 CMS가 아니다.
- 데이터 품질 화면은 Raw record 단위 수정 기능을 제공하지 않는다.
- 구조화 로그 API는 server log viewer이며 중앙 observability 서비스가 아니다.
- Volume 또는 container가 제거되면 별도 외부 보관이 없는 로그는 사라질 수 있다.
- count만으로 정책의 실제 내용 정확성을 완전히 증명할 수 없다.

## 관련 계약

- [관리자 정책 API](../../api/admin_policies.md)
- [관리자 로그 API](../../api/admin_logs.md)
- [CollectionRun 관리자 API](../../api/admin_collection_runs.md)
- [정책 DB 매핑](../../architecture/policy_database_mapping.md)
- [관리자 데이터·로그 개발 기록](../../development/development_notes/integration/admin_data_log_console.md)
