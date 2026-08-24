# 공개 dataset 사용자 결과 동등성 계약

## 목적

작성자 DB에만 존재하는 정책 때문에 Git clone·Download ZIP 사용자의 검색 결과가
달라지는 상태를 탐지한다. 공개 Release 완료 조건은 단순 Source 수집 성공뿐 아니라
사용자에게 노출될 수 있는 모든 정책이 공개 dataset에 포함 가능한 상태인지 확인하는
것이다.

## 판정 범위

`scripts/audit_public_dataset_parity.py`는 지정일 기준 다음 정책을 사용자 노출
후보로 계산한다.

- `data_quality_status`가 `valid` 또는 `partial`
- `inactive_at`이 없음
- `application_end`가 없거나 지정일 이후

공개 Source 계약에 포함되고 연락처·이메일·개인 휴대전화·비밀 query key 안전
경계를 통과한 레코드만 `publishable`이다. 그 밖의 레코드는 다음처럼 분리한다.

| 분류 | 의미 |
| --- | --- |
| `excluded_source` | 공개 재배포 allowlist 밖의 Source |
| `content_safety_excluded` | 허용 Source지만 공개 금지 내용 포함 |
| `exact_title_review` | 허용 Source와 정규화 제목이 같으나 자동 중복 확정 금지 |
| `unique_title_gap` | 허용 Source에서 같은 제목도 찾지 못한 사용자 결과 차이 후보 |

`parity_gap_row_count`가 0일 때만 `pass`다. 제목 일치는 검토 후보일 뿐 자동
중복 삭제 근거로 사용하지 않는다. Raw HTML·API 응답과 정책 본문은 보고서에
포함하지 않고 Source별 집계만 기록한다.

## 설치 후 공개 경계

Release artifact 검증과 후보 parity는 발행 전 gate다. 설치 시에는 별도로
manifest·artifact SHA-256과 모든 row·identity·예상 건수를 다시 확인한 뒤,
`public_dataset_installations`와 `public_dataset_memberships`를 정책 upsert와
같은 트랜잭션에서 활성화한다. 사용자 API는 active membership만 읽기 때문에
작성자 DB에 추가 정책이 남아 있어도 깨끗한 심사자 DB와 같은 identity 집합을
반환한다. 설치 실패는 이전 active version을 변경하지 않는다.

## 실행

DB URL은 명령행 기록이나 문서에 평문으로 남기지 말고 운영 환경변수에서
전달한다.

```powershell
.\.venv\Scripts\python.exe scripts/audit_public_dataset_parity.py `
  --database-url "$env:DATABASE_URL" `
  --as-of 2026-08-24 `
  --require-parity
```

기본 보고서는 Git에서 제외된 `runtime/public_dataset/parity-report.json`에
원자적으로 저장된다. `--require-parity`에서 차이가 발견되면 종료 코드 2를
반환하며, 미해결 상태를 Release 통과로 취급하지 않는다.

## 지역 웹 Source 처리

지역 웹 수집 데이터는 다음 조건을 모두 만족해야 공개 dataset Source로 승격한다.

1. 제공기관의 정규화 사실 재배포 허용 근거
2. 전체 목록 종료와 identity 집합을 증명하는 완전 수집
3. 온통청년·복지로와의 ID·공식 URL·내용 중복 감사
4. Raw HTML·이미지·연락처·비밀정보 제외
5. 깨끗한 Docker 환경에서 동일 dataset version과 검색 결과 재현

승격 전 데이터는 운영 감사·관리자 검토에는 사용할 수 있지만 공개 사용자 결과의
정답으로 간주하지 않는다.

## 2026-08-24 로컬 acceptance 실제 감사

실행 중인 로컬 acceptance PostgreSQL에 계약 버전 `1.1.0`과 지정일
`2026-08-24`를 적용했다. 보고서에는 정책 본문이나 연락처를 기록하지 않았다.

| 지표 | 건수 |
| --- | ---: |
| 사용자 노출 후보 | 2,180 |
| 공개 Source 후보 | 2,088 |
| 현재 안전하게 발행 가능 | 2,032 |
| 공개 계약 밖 Source | 92 |
| 허용 Source의 content safety 제외 | 56 |
| 허용 Source와 제목 동일 검토 | 16 |
| 동일 제목도 없는 지역·보완 gap | 76 |
| 전체 parity gap | 148 |

지역·보완 Source 92건은 부산 12, 대구 24, 대전 1, 강원 3, 광주 7, 경북 2,
경남 8, 인천 15, 전북 13, 서울 1, 울산 4, 천안 1, 한국장학재단 1건이다.
현재 실행 이미지에는 새 인천 공공데이터 Source가 아직 적재되지 않아 해당 Source
수치는 0이다. 온통청년 1,627건 중 이메일 포함 54건과 개인 휴대전화 포함 2건,
총 56건은 content safety 경계 때문에 레코드 전체가 제외되는 현재 계약의 문제로
분리됐다.

따라서 다음 해소 순서는 허용 Source 56건의 안전한 정규화 방식 확정, 지역 92건의
재배포 권한·완전 수집 보강, 제목 일치 16건의 실제 중복 판정이다. 현재 판정은
`blocked`이며 이 수치를 Release 완료 증거로 사용하지 않는다.
