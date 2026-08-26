# 관리자 인증과 보안

## 기능 목적

로컬 Docker 서비스의 운영 화면을 일반 사용자 화면과 분리하고, 비밀정보를
브라우저 URL·영구 저장소·로그에 남기지 않으면서 한 명의 관리자가 접근하게 한다.

## 사용하는 화면과 도구

| 기능 | 위치 |
| --- | --- |
| 관리자 로그인 | `/admin/login` |
| 관리자 보호 route | `/admin/*` |
| PIN 변경 | `/admin/security` |
| 로그아웃 | 관리자 navigation |
| 분실 PIN 복구 | 저장소 루트 `reset_admin_pin.bat` |

## 최초 PIN 설정

`run_docker.bat` 최초 실행은 숫자 4자리 관리자 PIN을 보안 입력으로 받는다.
PIN 평문을 `.env.compose`, 명령행 인자, shell history와 로그에 기록하지 않고
salted PBKDF2 verifier만 초기 관리자 설정에 사용한다.

개발 Mock에서 사용하는 예시 PIN과 실제 Docker 최초 실행 PIN은 같은 개념이
아니다. 실제 환경에서는 최초 실행자가 입력한 PIN을 사용한다.

## 로그인 원리

```text
4자리 PIN form
→ HTTPS가 아닌 로컬 loopback Backend POST body
→ DB의 salted verifier와 constant-time 비교
→ 성공 시 짧은 수명의 서명 token
→ 브라우저 메모리 session
```

PIN은 URL query에 넣지 않는다. Backend는 평문 PIN을 저장하거나 성공·실패 로그에
복사하지 않는다.

성공 token에는 관리자 역할, 만료 시각과 session generation이 결합된다. 서명과
현재 generation이 모두 일치해야 보호 API를 사용할 수 있다.

## 보호 route 원리

Frontend의 `/admin` 하위 route는 관리자 session이 없으면 로그인 화면으로
이동한다. Backend는 각 관리자 API에서 공통 인증 dependency를 다시 적용하므로
Frontend route를 우회해 API URL을 직접 호출해도 인증 없이 데이터가 노출되지
않는다.

| 응답 | 의미 |
| --- | --- |
| `401` | token 누락, 위조, 만료 또는 session generation 불일치 |
| `403` | 유효한 token이지만 관리자 역할 부족 |
| `429` | 반복 로그인 실패로 현재 잠금 시간 적용 |
| `422` | PIN 형식 등 요청 검증 실패 |

Frontend는 `401`을 받으면 메모리 session을 지우고 로그인 화면으로 이동한다.

## 로그인 실패와 잠금

반복 대입을 줄이기 위해 실패 횟수에 따라 점진적 잠금 시간을 적용한다. 잠금 중
요청은 남은 시간을 포함한 제한 응답을 반환하며, 사용자에게 서버 오류가 아니라
잠금 상태임을 안내한다.

성공 로그인은 실패 상태를 초기화한다. 오류 응답과 구조화 로그에는 실제 PIN,
verifier, token과 요청 body를 포함하지 않는다.

## 세션 저장과 만료

관리자 access token은 브라우저 메모리에만 둔다.

- `localStorage`, URL과 영구 cookie에 저장하지 않는다.
- 명시적 로그아웃에서 즉시 제거한다.
- 만료된 token은 Backend가 거부하고 Frontend도 세션을 정리한다.
- 전체 페이지 새로고침은 메모리 상태를 잃어 재로그인이 필요할 수 있다.
- PIN 변경·복구는 session generation을 올려 기존 token을 모두 무효화한다.

이 선택은 편의성보다 로컬 브라우저에 관리자 권한을 장기간 남기지 않는 것을
우선한다.

## PIN 변경 원리

현재 PIN을 알고 있으면 `/admin/security`에서 다음 값을 입력한다.

1. 현재 PIN
2. 새 PIN
3. 새 PIN 확인

Backend는 현재 verifier를 확인하고 새 verifier와 session generation 변경을 하나의
DB transaction으로 처리한다. 성공 전에는 기존 verifier를 바꾸지 않는다.
성공하면 현재 브라우저를 포함한 모든 기존 관리자 token이 무효가 되고 로그인
화면으로 이동한다.

PIN 변경 form은 각 값이 숫자 4자리인지, 새 PIN과 확인이 일치하는지 먼저
검증한다. PIN을 화면 메시지나 로그에 다시 출력하지 않는다.

## 분실 PIN 복구 원리

현재 PIN을 모르면 관리자 화면 안에서 본인 확인을 우회하지 않는다. 서버 PC의
저장소와 실행 중인 Docker 환경에 접근할 수 있는 운영자만 다음 명령을 실행한다.

```powershell
.\reset_admin_pin.bat
```

복구 절차는 다음 경계를 사용한다.

- host의 `Read-Host -AsSecureString`으로 새 PIN과 확인 입력
- 명령 인자가 아닌 container 표준입력으로 전달
- Backend CLI가 길이·숫자·확인 일치 재검증
- 관리자 인증 singleton row만 transaction 갱신
- session generation 증가로 기존 token 전부 무효화

Windows PowerShell 5.1이 native pipeline 시작에 UTF-8 BOM을 붙이는 환경을 위해
Backend CLI는 첫 입력 앞의 BOM 하나만 제거한다. 임의의 공백이나 다른 문자는
제거하지 않으므로 기존 숫자 4자리 검증은 유지된다.

## DB 보존 원리

PIN 변경과 분실 복구는 다음 데이터를 삭제하거나 다시 적재하지 않는다.

- 공개 정책과 활성 dataset installation·membership
- 로컬 수집 정책
- CollectionRun 감사 기록
- 정책을 참조하는 데이터
- PostgreSQL Docker Volume

`docker compose down -v`는 DB Volume을 제거하는 별도 파괴적 작업이므로 PIN
복구 수단으로 사용하지 않는다.

## 비밀정보 경계

화면·API·로그·문서에 다음 값을 노출하지 않는다.

- PIN 평문
- PIN verifier와 salt
- 관리자 token과 서명 secret
- DB 비밀번호
- API key

관리자 session API는 필요한 안전한 만료 정보만 응답한다. 운영자가 문제를
보고할 때도 실제 PIN이나 token을 screenshot·Issue·commit에 포함하지 않는다.

## 오류와 복구

- PIN이 기억나지만 로그인이 실패하면 최초 실행에서 설정한 PIN인지 확인한다.
- 잠금 상태이면 안내된 시간이 지난 뒤 다시 시도한다.
- PIN을 잊었으면 `reset_admin_pin.bat`을 사용한다.
- `.env.compose`가 없거나 Backend가 실행 중이 아니면 복구 script가 fail-closed로
  중단한다.
- 복구 명령 실패 시 새 verifier를 부분 저장하지 않는다.

## 현재 제한사항

- 다중 관리자 계정과 역할별 권한은 제공하지 않는다.
- 이메일·휴대전화 기반 원격 복구가 없다.
- PIN은 로컬 운영 편의를 위한 4자리 비밀이며 인터넷 공개 관리 콘솔용 인증
  체계를 대신하지 않는다.
- 브라우저 새로고침 뒤 자동 재로그인을 위한 영구 token 저장을 제공하지 않는다.

## 관련 계약

- [관리자 인증 API](../../api/admin_access.md)
- [Windows Docker 최초 실행과 PIN 복구](../../operations/docker_first_run.md)
- [브라우저 사용자 데이터 경계](favorites_calendar_notifications.md)
