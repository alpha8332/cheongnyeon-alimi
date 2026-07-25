# 문서 품질 검증

## 목적

문서 구조, 링크와 Forest 기록 규칙이 변경 과정에서 조용히 깨지는 것을
방지한다. 검증기는 Python 표준 라이브러리만 사용하며 외부 서비스나
네트워크를 호출하지 않는다.

## 실행

저장소 루트에서 실행한다.

```powershell
python scripts/validate_docs.py
```

성공:

```text
Documentation validation passed.
```

실패하면 오류 목록을 출력하고 종료 코드 `1`을 반환한다.

## 검사 항목

- 필수 프로젝트 문서 존재 여부
- Markdown 로컬 상대 링크의 대상 존재 여부
- 이전 저장소명 사용 여부
- 문서에 실제 비밀값으로 보이는 할당이 있는지 여부
- `docs/` 내부의 빈 파일과 빈 디렉터리
- 담당 영역별 번호가 있는 Forest 계획과 구현 단계 개발 기록의 대응
- Forest 계획과 개발 기록의 필수 섹션
- 허용된 Forest 상태값
- 완료된 Forest에 미완료 Slice가 남아 있는지 여부

HTTP 링크의 실제 접속 가능 여부와 Markdown 문법 전체 lint는 현재 검사하지
않는다. 네트워크 의존 검사와 외부 linter는 필요성과 실행 안정성을 검토한
뒤 추가한다.

## 검사 범위

다음을 검사한다.

- 루트 `README.md`
- 루트 `CHANGELOG.md`
- `docs/**/*.md`

`opensource_plan/`은 원본 Word 계획과 참고 자료를 보존하는 읽기 전용
영역이므로 검사 대상에서 제외한다.

## Forest 문서 규칙

공통 계획 또는 담당 영역별 계획 파일은 다음 형식을 사용한다.

```text
docs/development/develop_plan/NN_forest_name.md
docs/development/develop_plan/<owner>/NN_forest_name.md
```

`draft`와 `approved` 계획은 개발 기록을 요구하지 않는다. 구현을 시작해
`in-progress`가 되면 계획과 같은 담당 영역에 같은 Forest 이름의 개발 기록을
생성한다.

```text
docs/development/development_notes/forest_name.md
docs/development/development_notes/<owner>/forest_name.md
```

예:

```text
integration/01_docs_system.md ↔ integration/docs_system.md
```

Forest가 `completed` 상태라면 계획과 기록에 `pending` 또는 `in-progress`
Slice가 남아 있으면 안 된다.

## 테스트

```powershell
python -m unittest discover -s tests -p "test_*.py" -v
```

테스트는 임시 디렉터리에서 깨진 링크, 이전 저장소명, 비밀값과 Forest
계획·기록 대응을 검증한다. 임시 디렉터리는 테스트 종료 후 자동으로
삭제된다.

## 규칙 변경

검사 규칙을 변경할 때는 다음을 함께 수정한다.

- `scripts/validate_docs.py`
- `tests/test_validate_docs.py`
- 이 문서
- 영향을 받는 Forest 계획과 개발 기록

새 검사는 실제 저장소 문서에서 오탐 없이 통과하는지 확인한다. 실행하지 않은
검증은 개발 기록에 통과로 표시하지 않는다.

## CI 연동

검증기는 종료 코드로 성공과 실패를 구분하므로 GitHub Actions에서 그대로
실행할 수 있다. CI Workflow 추가는 배포·CI 설정 작업에서 현재 브랜치 정책과
필수 Python 버전을 함께 검토한 후 진행한다.
