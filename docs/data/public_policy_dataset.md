# 공개 정책 dataset 계약

## 현재 기준

- Source contract: `1.1.0`
- NormalizedProgram Schema: `1.2.0`
- 검증일: `2026-08-25`
- 활성 version: `public-bootstrap-20260824-897152e7a18c15`

API key와 기존 PostgreSQL이 없는 사용자도 같은 정책 집합으로 서비스를
시작하게 하고, 로컬 수집·과거 개발 데이터가 사용자 검색에 섞이지 않게 하는
계약이다. 수집 가능 여부와 normalized 결과의 공개 재배포 가능 여부를 분리한다.

## 현재 공개 artifact

| 지표 | 값 |
| --- | ---: |
| 발행 후보 | 2,114건 |
| 안전성 제외 | 62건 |
| 공개 정책 | 2,052건 |
| 복지로 | 461건 |
| 온통청년 | 1,587건 |
| 인천 공공데이터 | 4건 |
| artifact bytes | 27,740,580 |
| artifact SHA-256 | `98703dc79ca53063c3685008d8cede04c4ed8f79dbad53c993e9ac480d6a0860` |
| 활성 identity SHA-256 | `9f65f2b1dae66b7f07b61310f5f3d07c024e0ab9e86eee843387f06d04afd0e5` |

제외 62건은 이메일 60건과 개인 휴대전화 형식 2건이다. 이 숫자는 위 불변
manifest의 기준값이다. `dataset-latest`가 새 version으로 바뀌면 새 manifest의
row count·Source 구성과 hash를 권위값으로 사용한다.

## Source default-deny

권위 계약은
[`public_policy_dataset_sources.json`](../../data/reference/public_policy_dataset_sources.json)이다.

| Source | 판정 |
| --- | --- |
| `bokjiro-central-welfare-api` | include |
| `youthcenter-api` | include |
| `data-go-kr-incheon-youth-programs` | include |
| `regional-*`와 등록 웹 Source | 명시적 재배포 근거 확인 전 exclude |

새 Source는 공식 제공기관, license URL, 확인일과 attribution이 Source contract에
추가되기 전까지 공개하지 않는다. 수동 수집 성공이나 관리자 DB 표시만으로
공개 승격하지 않는다.

## 필드와 안전 경계

artifact는 `normalized_program.schema.json`의 허용 필드만 포함한다. 다음
데이터는 제외한다.

- PostgreSQL 내부 ID·생성·갱신·비활성 시각과 dump
- Raw API/XML/HTML payload, 이미지와 첨부파일
- API key, token, credential query와 DB 접속정보
- 기관 연락처, 이메일과 개인 휴대전화 형식
- Source allowlist 밖의 normalized 정책

위험한 값을 임의로 마스킹해 의미가 바뀐 정책을 만들지 않고 해당 row 전체를
제외한다. 후보·제외 사유·발행 수는 manifest에 기록한다.

## artifact·manifest

| 항목 | 규칙 |
| --- | --- |
| dataset version | `public-bootstrap-YYYYMMDD-<git-sha>` |
| filename | `cheongnyeon-alimi-<dataset-version>.json` |
| 정렬 | `source_id`, `external_id`, 안정적 보조 key |
| 형식 | UTF-8 JSON, 결정적 key 순서와 마지막 newline |
| 무결성 | byte 수·row 수·SHA-256 |
| 연결 | Git SHA, Normalized Schema hash, Source contract hash |
| 표시 | Source별 row 수·license URL·attribution |
| 안전성 | Raw·dump false, 연락처·비밀 pattern count 0 |

Schema는
[manifest](../../data/schema/public_policy_dataset_manifest.schema.json)와
[latest pointer](../../data/schema/public_policy_dataset_pointer.schema.json)를
따른다.

## 발행과 승격

1. 보호된 중앙 환경에서 허용 Source를 완전 수집한다.
2. lifecycle·품질·content safety와 지역 coverage를 검증한다.
3. 결정적 artifact와 manifest를 생성한다.
4. 격리 DB에 설치해 목록·검색·추천·상세 projection과 identity hash를 확인한다.
5. 불변 `dataset-<version>` GitHub Release에 artifact·manifest를 올린다.
6. 원격 다운로드와 hash를 다시 검증한다.
7. 마지막에만 `dataset-latest` pointer를 새 manifest로 교체한다.

어느 단계든 실패하면 이전 pointer를 유지한다. 최근 성공 version과 application
Release가 참조하는 version은 보존 정책에 따라 유지한다.

## 사용자 설치

`run_docker.bat`은 pointer, manifest와 artifact를 순서대로 검증하고 단일
transaction으로 정책·설치·membership을 반영한다. 모든 row와 identity가
확인된 뒤 새 설치를 활성화하며, 실패하면 이전 활성 version을 유지한다.

사용자 목록·검색·추천·상세는 활성 membership만 읽는다. 작성자 DB에 공개
allowlist 밖 정책이 있어도 사용자 API에 포함하지 않는다.

## 로컬 생성·검증

실제 DB URL은 환경변수로 전달하고 로그·문서에 출력하지 않는다.

```powershell
python -B scripts/build_public_bootstrap_dataset.py `
  --database-url "$env:DATABASE_URL" `
  --dataset-version public-bootstrap-YYYYMMDD-abcdef0 `
  --generated-at 2026-08-25T00:00:00+00:00 `
  --git-sha 0000000000000000000000000000000000000000

python -B scripts/build_public_bootstrap_dataset.py `
  --verify-manifest runtime/public_dataset/<version>.manifest.json
```

Runtime artifact와 manifest는 Git에 commit하지 않는다. 공개 artifact는
versioned GitHub Release로만 배포한다.
