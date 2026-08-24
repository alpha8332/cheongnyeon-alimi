# Docker Acceptance 결함·재검증 기록

## 결함 identity

- 결함 ID:
- 최초 발견 역할·실행자:
- 심각도: blocker / high / low
- 상태: open / fixed-awaiting-independent-retest / verified / deferred
- Git SHA:
- snapshot version:
- dump SHA-256:
- OS·Docker·Compose·Browser:
- Compose project·Volume:

## 재현

- 사전 조건:
- route·API·query:
- 입력 데이터(비밀·개인정보 제외):
- 재현 단계:
  1.
  2.
  3.
- 재현 빈도:

## 기대·실제·영향

- 기대 결과:
- 실제 결과:
- 사용자·데이터·보안 영향:
- 우회 가능 여부:
- Release 차단 근거:

## 증거

- 화면·응답·로그 위치:
- HTTP status·request ID:
- DB count·stable identity 변화:
- secret·Raw payload 제거 확인:

## 수정

- 담당 영역·담당자:
- 원인:
- 수정 Git SHA:
- 변경 파일:
- 자체 회귀 명령과 결과:

## 독립 재검증

- 재검증 역할·실행자:
- 재검증 Git SHA·snapshot version:
- 최초 재현 단계 결과:
- 인접 회귀 결과:
- pass / fail / conditional:
- 종료 또는 후속 근거:

자기 수정만으로 blocker·high 결함을 종료하지 않는다. 최초와 다른 Git SHA나
snapshot으로 재검증했다면 동일 결함의 종료 근거로 합치지 않는다.
