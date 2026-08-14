import { createContext } from 'react';
import type { ApiErrorToastPresentation } from '@/types/apiErrorToast';

export interface ShowApiErrorToastOptions {
  onRetry?: () => void;
}

export interface ApiErrorToastContextValue {
  showToast: (
    presentation: ApiErrorToastPresentation,
    options?: ShowApiErrorToastOptions,
  ) => void;
  dismissToast: () => void;
}

export const ApiErrorToastContext =
  createContext<ApiErrorToastContextValue | null>(null);
