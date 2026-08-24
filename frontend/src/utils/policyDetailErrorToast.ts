import { PolicyDetailApiError } from '../api/policyDetailApiError.js';
import type { ApiErrorToastPresentation } from '../types/apiErrorToast.js';

export function buildPolicyDetailErrorToastDedupeKey(
  status: number,
  detail: string,
): string {
  return `policy-detail-${status}-${detail.trim().slice(0, 64)}`;
}

export function mapPolicyDetailErrorToToast(
  error: PolicyDetailApiError,
): ApiErrorToastPresentation {
  const dedupeKey = buildPolicyDetailErrorToastDedupeKey(
    error.status,
    error.detail,
  );

  if (error.status === 422) {
    return {
      message: error.detail,
      kind: 'warning',
      retryable: false,
      dedupeKey,
    };
  }

  if (error.status >= 500) {
    return {
      message:
        error.detail ||
        '핵심 신청 조건을 다시 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.',
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

export function isPolicyDetailApiError(error: unknown): error is PolicyDetailApiError {
  return error instanceof PolicyDetailApiError;
}
