# 공개 정책 bootstrap dataset 계약

## 문서 상태

- 상태: current
- 계약 버전: `1.1.0`
- 확정일: `2026-08-24`
- Gate: `W6-P0_DATASET_CONTRACT_PASS`
- 대상 Schema: `NormalizedProgram 1.2.0`

## 목적

API key와 작성자 로컬 PostgreSQL이 없는 사용자도 공개 재배포가 허용된
정규화 정책으로 서비스를 시작할 수 있게 한다. 수집 가능 여부와 공개 dataset
재배포 가능 여부를 분리하고, 명시적으로 허용한 Source만 발행하는 default-deny
계약을 적용한다.

이 문서는 법률 자문이 아니라 저장소와 배포 파이프라인이 따르는 보수적인
공개 경계다. 이용 조건이 바뀌거나 근거가 불명확해지면 기존 허용을 자동
연장하지 않고 다시 검토한다.

## Source 공개 판정

`2026-08-23` 실제 DB에는 16개 Source 3,273건이 있다. 수집·서비스 표시에
승인된 Source라도 공개 재배포 근거가 없으면 bootstrap dataset에서는 제외한다.

| Source 또는 범위 | 공개 판정 | 근거 |
| --- | --- | --- |
| `bokjiro-central-welfare-api` | include | 공공데이터포털의 한국사회보장정보원 중앙부처복지서비스가 이용허락범위를 `제한 없음`으로 표시 |
| `youthcenter-api` | include | 공공데이터포털 이용허락범위 `제한 없음` 및 프로젝트의 API 이용·최소 정규화 데이터 재배포 승인 확인 |
| `regional-*` | exclude | Source별 수집은 승인됐으나 명시적 개방 라이선스가 없고 원문·이미지 비재배포 경계로 운영 |
| `cheonan-youthcenter-web` | exclude | 별도 이용약관을 찾지 못했고 사이트가 `all rights reserved`를 표시 |
| `kosaf-scholarship-web` 등 보완 웹 Source | exclude | 공개 접근은 가능하지만 정규화 결과의 재배포 허가가 명시되지 않음 |
| `work24-policy-web` | exclude | 개별 자료의 공공누리 표시 확인 전에는 담당자 사전 협의가 필요 |

권위 계약은
[`public_policy_dataset_sources.json`](../../data/reference/public_policy_dataset_sources.json)이며,
새 Source는 이 파일에 `include` 근거가 추가되기 전까지 자동 제외된다.

공식 근거:

