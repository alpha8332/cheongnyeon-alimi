/**
 * W3-F0 DRAFT — Gate G1 aligned with Backend 06 PolicySearch contract (pending approval).
 *
 * Do not import from production code until Team Leader records `G1_APPROVED`.
 *
 * Fixed handoff constraints:
 * - Frontend sends raw Korean `q` (trimmed, required); no Frontend NL parser.
 * - Flat query params only on the wire; no nested `structured` object.
 * - Region·age·status verdicts: match | mismatch | unknown (Backend sole authority).
 * - Invalid policies are never public.
 * - Existing GET /api/v1/policies list/detail unchanged until search API ships.
 */

import type { ApplicationStatus, PolicyCategory, PolicyDto } from '@/types/policy';

/** Backend evaluation verdict for a searchable dimension. Aligns with Backend `MatchVerdict`. */
export type MatchVerdict = 'match' | 'mismatch' | 'unknown';

/** Per-policy dimension verdicts returned by Backend search evaluation. */
export interface DimensionVerdicts {
  region: MatchVerdict;
  age: MatchVerdict;
  status: MatchVerdict;
}

/**
 * Machine-readable search reason code from Backend evaluation.
 * Closed enum list — sync with Backend 06 W3-B0 on G1 approval.
 */
export type ReasonCode = string;

/**
 * GET /api/v1/policies/search flat query parameters.
 * Mirrors Backend Pydantic request model field names, nullability, and defaults.
 */
export interface PolicySearchQueryParams {
  /** Natural-language query. Required after trim; empty → 422. */
  q: string;
  keyword?: string | null;
  region?: string | null;
  age?: number | null;
  category?: PolicyCategory | null;
  status?: ApplicationStatus | null;
  /** Default `true` when omitted (Backend and Frontend URL state). */
  include_partial?: boolean;
  page?: number;
  limit?: number;
}

/** Backend defaults — keep in sync with Backend 06 W3-B0. */
export const POLICY_SEARCH_DEFAULTS = {
  include_partial: true,
  page: 1,
  limit: 20,
} as const;

/**
 * One ranked search hit: nested PolicyRead (`PolicyDto`) plus search metadata.
 * Matches Backend nested DTO — not a flat merge of PolicyRead fields.
 */
export interface PolicySearchHit {
  policy: PolicyDto;
  score: number;
  verdicts: DimensionVerdicts;
  reason_codes: ReasonCode[];
  message: string;
  /** Dimensions still unconfirmed for this policy row (not guessed as match). */
  unconfirmed_conditions: string[];
}

/** Search response envelope. Pagination matches PolicyListResponse shape. */
export interface PolicySearchResponse {
  total: number;
  page: number;
  limit: number;
  items: PolicySearchHit[];
}

/** Approved search endpoint (G1 integration). */
export const POLICY_SEARCH_ENDPOINT = {
  method: 'GET' as const,
  path: '/api/v1/policies/search' as const,
};
