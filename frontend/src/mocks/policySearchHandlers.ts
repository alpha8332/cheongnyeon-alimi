import type { PolicyDto } from '../types/policy.js';
import type {
  InterpretedCondition,
  PolicySearchHit,
} from '../types/policySearch.js';
import { sortByPolicy } from '../utils/policySort.js';
import {
  materializePolicySearchResponse,
  POLICY_SEARCH_SCENARIO_FIXTURES,
  type PolicySearchMockScenarioId,
} from './policySearchFixtures.js';
import {
  PolicySearchQueryValidationError,
  resolvePolicySearchQuery,
  type ResolvedPolicySearchQuery,
} from './policySearchRequest.js';
import {
  POLICY_SEARCH_ENDPOINT,
  type PolicySearchQueryParams,
  type PolicySearchResponse,
} from '../types/policySearch.js';

export type PolicySearchMockSuccess = {
  status: 200;
  body: PolicySearchResponse;
};

export type PolicySearchMockValidationFailure = {
  status: 422;
  body: {
    detail: string;
  };
};

export type PolicySearchMockResult =
  | PolicySearchMockSuccess
  | PolicySearchMockValidationFailure;

export const POLICY_SEARCH_MOCK_PATH = POLICY_SEARCH_ENDPOINT.path;

function normalizeParam(value: string | null | undefined): string | undefined {
  const trimmed = value?.trim();
  return trimmed ? trimmed : undefined;
}

function detectScenarioId(
  query: ResolvedPolicySearchQuery,
): PolicySearchMockScenarioId | null {
  const keyword = normalizeParam(query.keyword);
  const region = normalizeParam(query.region);

  if (query.q === '지원금' && keyword === '지원금') {
    return 'M6';
  }

  if (region === '서울특별시' && query.q.includes('서울') && query.q.includes('주거')) {
    return 'M1';
  }

  if (query.age === 25 && query.q.includes('25') && query.q.includes('일자리')) {
    return 'M3';
  }

  if (query.q.includes('복지로') && query.q.includes('생활')) {
    return 'M4';
  }

  if (query.q.includes('전국') && query.q.includes('청년')) {
    return 'M2';
  }

  return null;
}

function filterPartialHits(
  response: PolicySearchResponse,
  includePartial: boolean,
): PolicySearchResponse {
  if (includePartial) {
    return response;
  }

  const items = response.items.filter(
    (hit: PolicySearchResponse['items'][number]) =>
      hit.policy.data_quality_status !== 'partial',
  );

  return {
    ...response,
    total: items.length,
    items,
  };
}

function materializeExplicitFilterResponse(
  policies: readonly PolicyDto[],
  query: ResolvedPolicySearchQuery,
  qRaw: string,
): PolicySearchResponse {
  const conditions: InterpretedCondition[] = [];
  if (query.region) {
    conditions.push({
      dimension: 'region',
      value: query.region,
      source: 'explicit',
      resolution: 'resolved',
      candidates: [],
    });
  }
  if (query.category) {
    conditions.push({
      dimension: 'category',
      value: query.category,
      source: 'explicit',
      resolution: 'resolved',
      candidates: [],
    });
  }

  const hits: PolicySearchHit[] = policies
    .filter((policy) => policy.application_status !== 'closed')
    .filter(
      (policy) => !query.category || policy.categories.includes(query.category),
    )
    .filter((policy) => {
      const isNationwide =
        policy.region_text?.includes('전국') ||
        policy.regions.some((region) => region === '전국' || region === '0000000000');
      if (!query.region || isNationwide) {
        return true;
      }
      const district = query.region.split(/\s+/).at(-1) ?? query.region;
      return Boolean(
        policy.region_text?.includes(query.region) ||
          policy.region_text?.includes(district),
      );
    })
    .map((policy) => ({
      policy,
      score: 1,
      verdicts: {
        region: query.region ? 'match' : null,
        age: null,
        status: null,
        category: query.category ? 'match' : null,
      },
      unknown_count: 0,
      reason_codes: [
        ...(query.region ? ['REGION_MATCH'] : []),
        ...(query.category ? ['CATEGORY_MATCH'] : []),
      ],
      message: '선택한 검색 조건과 일치하는 정책입니다.',
      unconfirmed_conditions: [],
    }));
  const sorted = sortByPolicy(hits, (hit) => hit.policy, query.sort);
  const offset = (query.page - 1) * query.limit;

  return {
    total: sorted.length,
    page: query.page,
    limit: query.limit,
    interpreted_conditions: {
      q_raw: qRaw,
      q_clean: query.q,
      conditions,
      override_fields: conditions.map((condition) => condition.dimension),
      uninterpreted_terms: [],
    },
    items: sorted.slice(offset, offset + query.limit),
  };
}

export function handlePolicySearchMock(
  input: PolicySearchQueryParams | URLSearchParams,
  policies: readonly PolicyDto[],
): PolicySearchMockResult {
  const rawQ =
    input instanceof URLSearchParams ? (input.get('q') ?? '') : (input.q ?? '');

  let query: ResolvedPolicySearchQuery;

  try {
    query = resolvePolicySearchQuery(input);
  } catch (error) {
    if (error instanceof PolicySearchQueryValidationError) {
      return {
        status: 422,
        body: { detail: error.detail },
      };
    }

    throw error;
  }

  const scenarioId = detectScenarioId(query);

  if (scenarioId === null && query.q === '') {
    return {
      status: 200,
      body: filterPartialHits(
        materializeExplicitFilterResponse(policies, query, rawQ),
        query.include_partial,
      ),
    };
  }

  if (scenarioId === null) {
    return {
      status: 200,
      body: {
        total: 0,
        page: query.page,
        limit: query.limit,
        interpreted_conditions: {
          q_raw: rawQ,
          q_clean: query.q,
          conditions: [],
          override_fields: [],
          uninterpreted_terms: query.q.split(/\s+/).filter(Boolean),
        },
        items: [],
      },
    };
  }

  const fixture = POLICY_SEARCH_SCENARIO_FIXTURES[scenarioId];
  const body = filterPartialHits(
    materializePolicySearchResponse(policies, fixture, query),
    query.include_partial,
  );

  return {
    status: 200,
    body,
  };
}

/** MSW wiring deferred to FE4-14; export stable handler metadata for dev/test. */
export const policySearchMockHandlers = {
  method: POLICY_SEARCH_ENDPOINT.method,
  path: POLICY_SEARCH_MOCK_PATH,
  handle: handlePolicySearchMock,
  scenarios: POLICY_SEARCH_SCENARIO_FIXTURES,
} as const;

export type PolicySearchMockHandlers = typeof policySearchMockHandlers;
