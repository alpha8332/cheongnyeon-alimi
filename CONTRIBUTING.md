# 청년정책알리미에 기여하기

버그 제보, 문서 개선, 정책 데이터 품질 검토와 코드 기여를 환영합니다.

## 기여 전에 확인할 내용

1. 중복 Issue와 Pull Request가 있는지 확인합니다.
2. 큰 기능이나 데이터 계약 변경은 구현 전에 Issue에서 범위를 합의합니다.
3. 비밀정보, 개인정보, Runtime Raw, DB dump와 API key를 Issue·commit에 넣지
   않습니다.
4. 정책 데이터는 공식 Source와 원문 근거를 사용하고 재배포 계약을 지킵니다.

데이터 기여의 세부 기준은
[수집 정책](docs/data/collection_policy.md),
[공개 dataset 계약](docs/data/public_policy_dataset.md),
[정규화 규칙](docs/data/normalization_rules.md)을 따릅니다.

## 개발 환경

서비스를 먼저 확인하려면 README의
[바로 실행하기](README.md#바로-실행하기)를 사용하세요. Docker 실행에는
Python·Node.js를 host에 설치할 필요가 없습니다.

코드 개발 환경은 영역별 문서를 따릅니다.

- 전체 문서 안내: [docs/index.md](docs/index.md)
- Backend Windows 환경: [docs/development/backend_local_setup.md](docs/development/backend_local_setup.md)
- Frontend 명령: [frontend/package.json](frontend/package.json)
- Collector 실행: [docs/operations/collector.md](docs/operations/collector.md)

## 변경 작성

- 하나의 Pull Request에는 하나의 명확한 목적을 담습니다.
- 기존 사용자 변경과 공개 데이터 계약을 임의로 되돌리지 않습니다.
- commit은 [Conventional Commits 규칙](docs/governance/commit_convention.md)을
  따릅니다.
- 코드와 동작이 바뀌면 관련 테스트와 사용자·운영 문서를 함께 갱신합니다.
- 자동 생성 build 결과, 가상환경, 로그와 로컬 설정은 commit하지 않습니다.

## 검증

변경 영역에 맞는 테스트와 다음 공통 검증을 실행합니다.

```powershell
python scripts/validate_docs.py
git diff --check
git status --short
```

Python 명령은 저장소 `.venv`, `uv`, Windows `py` launcher 등 프로젝트에서
사용 중인 환경에 맞게 실행할 수 있습니다. 전체 CI는 다음을 검증합니다.

- PostgreSQL 기반 Backend/Data pytest
- 문서 링크·색인·비밀 경계
- Frontend unit test·lint·production build·dependency audit
- Docker image·Production Compose 계약

## Pull Request

PR 본문에는 다음을 포함해 주세요.

- 해결하려는 문제와 변경 범위
- 주요 구현 내용
- 실행한 테스트와 실제 결과
- DB·API·화면 또는 데이터 계약에 미치는 영향
- 남아 있는 위험과 재현 방법

리뷰에서 확인되지 않은 기능을 완료로 표시하거나 실행하지 않은 테스트를 통과로
기록하지 않습니다.
