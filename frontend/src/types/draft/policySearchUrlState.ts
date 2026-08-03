/**
 * W3-F0 DRAFT — URL query state types only (Gate G1 pending).
 *
 * URL stores user input and explicit flat filters only.
 * Backend response fields (verdicts, reason_codes, interpreted NL chips) are
 * NOT serialized into the URL query string.
 *
 * parse/build/toRequest helpers: implement in post-G1 Slice FE4-05 (SearchBar & URL Sync).
 */

import type { PolicySearchQueryParams } from '@/types/draft/policySearch.contract';
import type { ApplicationStatus, PolicyCategory } from '@/types/policy';

/** Planned Frontend route for NL search (distinct from `/programs` list API). */
export const POLICY_SEARCH_ROUTE = '/search';

/**
 * Browser URL query state for `/search`.
 * Field set mirrors {@link PolicySearchQueryParams} fields that may appear in the URL.
 */
export interface PolicySearchUrlQueryState {
  q: string;
  keyword?: string | null;
  region?: string | null;
  age?: number | null;
  category?: PolicyCategory | null;
  status?: ApplicationStatus | null;
  include_partial: boolean;
  page: number;
  limit: number;
}

/** Defaults when URL omits optional params (align with POLICY_SEARCH_DEFAULTS). */
export const POLICY_SEARCH_URL_DEFAULTS: Pick<
  PolicySearchUrlQueryState,
  'include_partial' | 'page' | 'limit'
> = {
  include_partial: true,
  page: 1,
  limit: 20,
};

/**
 * Type-level note: PolicySearchUrlQueryState round-trips to PolicySearchQueryParams
 * without NL parsing. Implementation deferred to G1-approved Slice FE4-05.
 */
export type PolicySearchUrlToRequest = PolicySearchUrlQueryState & PolicySearchQueryParams;
