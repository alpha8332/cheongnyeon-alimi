# 공개 dataset 사용자 결과 동등성

## 목적

작성자 DB, Git clone과 Download ZIP 사용자가 같은 공개 정책 identity 집합을
보게 한다. PostgreSQL 전체 row 수와 CollectionRun 수가 아니라 활성 dataset
version·row count·identity hash를 비교한다.

## 공개 projection

사용자 목록·검색·추천·상세는 다음 조건을 모두 적용한다.

```text
active public_dataset_membership
AND inactive_at IS NULL
AND application_end가 없거나 KST 오늘 이후
AND 공개 허용 data_quality_status
```

작성자 DB에 로컬 웹 수집이나 과거 정책이 남아 있어도 active membership 밖의
row는 사용자 API에서 제외한다. 관리자 읽기 전용 정책 화면은 운영 감사를 위해
더 넓은 DB 범위를 보여줄 수 있다.

## 설치 원자성

manifest·artifact SHA-256, byte 수, row 수, Schema, 중복 identity와 모든
`source_id + external_id`를 먼저 검증한다. 정책 upsert,
`public_dataset_installations`와 `public_dataset_memberships` 변경은 한
transaction으로 실행한다.

- 전체 검증 성공 후에만 새 version을 active로 바꾼다.
- 실패하면 rollback하고 이전 active version을 유지한다.
- dataset 밖 기존 정책을 물리 삭제하지 않는다.
- 즐겨찾기 등 기존 정책 FK를 보존한다.

## 현재 검증 기준

| 항목 | 값 |
| --- | --- |
| version | `public-bootstrap-20260825-38180bc7a837ef` |
| 공개 정책 | 2,051건 |
| Source | 복지로 461, 온통청년 1,586, 인천 4 |
| identity SHA-256 | `85b70773cb64c7f97e2ffb7270be4dd68c892c23624f807a971b1585b808d76e` |

`2026-08-26` clean Volume 검증에서 API key와 수동 DB 적재 없이 위 정책 수와
identity hash가 일치했다. 주거 필터·자연어 검색·추천 category 불일치는 0건,
Compose 장기 서비스 6개 health를 확인했다.

## 발행 전 parity 감사

`scripts/audit_public_dataset_parity.py`는 지정일의 사용자 노출 후보를
`publishable`, `excluded_source`, `content_safety_excluded`와 검토 후보로
분리한다. 공개 가능한 후보가 artifact에서 빠지는 `parity_gap_row_count`가
0일 때만 통과한다.

```powershell
.\.venv\Scripts\python.exe scripts/audit_public_dataset_parity.py `
  --database-url "$env:DATABASE_URL" `
  --as-of 2026-08-25 `
  --require-parity
```

보고서는 정책 본문·연락처와 DB credential을 포함하지 않고 Source별 안전한
집계만 기록한다. 제목 일치는 자동 중복 삭제 근거가 아니라 검토 후보로만
사용한다.

## 지역 Source

지역 웹 Source를 공개 dataset에 추가하려면 다음을 모두 충족해야 한다.

1. normalized 사실의 재배포 허용 근거
2. 완전 수집과 identity 집합 증명
3. 온통청년·복지로와의 중복 감사
4. Raw·이미지·연락처·비밀정보 제외
5. 격리 DB projection과 clean-room clone·ZIP 동등성

승격 전 데이터는 관리자 검토와 로컬 수집 이력에 남을 수 있지만 사용자 공개
정답으로 사용하지 않는다.

상세 QA 근거는
[v1.0.2 개선 기록](../troubleshooting/integration/v1_0_2_qa_improvements.md)을
따른다.
