# Docker Acceptance 역할별 실행 결과

## 실행자·역할

- 역할: Backend / Frontend / 사용성 리뷰어 / QA
- 실행자:
- 실행 시작·종료 시각과 timezone:
- 결과: pass / conditional / blocked

## 환경 identity

- receipt filename:
- Git SHA (`git rev-parse HEAD`):
- `git status --short` 결과: clean / dirty
- snapshot version:
- dump SHA-256:
- archive SHA-256 대조: pass / fail
- Docker Engine version:
- Docker Compose version:
- OS·Browser·viewport:
- Compose project name:
- service DB Volume name:
- test DB Volume name(해당 시):

## 복원·서비스

- `restore.ps1` 최종 marker:
- Policy / CollectionRun count:
- Alembic revision:
- database / backend / frontend health:
- restart 전후 count:
- secret·Raw payload log 노출: 0 / 발견

## 실행 결과

| ID | 명령·시나리오 | 기대 | 실제 | pass / fail / skip | 증거 |
| --- | --- | --- | --- | --- | --- |
| ENV-01 | Git·archive·snapshot identity | receipt와 일치 |  |  |  |
| ENV-02 | restore·Migration·health | 3273·61·healthy |  |  |  |
| ROLE-01 | 역할 핵심 시나리오 | 역할별 계약 충족 |  |  |  |
| ROLE-02 | 실패·경계 시나리오 | fail-closed·복구 |  |  |  |
| REG-01 | 역할별 회귀 명령 | 0 failed |  |  |  |

skip은 이유와 대체 검증을 적고 pass에 합산하지 않는다. 화면 캡처·로그를 첨부할
때 PIN, token, DB URL, 환경변수 전체와 Raw payload를 제거한다.

## 발견 결함

| 결함 ID | 심각도 | 요약 | 담당 | Release 차단 | 상세 기록 |
| --- | --- | --- | --- | --- | --- |
|  | blocker / high / low |  |  | yes / no |  |

## 미실행·제약

- 미실행 항목과 이유:
- 환경 차이:
- 알려진 제약:

## 인계 확인

- [ ] receipt의 Git SHA·snapshot version·dump hash가 실제 환경과 일치함
- [ ] 개인 secret·PIN·Volume을 다른 참여자와 공유하지 않음
- [ ] Mock과 actual, pass와 skip을 분리함
- [ ] 서비스 DB를 테스트 정리 대상으로 사용하지 않음
- [ ] 정상 종료에서 Volume을 보존함
- [ ] 결함에 재현 조건·기대/실제·증거를 연결함

- 실행자 확인:
- Integration·Deploy 대조:
