# 보안 정책

## 지원 범위

보안 수정은 최신 GitHub Release를 우선한다. 이전 버전에서 문제가 발견되면
최신 버전에서도 재현되는지 함께 알려 주세요.

## 취약점 비공개 제보

취약점은 공개 Issue, Discussion 또는 Pull Request에 상세 내용을 올리지 말고,
저장소에서 비공개 제보 기능을 제공할 때 **Security → Report a vulnerability**를
사용해 주세요.

- 제보 경로: <https://github.com/alpha8332/cheongnyeon-alimi/security/advisories/new>
- 포함할 내용: 영향받는 버전, 재현 절차, 예상 영향과 가능한 완화 방법
- 제외할 내용: 실제 API key, 관리자 PIN, token, DB 비밀번호, 개인정보와 Raw
  정책 payload

비밀정보가 노출됐다면 제보문에 값을 복사하지 말고 즉시 해당 credential을
폐기·재발급한 뒤, 어떤 종류의 credential이 노출됐는지만 알려 주세요.

비공개 제보 메뉴가 보이지 않으면 공개 Issue에는 취약점 상세나 재현 코드를
쓰지 말고, "비공개 보안 연락 경로 요청"만 남겨 주세요. 관리자가 비공개 경로를
안내한 뒤 상세 내용을 전달해 주세요.

## 일반 오류와 기능 제안

보안상 비공개 처리가 필요하지 않은 오류와 기능 제안은 GitHub Issue를
사용할 수 있습니다. 로그를 첨부하기 전 API key, PIN, token, DB 접속정보와
개인정보가 제거됐는지 확인해 주세요.
