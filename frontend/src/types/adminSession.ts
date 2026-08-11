/**
 * Admin PIN session API contract (Frontend 03 / FE3-00).
 *
 * Aligns with Backend 04 `POST /api/v1/admin/session`
 * (docs/api/admin_access.md on `feature/backend/collection-run-admin-api`).
 *
 * Security: PIN and access_token must never appear in URL query strings or logs.
 */

export const ADMIN_SESSION_ENDPOINT = {
  method: 'POST' as const,
  path: '/api/v1/admin/session',
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
