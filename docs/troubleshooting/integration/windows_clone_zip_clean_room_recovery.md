# Windows clone·ZIP clean-room 복구

## 문제 상황

W6-P5에서 작성자 환경과 분리한 Git clone과 GitHub ZIP을 각각 새 Compose
project·cache·Volume으로 실행했다. 이 과정에서 최초 실행 안전성 문제와 실제
Browser 사용자 차단 문제가 함께 재현됐다.

- 명시한 clean-room project가 아닌 기본 project Volume을 검사했다.
- Volume이 아직 없을 때 Windows PowerShell이 native error를 예외로 바꿨다.
- 새 PowerShell process에서 `Get-FileHash`와 ACL cmdlet module 자동 로드가
  안정적이지 않았다.
- GitHub ZIP에는 `.git`이 없어 `.env.compose`의 ignore 여부 검사가 실패했다.
- 발행된 457건이 모두 `partial`인데 사용자 정책 목록과 추천은 이를 기본
  제외해 목록 0건을 표시했다.
- 목록이 partial을 포함한 뒤에도 API limit 100 때문에 나머지 357건에 접근할
  수 없었다.
- 추천 API가 여섯 번째 항목에서 category `기타`, status `unknown`을 반환하자
  Frontend가 이를 내부 enum으로 단언해 category theme 조회 중 화면 전체가
  ErrorBoundary로 전환됐다. Backend 요청 자체는 `200`이었다.

## 실제 원인과 해결

1. 실행기 Volume 검사를 `ComposeProjectName`으로 계산한 정확한 이름에 연결하고,
   `docker volume ls --quiet` 결과의 exact match로 존재 여부를 판정했다.
2. 파일 SHA-256은 PowerShell module 대신 .NET stream과
   `Security.Cryptography.SHA256`으로 계산했다.
3. `.env.compose` ACL은 module cmdlet 대신 .NET file security API로 적용했다.
4. clone에서는 `git check-ignore`를 사용하고, `.git`이 없는 ZIP에서는 루트
   `.gitignore`가 `.env.*`를 포함하는지 fail-closed로 확인했다.
5. 서버 API의 보수적 기본값은 유지하고 사용자 목록·홈·맞춤 추천 요청만
   `include_partial=true`를 명시했다. partial badge와 원문 확인 안내는 유지했다.
6. 정책 목록에 기존 공용 pagination을 연결해 100건씩 5페이지를 제공했다.
7. 추천 category는 알려진 값 외에는 `other`, application status는 알려진 값
   외에는 `null`로 정규화한 뒤 UI theme과 deadline 판정에 전달했다.
8. Playwright와 전이 의존성의 high advisory 4건을 lockfile에서 갱신하고 CI에
   high audit를 추가했다.

## 결과

- 최종 runtime 후보: `d420608bc1cc3d782603afc1eea1f2670fcf7449`
- GitHub ZIP SHA-256:
  `5ba8cc02de44a17f56ee92c509e295ab085affd65d4e261b8785dd5ef0ea0914`
- 공개 dataset: `public-bootstrap-20260824-f5883bb79c594f`, 457건,
  artifact SHA-256
  `6457a37f109381384eb238bb84fd43dd5b60f0d37bc3a262d2c4e483a27ed1f9`
- 최초 ZIP 실행: Migration `0001 → 20260824_0010`, `inserted 457`, 장기
  service 6개 healthy
- offline 재실행: `inserted 0`, `unchanged 457`, 전후 공개 행 수 457와 DB·
  Redis·Log·Runtime Volume 4개 보존
- actual Browser: 정책 `1-100 / 457`과 `401-457 / 457`, 상세 원문·partial
  경고, 북마크, 추천 457건·미확정 안내, 관리자 PIN·정책·CollectionRun·Log 통과
- Frontend 격리 회귀: dependency audit 0, 225 tests, lint, production build PASS

clone 검증에서는 worker 중지·Redis 재시작·terminal task 재전달 후에도 같은
CollectionRun 한 건만 성공했고 정책 457건을 유지했다. 임시 active·expired·
inactive 정책의 공개 상세 응답은 `200·404·404`였으며, PostgreSQL dump 복원본의
정책 identity·CollectionRun aggregate도 원본과 일치했다. hash 불일치 artifact는
DB 쓰기 전에 중단됐고 rollback pointer는 실제 latest를 바꾸지 않는 dry-run으로
검증했다.

## 재발 방지

- clone과 ZIP을 별도 clean-room 입력으로 취급하고 둘 다 실행한다.
- custom port를 쓴 project는 재시작 때 같은 port 인자를 다시 전달한다.
- 공개 dataset 품질 분포가 바뀌면 API 기본값뿐 아니라 실제 UI 요청과 첫 화면
  결과 수를 Browser로 확인한다.
- 외부 API의 string enum은 TypeScript cast로 신뢰하지 않고 runtime allowlist로
  정규화한다.
- 실행기 안전 검사는 PowerShell module 자동 로드나 `.git` 존재를 전제로 하지
  않는다.
