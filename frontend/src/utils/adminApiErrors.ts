import type {
  AdminDetailErrorBody,
  AdminStructuredErrorBody,
} from '../types/adminSession.js';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}

/** Parse Backend admin error JSON without logging credential fields. */
export function parseAdminApiErrorDetail(
  data: unknown,
  fallback = 'Admin API request failed.',
): string {
  if (!isRecord(data)) {
    return fallback;
  }

  if (typeof data.detail === 'string' && data.detail.length > 0) {
    return data.detail;
  }

  if (isRecord(data.error) && typeof data.error.message === 'string') {
    return data.error.message;
  }

  return fallback;
}

export function isAdminStructuredErrorBody(
  data: unknown,
): data is AdminStructuredErrorBody {
  return (
    isRecord(data) &&
    isRecord(data.error) &&
    typeof data.error.message === 'string'
  );
}

export function isAdminDetailErrorBody(data: unknown): data is AdminDetailErrorBody {
  return isRecord(data) && typeof data.detail === 'string';
}
