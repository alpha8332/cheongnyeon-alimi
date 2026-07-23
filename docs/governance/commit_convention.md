# 커밋 작성 규칙

## 1. 기본 형식

커밋 메시지는 Conventional Commits 형식을 사용한다.

```text
<type>(<scope>): <description>
```

본문이나 footer가 필요한 경우 제목 다음에 빈 줄을 두고 작성한다.

## 2. Type

| Type | 용도 |
| --- | --- |
| `feat` | 새로운 기능 |
| `fix` | 오류 수정 |
| `refactor` | 기능 변화 없는 구조 개선 |
| `test` | 테스트 추가 또는 수정 |
| `docs` | 문서 추가 또는 수정 |
| `chore` | 패키지, 설정과 파일 정리 |
| `style` | 동작에 영향 없는 코드 포맷 변경 |
| `perf` | 성능 개선 |
| `ci` | GitHub Actions 등 CI 변경 |

## 3. Scope

변경의 주된 영역을 소문자 scope로 사용한다.

```text
frontend
backend
collector
database
schema
search
recommendation
notification
docker
docs
governance
```

여러 영역을 변경하더라도 커밋의 핵심 책임을 가장 잘 나타내는 하나를
선택한다. 하나를 고르기 어렵다면 커밋을 나눌 수 있는지 먼저 검토한다.

## 4. Description

- 영어 소문자로 작성한다.
- 명령형 또는 현재형 동사를 사용한다.
- 마침표를 붙이지 않는다.
- 무엇을 변경했는지 구체적으로 표현한다.
- 한 커밋에는 하나의 논리적 변경만 포함한다.

좋은 예:

```text
feat(collector): add youthcenter api collector
feat(backend): add program list endpoint
feat(frontend): implement policy search page
feat(schema): define normalized program schema
fix(collector): handle missing application deadline
test(collector): add web parser cases
docs(schema): document program data contract
```

피해야 할 예:

```text
update files
fix bug
feat: add collector and redesign frontend
```

## 5. 본문과 Footer

제목만으로 변경 이유나 영향이 분명하지 않으면 본문에 다음 내용을 간결하게
작성한다.

- 변경 이유
- 이전 동작과 달라진 점
- 마이그레이션 또는 운영상 주의사항
- 검증 방법

호환성을 깨는 변경은 type 뒤에 `!`를 붙이고 footer에 설명한다.

```text
feat(schema)!: require source url

BREAKING CHANGE: normalized programs without source_url are no longer valid
```

Issue를 연결할 때는 저장소에서 사용하는 footer 형식을 따른다.

```text
Refs: #123
Closes: #123
```

## 6. 커밋 구성

- 코드와 그 코드에 직접 필요한 테스트·문서는 같은 논리적 커밋에 포함할 수
  있다.
- 무관한 포맷 변경, 파일 이동과 기능 변경을 한 커밋에 섞지 않는다.
- 비밀키, 개인정보, 생성된 런타임 데이터와 임시 파일을 커밋하지 않는다.
- 커밋 전 staged diff와 포함 파일을 확인한다.

```powershell
git status --short
git diff --cached
```

문서 갱신 여부는 [문서화 정책](documentation_policy.md), PR 검증 기준은
[코드 리뷰 정책](code_review.md)을 따른다.
