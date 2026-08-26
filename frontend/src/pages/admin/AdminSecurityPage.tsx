import { useId, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router';
import { changeAdminPin } from '@/api/adminSession';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { AdminApiError } from '@/api/adminApiError';
import Button from '@/components/common/Button';
import { useAdminSession } from '@/hooks/useAdminSession';

function normalizePin(value: string): string {
  return value.replace(/\D/g, '').slice(0, 4);
}

export default function AdminSecurityPage() {
  const formId = useId();
  const currentPinId = useId();
  const newPinId = useId();
  const confirmationId = useId();
  const navigate = useNavigate();
  const { accessToken, logout } = useAdminSession();
  const [currentPin, setCurrentPin] = useState('');
  const [newPin, setNewPin] = useState('');
  const [confirmation, setConfirmation] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);

    if (![currentPin, newPin, confirmation].every((pin) => /^\d{4}$/.test(pin))) {
      setErrorMessage('모든 PIN을 숫자 4자리로 입력해 주세요.');
      return;
    }
    if (newPin !== confirmation) {
      setErrorMessage('새 PIN과 확인 PIN이 일치하지 않습니다.');
      return;
    }
    if (currentPin === newPin) {
      setErrorMessage('새 PIN은 현재 PIN과 달라야 합니다.');
      return;
    }

    setIsSubmitting(true);
    try {
      await changeAdminPin(
        { current_pin: currentPin, new_pin: newPin },
        accessToken,
      );
      setCurrentPin('');
      setNewPin('');
      setConfirmation('');
      logout();
      navigate(ADMIN_APP_ROUTES.login, {
        replace: true,
        state: { pinChanged: true },
      });
    } catch (error) {
      if (error instanceof AdminApiError) {
        if (error.status === 401) {
          setErrorMessage(
            error.detail.includes('session')
              ? '관리자 세션이 만료되었습니다. 다시 로그인해 주세요.'
              : '현재 PIN이 올바르지 않습니다.',
          );
        } else if (error.status === 409) {
          setErrorMessage('새 PIN은 현재 PIN과 달라야 합니다.');
        } else {
          setErrorMessage('PIN을 변경하지 못했습니다. 잠시 후 다시 시도해 주세요.');
        }
      } else {
        setErrorMessage('PIN을 변경하지 못했습니다. 잠시 후 다시 시도해 주세요.');
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const errorId = `${formId}-error`;

  return (
    <section className="admin-security-page" aria-labelledby="admin-security-title">
      <header className="greeting">
        <h2 id="admin-security-title" className="greeting__title">관리자 보안</h2>
        <p className="greeting__subtitle">
          PIN을 변경하면 현재 브라우저를 포함한 기존 관리자 세션이 모두 종료됩니다.
        </p>
      </header>

      <div className="admin-security-page__card">
        <form
          id={formId}
          className="admin-login-form"
          onSubmit={(event) => void handleSubmit(event)}
          aria-label="관리자 PIN 변경"
        >
          <label className="admin-login-form__field" htmlFor={currentPinId}>
            <span className="admin-login-form__label">현재 PIN</span>
            <input
              id={currentPinId}
              className="admin-login-form__input"
              type="password"
              inputMode="numeric"
              autoComplete="current-password"
              pattern="[0-9]{4}"
              maxLength={4}
              value={currentPin}
              onChange={(event) => setCurrentPin(normalizePin(event.target.value))}
              disabled={isSubmitting}
              aria-describedby={errorMessage ? errorId : undefined}
            />
          </label>

          <label className="admin-login-form__field" htmlFor={newPinId}>
            <span className="admin-login-form__label">새 PIN</span>
            <input
              id={newPinId}
              className="admin-login-form__input"
              type="password"
              inputMode="numeric"
              autoComplete="new-password"
              pattern="[0-9]{4}"
              maxLength={4}
              value={newPin}
              onChange={(event) => setNewPin(normalizePin(event.target.value))}
              disabled={isSubmitting}
              aria-describedby={errorMessage ? errorId : undefined}
            />
          </label>

          <label className="admin-login-form__field" htmlFor={confirmationId}>
            <span className="admin-login-form__label">새 PIN 확인</span>
            <input
              id={confirmationId}
              className="admin-login-form__input"
              type="password"
              inputMode="numeric"
              autoComplete="new-password"
              pattern="[0-9]{4}"
              maxLength={4}
              value={confirmation}
              onChange={(event) => setConfirmation(normalizePin(event.target.value))}
              disabled={isSubmitting}
              aria-describedby={errorMessage ? errorId : undefined}
            />
          </label>

          {errorMessage ? (
            <p id={errorId} className="admin-login-form__error" role="alert">
              {errorMessage}
            </p>
          ) : null}

          <div className="admin-login-form__actions">
            <Button
              type="submit"
              disabled={
                isSubmitting ||
                currentPin.length !== 4 ||
                newPin.length !== 4 ||
                confirmation.length !== 4
              }
            >
              {isSubmitting ? '변경 중…' : 'PIN 변경'}
            </Button>
          </div>
        </form>

        <p className="hint-text" role="note">
          PIN을 잊은 경우 서버 PC의 저장소 루트에서{' '}
          <code>reset_admin_pin.bat</code>을 실행하면 정책 DB와 CollectionRun을
          보존한 채 복구할 수 있습니다.
        </p>
      </div>
    </section>
  );
}
