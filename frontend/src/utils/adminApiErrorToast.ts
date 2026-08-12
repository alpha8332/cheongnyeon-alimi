import { AdminApiError } from '../api/adminApiError.js';
import type { ApiErrorToastPresentation } from '../types/apiErrorToast.js';

export const API_ERROR_TOAST_DEDUPE_MS = 3_000;

export function buildAdminApiErrorToastDedupeKey(
  status: number,
  detail: string,
): string {
  return `admin-api-${status}-${detail.trim().slice(0, 64)}`;
}

export function mapAdminApiErrorToToast(
  error: AdminApiError,
): ApiErrorToastPresentation {
  const dedupeKey = buildAdminApiErrorToastDedupeKey(error.status, error.detail);

  if (error.status === 401) {
    return {
      message: '세션이 만료되었습니다. 다시 로그인해 주세요.',
      kind: 'warning',
      retryable: false,
      dedupeKey,
    };
  }

  if (error.status === 403) {
    return {
      message: error.detail || '관리자 권한이 없습니다.',
      kind: 'error',
      retryable: false,
      dedupeKey,
    };
  }

  if (error.status === 409 || error.status === 422) {
    return {
      message: error.detail,
      kind: 'warning',
      retryable: false,
      dedupeKey,
    };
  }

  if (error.status === 429) {
    return {
      message:
        error.detail || '요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.',
      kind: 'warning',
      retryable: false,
      dedupeKey,
    };
  }

  if (error.status >= 500) {
    return {
      message: error.detail || '서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.',
      kind: 'error',
      retryable: true,
      dedupeKey,
    };
  }

  return {
    message: error.detail,
    kind: 'error',
    retryable: false,
    dedupeKey,
  };
}
