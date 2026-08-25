import {
  POLICY_SEARCH_DEFAULTS,
  POLICY_SEARCH_QUERY_LIMITS,
  type PolicySearchQueryParams,
} from '../types/policySearch.js';
import { isPolicySort } from '../utils/policySort.js';

export type ResolvedPolicySearchQuery = Required<
  Pick<PolicySearchQueryParams, 'include_partial' | 'page' | 'limit' | 'sort'>
> & {
  q: string;
  keyword?: string | null;
  region?: string | null;
  age?: number | null;
  category?: PolicySearchQueryParams['category'];
  status?: PolicySearchQueryParams['status'];
};

export class PolicySearchQueryValidationError extends Error {
  readonly detail: string;

  constructor(detail: string) {
    super(detail);
    this.name = 'PolicySearchQueryValidationError';
    this.detail = detail;
  }
}

function parseOptionalInt(value: string | null): number | undefined {
  if (value === null || value === '') {
    return undefined;
  }

  const parsed = Number(value);
  if (!Number.isSafeInteger(parsed)) {
    throw new PolicySearchQueryValidationError(
      'Query parameters must use valid integer values where required.',
    );
  }

  return parsed;
}

function parseOptionalBoolean(value: string | null): boolean | undefined {
  if (value === null || value === '') {
    return undefined;
  }

  if (value === 'true') {
    return true;
  }

  if (value === 'false') {
    return false;
  }

  throw new PolicySearchQueryValidationError(
    'include_partial must be true or false.',
  );
}

export function resolvePolicySearchQuery(
  input: PolicySearchQueryParams | URLSearchParams,
): ResolvedPolicySearchQuery {
  const raw =
    input instanceof URLSearchParams
      ? {
          q: input.get('q') ?? '',
          keyword: input.get('keyword'),
          region: input.get('region'),
          age: parseOptionalInt(input.get('age')),
          category: input.get('category') as PolicySearchQueryParams['category'],
          status: input.get('status') as PolicySearchQueryParams['status'],
          include_partial: parseOptionalBoolean(input.get('include_partial')),
          page: parseOptionalInt(input.get('page')),
          limit: parseOptionalInt(input.get('limit')),
          sort: input.get('sort') as PolicySearchQueryParams['sort'],
        }
      : input;

  const q = raw.q ?? '';
  const trimmedQ = q.trim();

  const hasExplicitCondition = Boolean(
    raw.keyword?.trim() ||
      raw.region?.trim() ||
      raw.age !== undefined && raw.age !== null ||
      raw.category ||
      raw.status,
  );

  if (trimmedQ.length === 0 && !hasExplicitCondition) {
    throw new PolicySearchQueryValidationError(
      'q or at least one explicit search condition is required.',
    );
  }

  if (trimmedQ.length > POLICY_SEARCH_QUERY_LIMITS.q) {
    throw new PolicySearchQueryValidationError(
      `q must not exceed ${POLICY_SEARCH_QUERY_LIMITS.q} characters.`,
    );
  }

  const keyword = raw.keyword?.trim() || undefined;
  if (keyword && keyword.length > POLICY_SEARCH_QUERY_LIMITS.keyword) {
    throw new PolicySearchQueryValidationError(
      `keyword must not exceed ${POLICY_SEARCH_QUERY_LIMITS.keyword} characters.`,
    );
  }

  const region = raw.region?.trim() || undefined;
  if (region && region.length > POLICY_SEARCH_QUERY_LIMITS.region) {
    throw new PolicySearchQueryValidationError(
      `region must not exceed ${POLICY_SEARCH_QUERY_LIMITS.region} characters.`,
    );
  }

  const page = raw.page ?? POLICY_SEARCH_DEFAULTS.page;
  const limit = raw.limit ?? POLICY_SEARCH_DEFAULTS.limit;
  const sort = raw.sort ?? POLICY_SEARCH_DEFAULTS.sort;

  if (!isPolicySort(sort)) {
    throw new PolicySearchQueryValidationError('sort is not supported.');
  }

  if (!Number.isSafeInteger(page) || page < 1) {
    throw new PolicySearchQueryValidationError(
      'page must be an integer greater than or equal to 1.',
    );
  }

  if (!Number.isSafeInteger(limit) || limit < 1 || limit > 100) {
    throw new PolicySearchQueryValidationError(
      'limit must be an integer from 1 to 100.',
    );
  }

  if (raw.age !== undefined && raw.age !== null) {
    if (!Number.isSafeInteger(raw.age) || raw.age < 0 || raw.age > 150) {
      throw new PolicySearchQueryValidationError(
        'age must be an integer from 0 to 150.',
      );
    }
  }

  return {
    q: trimmedQ,
    ...(keyword ? { keyword } : {}),
    ...(region ? { region } : {}),
    ...(raw.age !== undefined && raw.age !== null ? { age: raw.age } : {}),
    ...(raw.category ? { category: raw.category } : {}),
    ...(raw.status ? { status: raw.status } : {}),
    include_partial: raw.include_partial ?? POLICY_SEARCH_DEFAULTS.include_partial,
    page,
    limit,
    sort,
  };
}
