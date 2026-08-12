import { useContext } from 'react';
import { ApiErrorToastContext } from '@/context/ApiErrorToastContext';

export function useApiErrorToast() {
  const context = useContext(ApiErrorToastContext);

  if (context === null) {
    throw new Error('useApiErrorToast must be used within ApiErrorToastProvider');
  }

  return context;
}
