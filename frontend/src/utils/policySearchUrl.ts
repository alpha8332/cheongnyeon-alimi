import {
  POLICY_SEARCH_DEFAULTS,
  POLICY_SEARCH_QUERY_LIMITS,
  type PolicySearchQueryParams,
  type PolicySearchPreferences,
} from '@/types/policySearch';
import {
  POLICY_SEARCH_URL_DEFAULTS,
  type PolicySearchUrlQueryState,
} from '@/types/policySearchUrlState';
import type {
  ApplicationStatus,
  PolicyCategory,
  PolicySort,
} from '@/types/policy';
import {
  buildPolicySearchPageNumbers,
  getPolicySearchTotalPages,
  isPolicySearchResponseCurrent,
  withPolicySearchPage,
} from './policySearchPagination';

export {
  buildPolicySearchPageNumbers,
  getPolicySearchTotalPages,
  isPolicySearchResponseCurrent,
  withPolicySearchPage,
};

export {
  buildPolicySearchEntryPath,
  HOME_RECOMMENDED_SEARCHES,
} from './policySearchNavigation';

const POLICY_CATEGORIES = new Set<PolicyCategory>([
  'housing',
  'finance',
  'welfare',
  'employment',
  'startup',
  'education',
  'other',
]);

const APPLICATION_STATUSES = new Set<ApplicationStatus>([
  'open',
  'closed',
  'scheduled',
]);

const POLICY_SORTS = new Set<PolicySort>([
  'default',
  'title_asc',
  'title_desc',
  'deadline_asc',
  'deadline_desc',
  'collected_desc',
  'collected_asc',
]);

function parseOptionalInt(value: string | null): number | null {
  if (value === null || value.trim() === '') {
    return null;
  }

  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    return null;
  }

  return parsed;
}

function parseOptionalBoolean(value: string | null): boolean | null {
  if (value === null || value.trim() === '') {
    return null;
  }

  if (value === 'true') {
    return true;
  }

  if (value === 'false') {
    return false;
  }

  return null;
}

function parseOptionalCategory(value: string | null): PolicyCategory | null {
  if (!value) {
    return null;
  }

  return POLICY_CATEGORIES.has(value as PolicyCategory)
    ? (value as PolicyCategory)
    : null;
}

function parseOptionalStatus(value: string | null): ApplicationStatus | null {
  if (!value) {
    return null;
  }

  return APPLICATION_STATUSES.has(value as ApplicationStatus)
    ? (value as ApplicationStatus)
    : null;
}

function parsePolicySort(value: string | null): PolicySort {
  return value && POLICY_SORTS.has(value as PolicySort)
    ? (value as PolicySort)
    : POLICY_SEARCH_URL_DEFAULTS.sort;
}

/**
 * Read flat browser URL params into {@link PolicySearchUrlQueryState}.
 * Does not validate `q` for API — empty `q` means no search has been submitted.
 */
export function parsePolicySearchUrl(
  searchParams: URLSearchParams,
): PolicySearchUrlQueryState {
  const includePartial = parseOptionalBoolean(searchParams.get('include_partial'));
  const useSavedConditions = parseOptionalBoolean(
    searchParams.get('use_saved_conditions'),
  );
  const page = parseOptionalInt(searchParams.get('page'));
  const limit = parseOptionalInt(searchParams.get('limit'));
  const age = parseOptionalInt(searchParams.get('age'));

  return {
    q: searchParams.get('q') ?? '',
    use_saved_conditions: useSavedConditions ?? true,
    keyword: searchParams.get('keyword'),
    region: searchParams.get('region'),
    age,
    category: parseOptionalCategory(searchParams.get('category')),
    status: parseOptionalStatus(searchParams.get('status')),
    include_partial:
      includePartial ?? POLICY_SEARCH_URL_DEFAULTS.include_partial,
    page: page && page >= 1 ? page : POLICY_SEARCH_URL_DEFAULTS.page,
    limit:
      limit && limit >= 1 && limit <= 100
        ? limit
        : POLICY_SEARCH_URL_DEFAULTS.limit,
    sort: parsePolicySort(searchParams.get('sort')),
  };
}

/**
 * Serialize URL state to flat query params.
 * Response fields (interpreted_conditions, verdicts, etc.) are never written.
 */
export function buildPolicySearchUrlParams(
  state: PolicySearchUrlQueryState,
): URLSearchParams {
  const params = new URLSearchParams();

  const trimmedQ = state.q.trim();
  if (trimmedQ) {
    params.set('q', trimmedQ);
  }

  if (trimmedQ && state.use_saved_conditions === false) {
    params.set('use_saved_conditions', 'false');
  }

  const keyword = state.keyword?.trim();
  if (keyword) {
    params.set('keyword', keyword);
  }

  const region = state.region?.trim();
  if (region) {
    params.set('region', region);
  }

  if (state.age !== null && state.age !== undefined) {
    params.set('age', String(state.age));
  }

  if (state.category) {
    params.set('category', state.category);
  }

  if (state.status) {
    params.set('status', state.status);
  }

  if (state.include_partial !== POLICY_SEARCH_DEFAULTS.include_partial) {
    params.set('include_partial', String(state.include_partial));
  }

  if (state.page !== POLICY_SEARCH_DEFAULTS.page) {
    params.set('page', String(state.page));
  }

  if (state.limit !== POLICY_SEARCH_DEFAULTS.limit) {
    params.set('limit', String(state.limit));
  }

  if (trimmedQ && state.sort !== POLICY_SEARCH_DEFAULTS.sort) {
    params.set('sort', state.sort);
  }

  return params;
}

/** Whether the URL state contains a non-empty trimmed `q` suitable for API fetch. */
export function hasPolicySearchQuery(
  state: Pick<PolicySearchUrlQueryState, 'q'>,
): boolean {
  return state.q.trim().length > 0;
}

/**
 * Map URL state to flat API request params without NL parsing.
 * Trims `q` and passes explicit flat filters as-is.
 */
export function toPolicySearchRequest(
  state: PolicySearchUrlQueryState,
  preferences: PolicySearchPreferences | null = null,
): PolicySearchQueryParams {
  const trimmedQ = state.q.trim();

  return {
    q: trimmedQ,
    keyword: state.keyword?.trim() || null,
    region: state.region?.trim() || null,
    age: state.age,
    category: state.category,
    status: state.status,
    include_partial: state.include_partial,
    page: state.page,
    limit: state.limit,
    sort: state.sort,
    preferences,
  };
}

/** Guard against oversized flat params before writing to the URL. */
export function isPolicySearchUrlStateValid(
  state: PolicySearchUrlQueryState,
): boolean {
  const trimmedQ = state.q.trim();

  if (trimmedQ.length > POLICY_SEARCH_QUERY_LIMITS.q) {
    return false;
  }

  const keyword = state.keyword?.trim();
  if (keyword && keyword.length > POLICY_SEARCH_QUERY_LIMITS.keyword) {
    return false;
  }

  const region = state.region?.trim();
  if (region && region.length > POLICY_SEARCH_QUERY_LIMITS.region) {
    return false;
  }

  return true;
}
