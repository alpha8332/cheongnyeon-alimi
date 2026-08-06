import { POLICY_SEARCH_DEFAULTS } from '../types/policySearch.js';
import type { ApplicationStatus, PolicyCategory } from '../types/policy.js';
import { withPolicySearchPage } from './policySearchPagination.js';

/** URL state fields consumed by flat filter mutations. */
export interface PolicySearchFilterUrlState {
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

/** Flat filter dimensions that map to URL query params (excluding `q`). */
export type PolicySearchFilterDimension =
  | 'keyword'
  | 'region'
  | 'age'
  | 'category'
  | 'status'
  | 'include_partial';

export function hasPolicySearchFilterParam(
  state: PolicySearchFilterUrlState,
  dimension: PolicySearchFilterDimension,
): boolean {
  switch (dimension) {
    case 'keyword':
      return Boolean(state.keyword?.trim());
    case 'region':
      return Boolean(state.region?.trim());
    case 'age':
      return state.age !== null && state.age !== undefined;
    case 'category':
      return state.category !== null && state.category !== undefined;
    case 'status':
      return state.status !== null && state.status !== undefined;
    case 'include_partial':
      return state.include_partial !== POLICY_SEARCH_DEFAULTS.include_partial;
    default:
      return false;
  }
}

/** Remove one flat filter from URL state and reset page to 1. */
export function removePolicySearchFilter(
  state: PolicySearchFilterUrlState,
  dimension: PolicySearchFilterDimension,
): PolicySearchFilterUrlState {
  const cleared = clearPolicySearchFilter(state, dimension);
  return withPolicySearchPage(cleared, 1);
}

function clearPolicySearchFilter(
  state: PolicySearchFilterUrlState,
  dimension: PolicySearchFilterDimension,
): PolicySearchFilterUrlState {
  switch (dimension) {
    case 'keyword':
      return { ...state, keyword: null };
    case 'region':
      return { ...state, region: null };
    case 'age':
      return { ...state, age: null };
    case 'category':
      return { ...state, category: null };
    case 'status':
      return { ...state, status: null };
    case 'include_partial':
      return { ...state, include_partial: POLICY_SEARCH_DEFAULTS.include_partial };
    default:
      return state;
  }
}

export type PolicySearchFilterValue =
  | string
  | number
  | PolicyCategory
  | ApplicationStatus;

/** Set or update one flat filter in URL state and reset page to 1. */
export function updatePolicySearchFilter(
  state: PolicySearchFilterUrlState,
  dimension: Exclude<PolicySearchFilterDimension, 'include_partial'>,
  value: PolicySearchFilterValue,
): PolicySearchFilterUrlState {
  const next = applyPolicySearchFilterValue(state, dimension, value);
  return withPolicySearchPage(next, 1);
}

function applyPolicySearchFilterValue(
  state: PolicySearchFilterUrlState,
  dimension: Exclude<PolicySearchFilterDimension, 'include_partial'>,
  value: PolicySearchFilterValue,
): PolicySearchFilterUrlState {
  switch (dimension) {
    case 'keyword':
      return { ...state, keyword: String(value).trim() || null };
    case 'region':
      return { ...state, region: String(value).trim() || null };
    case 'age': {
      const parsed = typeof value === 'number' ? value : Number(value);
      return Number.isSafeInteger(parsed) ? { ...state, age: parsed } : state;
    }
    case 'category':
      return { ...state, category: value as PolicyCategory };
    case 'status':
      return { ...state, status: value as ApplicationStatus };
    default:
      return state;
  }
}
