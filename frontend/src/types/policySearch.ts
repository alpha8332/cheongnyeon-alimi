/**
 * Gate G1 approved Policy Search API contract types (Frontend 04).
 *
 * Aligns with Backend 06 W3-B0 `GET /api/v1/policies/search`.
 *
 * Fixed consumption constraints:
 * - Frontend sends raw Korean `q` (trimmed, required); no Frontend NL parser.
 * - Flat query params only on the wire; no nested `structured` object.
 * - Explicit flat filters override the same dimension interpreted from `q`.
 * - Region·age·status·category verdicts: match | mismatch | unknown | null (Backend sole authority).
 * - Invalid policies are never public.
 * - Existing GET /api/v1/policies list/detail unchanged until search API ships.
 */

import type {
  ApplicationStatus,
  PolicyCategory,
  PolicyDto,
  PolicySort,
} from './policy.js';

/** Backend evaluation verdict for a searchable dimension. Aligns with Backend `MatchVerdict`. */
export type MatchVerdict = 'match' | 'mismatch' | 'unknown';

/** Dimension key for NL interpretation and per-policy verdicts. */
export type InterpretedConditionDimension =
  | 'keyword'
  | 'region'
  | 'age'
  | 'category'
  | 'status';

/** Whether a condition came from natural-language `q` or an explicit flat filter. */
export type InterpretedConditionSource = 'q' | 'explicit';

/** Backend resolution for a parsed condition dimension. */
export type InterpretedConditionResolution = 'resolved' | 'unmapped' | 'ambiguous';

/**
 * Resolved value for one interpreted condition.
 * Shape depends on `dimension` (keyword/region string, age number, category/status enum).
 */
export type InterpretedConditionValue =
  | string
  | number
  | PolicyCategory
  | ApplicationStatus;

/** One row in response `interpreted_conditions.conditions`. */
export interface InterpretedCondition {
  dimension: InterpretedConditionDimension;
  value: InterpretedConditionValue;
  source: InterpretedConditionSource;
  resolution: InterpretedConditionResolution;
  /** Candidate strings when resolution is `ambiguous` (e.g. region alias matches). */
  candidates: string[];
}

/** Top-level NL interpretation block on {@link PolicySearchResponse}. */
export interface PolicySearchInterpretedConditions {
  q_raw: string;
  q_clean: string;
  conditions: InterpretedCondition[];
  /** Dimensions where explicit flat params overrode `q` interpretation. */
  override_fields: InterpretedConditionDimension[];
  /** Tokens from `q` that could not be mapped to a searchable dimension. */
  uninterpreted_terms: string[];
}

/**
 * Per-policy dimension verdicts returned by Backend search evaluation.
 * `null` = condition not applied to this search; `unknown` = applied but no policy evidence.
 */
export interface DimensionVerdicts {
  region: MatchVerdict | null;
  age: MatchVerdict | null;
  status: MatchVerdict | null;
  category: MatchVerdict | null;
}

/**
 * Machine-readable reason code from Backend evaluation.
 * Extensible string — unknown codes must not break UI (see Forest plan § Reason fallback).
 */
export type ReasonCode = string;

/** Per-row dimension still unconfirmed for this policy (not guessed as match). */
export interface UnconfirmedCondition {
  field: string;
  reason_code: ReasonCode;
  message: string;
}

/**
 * GET /api/v1/policies/search flat query parameters.
 * Mirrors Backend Pydantic request model field names, nullability, and defaults.
 */
export interface PolicySearchQueryParams {
  /** Natural-language query. Required after trim; empty → 422. Max 200 chars. */
  q: string;
  /** Optional keyword text filter. Max 100 chars. */
  keyword?: string | null;
  /** Administrative region alias or canonical name string. Max 100 chars. */
  region?: string | null;
  age?: number | null;
  category?: PolicyCategory | null;
  status?: ApplicationStatus | null;
  /** Default `true` when omitted (Backend and Frontend URL state). */
  include_partial?: boolean;
  page?: number;
  limit?: number;
  sort?: PolicySort;
  /** Browser-only profile preferences sent in a POST body, never as URL filters. */
  preferences?: PolicySearchPreferences | null;
}

export interface PolicySearchPreferences {
  region?: string | null;
  age?: number | null;
  categories: PolicyCategory[];
}

/** Backend defaults — keep in sync with Backend 06 W3-B0. */
export const POLICY_SEARCH_DEFAULTS = {
  include_partial: true,
  page: 1,
  limit: 20,
  sort: 'default',
} as const;

/** Recommended query string length limits (422 when exceeded). */
export const POLICY_SEARCH_QUERY_LIMITS = {
  q: 200,
  keyword: 100,
  region: 100,
} as const;

/**
 * One ranked search hit: nested PolicyRead (`PolicyDto`) plus search metadata.
 * Matches Backend nested DTO — not a flat merge of PolicyRead fields.
 *
 * `score` is for Backend ordering only — Release 1 UI does not display it as a number
 * and must not compare scores across different search requests.
 */
export interface PolicySearchHit {
  policy: PolicyDto;
  score: number;
  verdicts: DimensionVerdicts;
  /** Number of applied verdict dimensions whose result is `unknown`. */
  unknown_count: number;
  reason_codes: ReasonCode[];
  message: string;
  unconfirmed_conditions: UnconfirmedCondition[];
}

/** Search response envelope. Pagination matches PolicyListResponse shape. */
export interface PolicySearchResponse {
  total: number;
  page: number;
  limit: number;
  interpreted_conditions: PolicySearchInterpretedConditions;
  items: PolicySearchHit[];
}

/** Approved search endpoint (G1 integration). */
export const POLICY_SEARCH_ENDPOINT = {
  method: 'GET' as const,
  preferenceMethod: 'POST' as const,
  path: '/api/v1/policies/search' as const,
};
