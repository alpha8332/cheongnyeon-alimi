export type ApiErrorToastKind = 'info' | 'warning' | 'error';

export interface ApiErrorToastPresentation {
  message: string;
  kind: ApiErrorToastKind;
  retryable: boolean;
  dedupeKey: string;
}

export interface ActiveApiErrorToast extends ApiErrorToastPresentation {
  id: string;
  onRetry?: () => void;
}
