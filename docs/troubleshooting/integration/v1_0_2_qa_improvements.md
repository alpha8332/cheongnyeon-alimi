# v1.0.2 공개 데이터·검색·추천 QA 개선

## 문서 상태

- 상태: 해결 완료, `v1.0.2` Production Release 발행 완료
- 성격: 실제 재현 오류·개선사항과 회귀 검증 기록

## 작업 정보

- 작업일: `2026-08-24`~`2026-08-25`
- 영역: Data·Backend·Frontend·Integration QA
- 작업 브랜치: `fix/qa/v1.0.2-v1`
- 시작 기준: `eb968431bfb1169e608f468746cde6fb2c868bf3`
- 현재 검증 기준: `03eb506176ff6b081febdbcee013eece3fcc28e9`
- Release 기준: `c3d3935a196a024037168e9afb5a94dfef4542e3`
- 대상 Release: `v1.0.2` 후보

## 목적

작성자 PC와 Git clone·Download ZIP 사용자의 정책 결과가 달랐던 문제를
제거하고, 실제 사용자 리뷰에서 재현된 지역 검색·예시 검색·복수 분야·프로필
추천·정렬 문제를 하나의 공개 dataset과 검색 계약으로 정리한다.

이번 기록은 계획을 소급 작성한 문서가 아니다. 위 기준 SHA 이후 실제로
구현하고 테스트한 변경만 기록한다. `CollectionRun`은 각 환경의 로컬 실행 감사
이력이므로 동일 건수를 요구하지 않고, 사용자에게 공개되는 활성 정책 identity와
검색 결과의 동등성을 검증 대상으로 삼는다.

## 개선 범위

1. 지역 검색 의미와 사용자 안내 수정
2. 공개 Source 확대와 작성자·심사자 결과 동등성 Gate
3. 활성 공개 dataset projection과 안전한 설치·교체
4. 예시 검색·복수 관심 분야·복수 정책 분야·결정적 정렬
5. 홈 검색 조건과 프로필 기반 추천 통합
6. Docker actual·API·Browser 회귀 검증

## 변경 진행 현황

| 묶음 | 상태 | 결과 |
| --- | --- | --- |
| 지역 검색 정확성 | 완료 | 하위 지역·상위 관할·전국 포함, 미확정과 확정 일치 분리 |
| 공개 데이터 동등성 | 완료 | 3개 허용 Source, 활성 membership, parity·지역 coverage Gate |
| 검색·프로필 UX | 완료 | 예시 검색 보정, 복수 관심 분야, 정렬, 홈 조건·추천 통합 |
| 복수 분야 표시 | 완료 | 목록·자연어 검색·추천·상세에 전체 `categories` 표시 |
| 현재 PC actual | 완료 | 공개 2,052건, API·Docker·데스크톱·390px 검증 |
| Production Release | 완료 | `v1.0.2` tag, GHCR image, provenance, clean Production smoke, Release 영수증 |
| 외부 clone·ZIP 제출 Gate | 대기 | 발행된 tag source archive를 별도 물리 PC에서 README 절차로 최종 대조 |

## 구현 내용

### 지역 검색과 지역 정책

- 지역 정보가 없는 정책을 임의의 지역 일치로 만들지 않고 `unknown` 후보로
  구분해 공식 원문 확인 안내를 유지했다.
- `양산`, `양산시`, `경상남도 양산시`처럼 접미사 유무와 상위 관할이 결합된
  표현을 같은 canonical 지역으로 해석한다.
- 광역자치단체 검색에는 해당 광역 단독 정책, 하위 시·군·구 정책과 전국 정책을
  함께 포함한다. 시·군·구 검색에는 해당 지역·상위 관할·전국 정책을 포함한다.
- 확정 지역 정책을 일반 전국·미확정 정책보다 우선하고, 미확정 정책에는 카드와
  우측 분석 패널에서 지역 근거 부족을 명시한다.
- 지역 검색 결과에 확정·미확정이 섞이면 요약 경고를 표시해 신청 가능 지역으로
  오해하지 않게 했다.

관련 커밋:

- `2c16ae7 fix(search): keep region-unknown policies discoverable`
- `f793e85 fix(search): resolve suffixless local region names`
- `abe6627 fix(search): include descendant regional policies`
- `f079a8c fix(ui): distinguish unconfirmed regional matches`
- `28df521 fix(search): prioritize local regional policies`
- `0ce5eaf fix(ui): show regional warning summary`
- `838d495 fix(search): resolve compound local region queries`

