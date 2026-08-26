/**
 * Admin PIN session API contract.
 *
 * Aligns with docs/api/admin_access.md and `POST /api/v1/admin/session`.
 *
 * Security: PIN and access_token must never appear in URL query strings or logs.
 */

export const ADMIN_SESSION_ENDPOINT = {
  method: 'POST' as const,
  path: '/api/v1/admin/session',
};

export const ADMIN_PIN_ENDPOINT = {
  method: 'PUT' as const,
  path: '/api/v1/admin/pin',
};

export interface AdminSessionRequest {
  /** Exactly four numeric digits. Sent in JSON body only. */
  pin: string;
}

export interface AdminSessionResponse {
  access_token: string;
  token_type: 'bearer';
  /** Token lifetime in seconds. */
  expires_in: number;
  role: 'admin';
}

export interface AdminPinChangeRequest {
  current_pin: string;
  new_pin: string;
}

/** Session login failures (401/429) use nested `error.message`. */
export interface AdminStructuredErrorBody {
  error: {
    message: string;
    details?: Record<string, unknown>;
  };
}

/** Protected admin routes use FastAPI `detail` string errors (401/403/404). */
export interface AdminDetailErrorBody {
  detail: string;
}

export type AdminSessionErrorStatus = 401 | 403 | 422 | 429 | 503;
