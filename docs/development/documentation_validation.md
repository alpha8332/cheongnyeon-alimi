# 문서 품질 검증

## 목적

공개 문서의 필수 색인, 로컬 링크, 프로젝트명, 비밀정보 pattern과 빈 파일·
디렉터리를 자동 검사한다. 완료된 계획 문서의 형식 검사는 제출본 정리와 함께
제거했으며 현재 계약 문서의 탐색성과 공개 안전성에 집중한다.

## 실행

저장소 루트에서 실행한다.

```powershell
.\.venv\Scripts\python.exe scripts/validate_docs.py
```

또는 PATH의 Python을 사용할 수 있다.

```powershell
python scripts/validate_docs.py
```

## 검사 항목

- README, CHANGELOG와 영역별 안내 문서 존재
- Markdown 상대 링크 대상 존재
- 이전 프로젝트명 재유입
- API key·secret·password 형태의 의심스러운 실제 값
- 빈 문서와 빈 디렉터리

외부 URL의 현재 HTTP 상태와 문서 내용의 사실성은 자동으로 확정하지 않는다.
Compose, Route, Schema, Migration과 실제 실행 결과를 별도로 대조해야 한다.

## 실패 처리

검사가 실패하면 오류가 가리키는 파일을 수정한 뒤 다시 실행한다. 비밀정보
의심 값은 단순 allowlist로 숨기기 전에 실제 공개 가능한 placeholder인지
확인한다. 문서를 삭제했으면 해당 문서를 가리키는 모든 색인과 관련 문서 링크를
현재 권위 문서로 교체한다.

검증기 자체를 변경하면 다음 테스트를 실행한다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_validate_docs.py -q
```