### 공개 Source와 결과 동등성

- 재배포가 허용된 인천 청년 프로그램 파일 데이터와 승인된 온통청년 API를
  공개 dataset Source에 추가했다.
- 발행 전 작성자 DB의 사용자 노출 후보와 공개 artifact를 비교하는 parity Gate를
  추가했다. 지역 coverage가 비어 있거나 Source 결과가 누락되면 latest pointer를
  갱신하지 않는다.
- `public_dataset_installations`와 `public_dataset_memberships`로 활성 dataset의
  정확한 `source_id + external_id` 집합을 기록한다.
- artifact·manifest hash, row 수와 모든 identity를 단일 트랜잭션에서 검증한 뒤에만
  새 version을 활성화한다. 실패하면 이전 활성 version을 유지한다.
- 작성자 DB의 로컬 수집·과거 정책은 삭제하지 않지만, 목록·검색·추천·상세 사용자
  API는 활성 membership만 조회한다.
- 수동 수집 결과는 DB에 보존하되 자동 공개하지 않고 별도 승격 전 상태로 둔다.

관련 커밋:

- `d0e4997 feat(data): add licensed Incheon youth programs`
- `9e04355 feat(data): publish approved Ontong Youth policies`
- `6a2c5dc feat(data): gate public dataset on result parity`
- `a45c25b feat(data): isolate the active public dataset projection`
- `467b1b1 fix(data): gate releases on the active dataset projection`
- `f2a4377 fix(data): enforce regional coverage in public releases`
- `62f3880 docs(data): describe the live public dataset pointer`

현재 공개 Source 계약은
[공개 정책 bootstrap dataset 계약](../../data/public_policy_dataset.md)과
[`public_policy_dataset_sources.json`](../../../data/reference/public_policy_dataset_sources.json)을
따른다.

### 검색·프로필·복수 분야 UX

- 홈 예시 검색어를 실제 결과가 있는 curated query로 보정하고, `대학생`처럼
  범위가 넓은 표현에는 사용자가 선택할 수 있는 관련 검색어를 함께 제공한다.
- 프로필 관심 분야를 단일 값에서 중복 없는 복수 선택으로 확장했다. 복수 관심
  분야는 OR로 후보를 평가하고, 자연어 검색 조건을 강제로 덮지 않으며 동률 안에서
  관련도를 보정한다.
- 정책 `categories` 배열을 목록·자연어 검색·추천·상세에 모두 전달하고 표시한다.
  주거 필터로 검색된 `housing + welfare` 정책은 `주거·복지`를 모두 보여준다.
- 검색 결과에 관련도·가나다·마감·수집일 오름차순/내림차순을 추가하고, 같은
  입력과 dataset에서 순서가 바뀌지 않도록 최종 identity tie-break를 적용했다.
- 홈에 `시·도 → 시·군·구`, 관심 분야와 `저장 프로필로 관련도 보정` 조건을
  추가했다. 검색어가 없어도 명시 조건만으로 검색할 수 있다.
- 별도 맞춤 추천 메뉴를 주 내비게이션에서 제거하고, 저장 프로필과 연동된 추천
  요약·추천 이유를 홈 검색 결과와 가까운 위치에 배치했다. 기존
  `/recommendations` URL은 호환성과 상세 조건 편집을 위해 유지한다.

관련 커밋:

- `d4f4efa fix(search): make curated queries return useful results`
- `60e7da7 feat(profile): apply multi-interest search preferences`
- `0883df5 fix(policy): show all matching categories`
- `23752a5 feat(search): add deterministic result sorting`
- `7e37812 test(recommendation): align e2e with multi-interest controls`
- `9125c9c feat(home): unify search conditions and personalized recommendations`
- `03eb506 test(policy): cover multi-category card display`

검색 API와 추천 요청의 현재 계약은 [Policy API](../../api/policies.md)와
[맞춤 정책 추천 API](../../api/recommendation.md)를 따른다.

## 현재 공개 dataset 검증

`2026-08-25`에 `run_docker.bat -NoBrowser`를 현재 브랜치에서 다시 실행했다.
latest pointer가 가리킨 version과 manifest 결과는 다음과 같다.

