/**
 * W3-F0 DRAFT — NOT APPROVED (DT2 Gate G1 pending)
 *
 * Natural-language policy search API consumption types for Frontend 04.
 * Do not import from production code until Backend 06 and Data semantics
 * are jointly approved.
 *
 * Fixed handoff constraints reflected here:
 * - Frontend sends raw Korean `q`; no Frontend-only NL parser.
 * - Region·age·status use match|mismatch|unknown verdicts from Backend.
 * - Invalid policies are never public; partial inclusion is opt-in (TBD G1).
 * - Existing GET /api/v1/policies list/detail remains until search API ships.
 */

import type { ApplicationStatus, PolicyCategory, PolicyDto } from '@/types/policy';

/** Backend interpretation verdict for a structured dimension. */
export type PolicyMatchVerdict = 'match' | 'mismatch' | 'unknown';

/** G1-pending: final HTTP method/path — placeholder documents intent only. */
export type PolicySearchHttpMethod = 'GET' | 'POST';

/**
 * Structured filters the user may set explicitly or edit after Backend
 * interprets natural language. Names align with Backend 06 W3-B0 draft target;
 * rename only through G1.
 */
export interface PolicySearchStructuredFilters {
  /** Exact category enum token when user selects a chip. */
  category?: PolicyCategory;
  /** Canonical region name from administrative reference when confirmed. */
  region?: string;
  /** Inclusive age the user intends to match (integer 0–150). */
  age?: number;
  /** Application status filter when explicitly chosen. */
  status?: ApplicationStatus;
}

/**
 * Request draft. `q` is required for NL search; structured fields refine or
 * override interpreted conditions after user edit (exact merge rules: G1).
 */
export interface PolicySearchRequestDraft {
  /** Raw Korean natural-language query. Frontend must not tokenize or parse. */
  q: string;
  structured?: PolicySearchStructuredFilters;
  page?: number;
  limit?: number;
  /**
   * Include partial policies in ranked candidates when true.
   * Default and interaction with list API include_partial: G1 decision.
   */
  include_partial?: boolean;
  /**
   * When true, confirmed mismatches are excluded from results.
   * Unknown handling (include vs rank penalty): G1 decision.
   */
  exclude_confirmed_mismatch?: boolean;
}

/** One interpreted condition Backend derived from `q` or user edits. */
export interface PolicySearchInterpretedConditionDraft {
  /** Stable key for chip UI, e.g. region, age, status, category, keyword. */
  dimension: string;
  /** Human-readable label for chips, e.g. "지역: 서울특별시". */
  label: string;
  /** Structured value Backend will use for query (shape varies by dimension). */
  value: string | number | PolicyCategory | ApplicationStatus | null;
  /** Whether Backend treats this condition as confirmed, uncertain, or rejected. */
  verdict: PolicyMatchVerdict;
  /** True when the user edited this chip after the initial interpretation. */
  user_modified?: boolean;
}

/** Per-result explanation of why a policy appears and what remains unknown. */
export interface PolicySearchResultReasonDraft {
  /** Short UI string, e.g. "지역 일치", "연령 정보 미확인". */
  summary: string;
  /** Machine-readable codes aligned with Backend reason enum (G1). */
  codes: string[];
  /** Dimensions still unknown for this policy row (not global query unknowns). */
  unknown_dimensions: string[];
}

/** Ranked search hit wrapping public PolicyDto. */
export interface PolicySearchResultItemDraft {
  policy: PolicyDto;
  /** Deterministic relevance score from Backend (higher first). Tie-break: G1. */
  score: number;
  reasons: PolicySearchResultReasonDraft[];
  /**
   * Per-dimension verdicts for this row. Frontend uses for badges/tooltips.
   * Keys mirror interpreted condition dimensions.
   */
  verdicts: Partial<Record<string, PolicyMatchVerdict>>;
}

/** Top-level search response envelope (pagination + interpretation metadata). */
export interface PolicySearchResponseDraft {
  total: number;
  page: number;
  limit: number;
  /** Conditions Backend applied after merging NL + structured + user edits. */
  interpreted_conditions: PolicySearchInterpretedConditionDraft[];
  /** Global dimensions Backend could not resolve from the query (not guessed). */
  unconfirmed_dimensions: string[];
  items: PolicySearchResultItemDraft[];
}

/** G1-pending endpoint descriptor for planning only. */
export interface PolicySearchEndpointDraft {
  method: PolicySearchHttpMethod;
  /** Placeholder path — MUST NOT be hard-coded in production client pre-G1. */
  path: '/api/v1/policies/search' | '/api/v1/search/policies';
}

export const POLICY_SEARCH_ENDPOINT_DRAFT: PolicySearchEndpointDraft = {
  method: 'GET',
  path: '/api/v1/policies/search',
};
