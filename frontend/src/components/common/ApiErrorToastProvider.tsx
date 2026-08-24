import {
  useCallback,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from 'react';
import ApiErrorToast from '@/components/common/ApiErrorToast';
import {
  ApiErrorToastContext,
  type ApiErrorToastContextValue,
} from '@/context/ApiErrorToastContext';
import type { ActiveApiErrorToast } from '@/types/apiErrorToast';
import { API_ERROR_TOAST_DEDUPE_MS } from '@/utils/adminApiErrorToast';

function createToastId(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function ApiErrorToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ActiveApiErrorToast | null>(null);
  const lastShownAtRef = useRef<Map<string, number>>(new Map());

  const dismissToast = useCallback(() => {
    setToast(null);
  }, []);

  const showToast = useCallback<
    ApiErrorToastContextValue['showToast']
  >((presentation, options = {}) => {
    const now = Date.now();
    const lastShownAt = lastShownAtRef.current.get(presentation.dedupeKey);

    if (
      lastShownAt !== undefined &&
      now - lastShownAt < API_ERROR_TOAST_DEDUPE_MS
    ) {
      return;
    }

    lastShownAtRef.current.set(presentation.dedupeKey, now);
    setToast({
      ...presentation,
      id: createToastId(),
      onRetry: options.onRetry,
    });
  }, []);

  const value = useMemo(
    () => ({
      showToast,
      dismissToast,
    }),
    [dismissToast, showToast],
  );

  return (
    <ApiErrorToastContext.Provider value={value}>
      {children}
      {toast ? (
        <div className="api-error-toast-host" aria-label="API 오류 알림">
          <ApiErrorToast toast={toast} onDismiss={dismissToast} />
        </div>
      ) : null}
    </ApiErrorToastContext.Provider>
  );
}
