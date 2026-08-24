import { useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';
import { useOptionalApiErrorToast } from '@/hooks/useOptionalApiErrorToast';
import { mapAdminApiErrorToToast } from '@/utils/adminApiErrorToast';
import { clearAdminSession } from '@/utils/adminSessionStorage';

interface UseAdminUnauthorizedRedirectOptions {
  error: unknown;
  onRetry?: () => void;
}

/**
 * Shows admin API error Toast and redirects to login on 401 (W4-F9 session UX).
 */
export function useAdminUnauthorizedRedirect({
  error,
  onRetry,
}: UseAdminUnauthorizedRedirectOptions) {
  const navigate = useNavigate();
  const { logout } = useAdminSession();
  const toastContext = useOptionalApiErrorToast();

  const redirectToLogin = useCallback(() => {
    clearAdminSession();
    logout();
    navigate(ADMIN_APP_ROUTES.login, { replace: true });
  }, [logout, navigate]);

  useEffect(() => {
    if (!(error instanceof AdminApiError)) {
      return;
    }

    toastContext?.showToast(mapAdminApiErrorToToast(error), {
      onRetry: error.status >= 500 ? onRetry : undefined,
    });

    if (error.status === 401) {
      redirectToLogin();
    }
  }, [error, onRetry, redirectToLogin, toastContext]);

  return { redirectToLogin };
}
