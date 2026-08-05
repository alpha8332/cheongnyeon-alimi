/**
 * Policy Search URL query state types (Frontend 04).
 *
 * URL stores user input and explicit flat filters only.
 * Backend response fields (interpreted_conditions, verdicts, reason_codes, score,
 * unconfirmed_conditions) are NOT serialized into the URL query string.
 *
 * parse/build/toRequest helpers: implement in Slice FE4-14 (SearchBar & URL Sync).
 */

import type { PolicySearchQueryParams } from '@/types/policySearch';
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
 * without NL parsing. Implementation deferred to Slice FE4-14.
 */
export type PolicySearchUrlToRequest = PolicySearchUrlQueryState & PolicySearchQueryParams;
