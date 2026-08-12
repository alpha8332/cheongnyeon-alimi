import { useContext } from 'react';
import { ApiErrorToastContext } from '@/context/ApiErrorToastContext';

/** Returns null when rendered outside ApiErrorToastProvider (non-throwing). */
export function useOptionalApiErrorToast() {
  return useContext(ApiErrorToastContext);
}
