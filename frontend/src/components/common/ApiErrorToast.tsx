import Button from '@/components/common/Button';
import type { ActiveApiErrorToast } from '@/types/apiErrorToast';

interface ApiErrorToastProps {
  toast: ActiveApiErrorToast;
  onDismiss: () => void;
}

export default function ApiErrorToast({ toast, onDismiss }: ApiErrorToastProps) {
  return (
    <div
      className={`api-error-toast api-error-toast--${toast.kind}`}
      role={toast.kind === 'error' ? 'alert' : 'status'}
      aria-live="polite"
      aria-atomic="true"
    >
      <p className="api-error-toast__message">{toast.message}</p>
      <div className="api-error-toast__actions">
        {toast.retryable && toast.onRetry ? (
          <Button
            type="button"
            variant="secondary"
            className="api-error-toast__retry"
            onClick={() => {
              toast.onRetry?.();
              onDismiss();
            }}
          >
            다시 시도
          </Button>
        ) : null}
        <button
          type="button"
          className="api-error-toast__dismiss"
          aria-label="알림 닫기"
          onClick={onDismiss}
        >
          닫기
        </button>
      </div>
    </div>
  );
}