- [한국사회보장정보원 중앙부처복지서비스](https://www.data.go.kr/data/15090532/openapi.do)
- [한국고용정보원 온통청년 청년정책API](https://www.data.go.kr/data/15143273/openapi.do)
- [온통청년 OPEN API 이용방법](https://www.youthcenter.go.kr/cmnFooter/openapiIntro/oaiGuide)
- [온통청년 이용약관](https://www.youthcenter.go.kr/cmnFooter/termsInfo)
- [고용24 저작권정책](https://m.work24.go.kr/cm/c/d/0130/retrieveCpyrPoly.do)

## 필드 계약

공개 artifact는
[`normalized_program.schema.json`](../../data/schema/normalized_program.schema.json)의
필수 필드 37개로 구성된 JSON 배열이다. Source license가 정규화된 정책 사실의
재배포를 허용할 때만 해당 레코드를 포함한다.

다음 DB·Runtime 내용은 포함하지 않는다.

- PostgreSQL `id`, `created_at`, `updated_at`, `last_seen_at`,
  `last_verified_at`, `inactive_at`
- PostgreSQL dump, Volume과 Migration 내부 상태
- Raw API/XML/HTML payload와 첨부파일
- API key, token과 비밀 query parameter
- 이메일, 개인 휴대전화 형식과 `institutional_contacts`
- allowlist에 없는 Source의 정규화 정책

자유 텍스트에 이메일·개인 휴대전화 형식이 있거나 URL에 비밀 query key가
있으면 값을 임의 마스킹하지 않고 레코드 전체를 제외한다. 후보·발행·제외
수치는 manifest에 남긴다.

## Artifact와 manifest

| 항목 | 규칙 |
| --- | --- |
| dataset version | `public-bootstrap-YYYYMMDD-<git-sha>` |
| dataset filename | `cheongnyeon-alimi-<dataset-version>.json` |
| 정렬 | `source_id`, `external_id`, DB `id`의 결정적 순서 |
| 문자·JSON | UTF-8, key 정렬, 마지막 newline |
| 무결성 | artifact byte 수·row 수·SHA-256 |
| 연결 | Git SHA, Normalized Schema hash, Source contract hash |
| Source 표시 | Source별 row 수·license URL·출처 문구 |
| 안전 경계 | Raw·dump 포함 여부와 연락처·비밀 pattern count 0 |
| 이전 버전 | 첫 발행은 `null`, 이후 직전 성공 dataset version 기록 |

Manifest 계약은
[`public_policy_dataset_manifest.schema.json`](../../data/schema/public_policy_dataset_manifest.schema.json),
latest pointer 계약은
[`public_policy_dataset_pointer.schema.json`](../../data/schema/public_policy_dataset_pointer.schema.json)을
따른다.

## 배포 위치와 보존

W6-P4에서 다음 구조로 발행한다. W6-P0의 Runtime proof artifact는 아직 외부로
발행하지 않는다.

W6-P1부터 artifact 후보 query에도 사용자 API와 같은 lifecycle 경계를 적용해
inactive 정책과 Asia/Seoul 기준 종료일 경과 정책을 발행하지 않는다.

- GitHub Release immutable tag:
  `dataset-<public-bootstrap-YYYYMMDD-git-sha>`
- Release asset: dataset JSON과 manifest JSON
- `dataset-latest`에는 작은 pointer JSON만 두고 immutable manifest URL과
  SHA-256을 가리킴
- versioned artifact 업로드·다운로드 재검증 뒤에만 latest pointer 갱신
- 최근 성공 12개와 application release가 참조한 version은 보존
- 그 외 artifact는 최소 90일 뒤 별도 승인된 정리 작업에서만 삭제
- 실패·partial 수집·hash 불일치 시 직전 latest pointer 유지
- 발행 전 격리 DB에 후보 artifact를 설치·활성화하고, 활성 membership 기준
  사용자 projection parity가 통과한 경우에만 immutable Release 생성

`run_docker.bat`은 P3에서 latest pointer → manifest → dataset 순으로 hash를
검증하고, 네트워크 실패 시 검증된 cache 또는 release 고정 fallback을 사용한다.

## W6-P0 실제 검증 기준선

Acceptance DB `f838d4191cb5cc33c324d3e946c7a12ed8a56b1b` 기준:

| 지표 | 결과 |
| --- | ---: |
| 전체 DB | 3,273건 |
| allowlist Source 후보 | 461건 |
| 개인 휴대전화 형식으로 제외 | 10건 |
| 공개 artifact | 451건 |
| 후보 대비 발행률 | 97.83% |
| 전체 DB 대비 공개 범위 | 13.78% |
| artifact bytes | 1,247,899 |
| artifact SHA-256 | `28c36be54ee859b63a496e2cea295d58ab88eb438ef1ffcce0b647198cf8ccb3` |

Artifact는 `runtime/public_dataset/`에 생성해 Git에서 제외했다. 공개 발행은
P4 promotion Gate 뒤 새 SHA·새 version으로 다시 생성한다.

## 생성과 검증

중앙 운영 환경에서 명시적 DB URL과 version을 주입한다. 실제 비밀번호와 URL은
문서·로그에 출력하지 않는다.

```powershell
python -B scripts/build_public_bootstrap_dataset.py `
  --database-url "$env:DATABASE_URL" `
  --dataset-version public-bootstrap-YYYYMMDD-abcdef0 `
  --generated-at 2026-08-23T00:00:00+00:00 `
  --git-sha 0000000000000000000000000000000000000000
```

생성 뒤에는 DB 연결 없이 manifest와 sibling artifact를 다시 검증한다.

```powershell
python -B scripts/build_public_bootstrap_dataset.py `
  --verify-manifest runtime/public_dataset/<version>.manifest.json
```

검증은 Source·field allowlist, NormalizedProgram Schema, artifact·contract·Schema
hash, row 수와 연락처·비밀 pattern을 다시 확인한다.

## 변경 규칙

- Source include에는 공식 license URL, 확인일과 출처 문구가 필요하다.
- Source 약관·라이선스 변경 시 contract version과 dataset version을 올린다.
- 허용 필드가 바뀌면 Schema와 Backend bootstrap 소비 검토를 먼저 수행한다.
- 현재 제외 Source 공개에는 제공기관의 명시적 허가 또는 재배포 가능한 별도
  공공데이터 목록 근거가 필요하다.
- Runtime artifact·manifest를 Git에 커밋하지 않는다.
