/**
 * W3-F0 DRAFT — URL query state for natural-language search (G1 pending).
 * Serializes PolicySearchRequestDraft fields to /search route searchParams.
 * Does not perform NL parsing; only round-trips user-visible state.
 */

import type {
  PolicySearchInterpretedConditionDraft,
  PolicySearchRequestDraft,
  PolicySearchStructuredFilters,
} from '@/types/draft/policySearch.contract';
import type { ApplicationStatus, PolicyCategory } from '@/types/policy';

/** Planned route for Frontend 04 NL search (distinct from /programs list API). */
export const POLICY_SEARCH_ROUTE = '/search';

export interface PolicySearchUrlStateDraft {
  q: string;
  page: number;
  limit: number;
  include_partial: boolean;
  exclude_confirmed_mismatch: boolean;
  category?: PolicyCategory;
  region?: string;
  age?: number;
  status?: ApplicationStatus;
  /**
   * Serialized interpreted chips after first response (JSON, URI-encoded).
   * G1: size limits and PII — keep structured fields only, no raw NL re-parse.
   */
  interpreted?: string;
}

const DEFAULT_LIMIT = 10;

export const DEFAULT_POLICY_SEARCH_URL_STATE: PolicySearchUrlStateDraft = {
  q: '',
  page: 1,
  limit: DEFAULT_LIMIT,
  include_partial: false,
  exclude_confirmed_mismatch: true,
};

export function parsePolicySearchUrlState(
  params: URLSearchParams,
): PolicySearchUrlStateDraft {
  const page = Number(params.get('page') ?? '1');
  const limit = Number(params.get('limit') ?? String(DEFAULT_LIMIT));
  const ageRaw = params.get('age');

  return {
    q: params.get('q') ?? '',
    page: Number.isInteger(page) && page >= 1 ? page : 1,
    limit: Number.isInteger(limit) && limit >= 1 && limit <= 100 ? limit : DEFAULT_LIMIT,
    include_partial: params.get('include_partial') === 'true',
    exclude_confirmed_mismatch: params.get('exclude_confirmed_mismatch') !== 'false',
    category: (params.get('category') as PolicyCategory | null) ?? undefined,
    region: params.get('region') ?? undefined,
    age:
      ageRaw !== null && ageRaw !== '' && Number.isInteger(Number(ageRaw))
        ? Number(ageRaw)
        : undefined,
    status: (params.get('status') as ApplicationStatus | null) ?? undefined,
    interpreted: params.get('interpreted') ?? undefined,
  };
}

export function toPolicySearchRequestDraft(
  state: PolicySearchUrlStateDraft,
): PolicySearchRequestDraft {
  const structured: PolicySearchStructuredFilters = {};
  if (state.category) structured.category = state.category;
  if (state.region) structured.region = state.region;
  if (state.age !== undefined) structured.age = state.age;
  if (state.status) structured.status = state.status;

  return {
    q: state.q,
    structured: Object.keys(structured).length > 0 ? structured : undefined,
    page: state.page,
    limit: state.limit,
    include_partial: state.include_partial,
    exclude_confirmed_mismatch: state.exclude_confirmed_mismatch,
  };
}

export function buildPolicySearchSearchParams(
  state: PolicySearchUrlStateDraft,
): URLSearchParams {
  const params = new URLSearchParams();
  if (state.q) params.set('q', state.q);
  if (state.page !== 1) params.set('page', String(state.page));
  if (state.limit !== DEFAULT_LIMIT) params.set('limit', String(state.limit));
  if (state.include_partial) params.set('include_partial', 'true');
  if (!state.exclude_confirmed_mismatch) params.set('exclude_confirmed_mismatch', 'false');
  if (state.category) params.set('category', state.category);
  if (state.region) params.set('region', state.region);
  if (state.age !== undefined) params.set('age', String(state.age));
  if (state.status) params.set('status', state.status);
  if (state.interpreted) params.set('interpreted', state.interpreted);
  return params;
}

export function serializeInterpretedConditions(
  conditions: PolicySearchInterpretedConditionDraft[],
): string {
  return encodeURIComponent(JSON.stringify(conditions));
}

export function deserializeInterpretedConditions(
  encoded: string | undefined,
): PolicySearchInterpretedConditionDraft[] {
  if (!encoded) return [];
  try {
    const parsed = JSON.parse(decodeURIComponent(encoded)) as PolicySearchInterpretedConditionDraft[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}
