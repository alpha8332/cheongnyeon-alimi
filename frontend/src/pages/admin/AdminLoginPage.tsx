import { useEffect, useId, useState, type FormEvent } from 'react';
import { Link, Navigate, useLocation, useNavigate } from 'react-router';
import Button from '@/components/common/Button';
import { createAdminSession } from '@/api/adminSession';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';
import {
  isValidAdminPinInput,
  mapAdminLoginError,
} from '@/utils/adminLoginPresentation';

interface LoginLocationState {
  from?: string;
}

export default function AdminLoginPage() {
  const formId = useId();
  const pinInputId = useId();
  const navigate = useNavigate();
  const location = useLocation();
  const { isAuthenticated, login } = useAdminSession();
  const redirectTarget =
    (location.state as LoginLocationState | null)?.from ??
    ADMIN_APP_ROUTES.dashboard;

  const [pin, setPin] = useState('');
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [cooldownUntilMs, setCooldownUntilMs] = useState<number | null>(null);
  const [nowMs, setNowMs] = useState(() => Date.now());

  useEffect(() => {
    if (cooldownUntilMs === null) {
      return;
    }

    const timer = window.setInterval(() => {
      setNowMs(Date.now());
    }, 250);

    return () => {
      window.clearInterval(timer);
    };
  }, [cooldownUntilMs]);

  if (isAuthenticated) {
    return <Navigate to={redirectTarget} replace />;
  }

  const isCooldownActive =
    cooldownUntilMs !== null && nowMs < cooldownUntilMs;
  const cooldownSecondsRemaining = isCooldownActive
    ? Math.ceil((cooldownUntilMs - nowMs) / 1000)
    : 0;

  const handleSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setErrorMessage(null);

    if (!isValidAdminPinInput(pin)) {
      setErrorMessage('PIN은 숫자 4자리여야 합니다.');
      return;
    }

    if (isCooldownActive) {
      return;
    }

    setIsSubmitting(true);

    try {
      const response = await createAdminSession({ pin });
      login(response);
      setPin('');
      navigate(redirectTarget, { replace: true });
    } catch (error) {
      const presentation = mapAdminLoginError(error);
      setErrorMessage(presentation.message);

      if (presentation.kind === 'cooldown' && presentation.cooldownMs) {
        setCooldownUntilMs(Date.now() + presentation.cooldownMs);
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="page admin-login-page">
      <header className="greeting">
        <h1 className="greeting__title">관리자 로그인</h1>
        <p className="greeting__subtitle">
          4자리 숫자 PIN으로 관리자 세션을 시작합니다.
        </p>
      </header>

      <p role="note" className="admin-login-page__notice">
        PIN과 access token은 URL·브라우저 로그·영구 localStorage에 저장하지
        않습니다. 세션은 브라우저 메모리에만 유지됩니다.
      </p>

      <form
        id={formId}
        className="admin-login-form"
        onSubmit={(event) => void handleSubmit(event)}
        aria-label="관리자 PIN 로그인"
      >
        <label className="admin-login-form__field" htmlFor={pinInputId}>
          <span className="admin-login-form__label">관리자 PIN (4자리)</span>
          <input
            id={pinInputId}
            className="admin-login-form__input"
            type="password"
            inputMode="numeric"
            autoComplete="one-time-code"
            pattern="[0-9]{4}"
            maxLength={4}
            value={pin}
            onChange={(event) =>
              setPin(event.target.value.replace(/\D/g, '').slice(0, 4))
            }
            disabled={isSubmitting || isCooldownActive}
            aria-describedby={errorMessage ? `${formId}-error` : undefined}
            aria-invalid={errorMessage ? true : undefined}
          />
        </label>

        {errorMessage ? (
          <p
            id={`${formId}-error`}
            className="admin-login-form__error"
            role="alert"
          >
            {errorMessage}
            {isCooldownActive
              ? ` (${cooldownSecondsRemaining}초 후 재시도 가능)`
              : null}
          </p>
        ) : null}

        <div className="admin-login-form__actions">
          <Button
            type="submit"
            disabled={isSubmitting || isCooldownActive || pin.length !== 4}
          >
            {isSubmitting ? '로그인 중…' : '로그인'}
          </Button>
        </div>
      </form>

      <p className="hint-text">
        Mock 환경 테스트 PIN: <code>0000</code> (429 cooldown 테스트:{' '}
        <code>4290</code>)
      </p>

      <p className="admin-login-page__back">
        <Link to="/">사용자 홈으로</Link>
      </p>
    </div>
  );
}