| 항목 | 결과 |
| --- | ---: |
| dataset version | `public-bootstrap-20260824-897152e7a18c15` |
| 공개 정책 | 2,052건 |
| 복지로 | 461건 |
| 온통청년 | 1,587건 |
| 인천 공공데이터 | 4건 |
| 발행 후보 | 2,114건 |
| 내용 안전성 제외 | 62건 |
| artifact SHA-256 | `98703dc79ca53063c3685008d8cede04c4ed8f79dbad53c993e9ac480d6a0860` |
| 활성 identity SHA-256 | `9f65f2b1dae66b7f07b61310f5f3d07c024e0ab9e86eee843387f06d04afd0e5` |

복지로·온통청년·인천 파일 데이터만 공개 Source membership에 포함된다. 라이선스
근거가 없는 지역 웹 수집 결과는 작성자 DB에 남아 있어도 공개 사용자 API에서
제외된다. 온통청년이 전국과 지역 청년정책을 공급하므로 사용자는 별도 API key나
DB 적재 없이 지역 정책을 검색할 수 있다.

## 검증 결과

### 자동 테스트

| 검증 | 결과 |
| --- | --- |
| Backend 정책·추천 관련 테스트 | `19 passed` |
| Frontend unit | `241 passed` |
| Frontend lint | 통과 |
| 검색 E2E Mock | `13 passed, 1 skipped` |
| 검색 E2E actual API | `12 passed, 2 skipped` |
| 추천 E2E actual API | `9 passed, 4 skipped` |
| Docker production Frontend build | 통과 |
| Compose 장기 서비스 | Backend·Frontend·DB·Redis·worker·scheduler 모두 healthy |

### 실제 API와 Browser

- `category=housing` 정책 목록 213건에서 분야 불일치 0건을 확인했다.
- `q=주거&category=housing` 자연어 검색 123건에서 분야 불일치 0건을 확인했다.
- 같은 검색 첫 페이지에 `주거안정 월세대출(housing, finance)`,
  `폭력피해자 주거지원 사업(housing, welfare)` 등 복수 분야 정책이 포함됐다.
- 주거 관심 분야 추천은 135건을 반환했고 첫 20건의 분야 불일치가 0건이었다.
- 실제 카드와 상세에서 `주거안정 월세대출`의 `주거·금융`이 모두 표시됐다.
- 390×844 viewport에서 두 분야 배지가 모두 보이고 카드·본문의 가로 overflow가
  없었다.

## 설계 결정

- 공개 정책 수와 identity는 같은 dataset version에서 모든 사용자에게 같아야 한다.
- `CollectionRun` 수는 설치·재실행·수동 수집에 따른 환경별 감사 기록이므로 같을
  필요가 없다. 공개 dataset 설치 실행도 로컬 기록으로 추가될 수 있다.
- 지역 정보가 없으면 전국으로 추정하지 않는다. 전국은 명시 근거가 있을 때만
  확정하고 그 밖에는 미확정 안내를 제공한다.
- 정책 분야는 단일 대표값이 아니라 `categories` 배열을 권위값으로 사용한다.
- 프로필 조건은 검색어를 숨은 필터로 덮지 않고 명시 toggle 아래에서 우선순위
  보정에 사용한다.

## 알려진 제약과 남은 작업

- 현재 HEAD의 다른 물리 Windows PC clone·Download ZIP 검증은 아직 완료되지
  않았다. 이전 457건 clean-room 결과는 역사적 증거이며 현재 2,052건 후보의
  Final Gate를 대신하지 않는다.
- `v1.0.2`는 최종 `main` `c3d3935`에서 발행됐다. Production workflow
  [run 32840085712](https://github.com/alpha8332/cheongnyeon-alimi/actions/runs/32840085712)가
  CI, GHCR image·provenance, dataset 검증, clean Production Compose smoke와
  Release 영수증 업로드를 모두 통과했다.
- Production Frontend build는 약 594 KiB JavaScript chunk에 대해 500 KiB 경고를
  낸다. 기능 오류는 아니며 후속 code splitting 성능 개선 후보로 남긴다.
- 코드를 pull한 뒤 이전 Docker 컨테이너를 계속 사용하면 새 API 계약이 보이지
  않을 수 있다. [Windows Docker 최초 실행](../../operations/docker_first_run.md)에
  따라 `run_docker.bat`을 다시 실행해 이미지를 재빌드한다.
