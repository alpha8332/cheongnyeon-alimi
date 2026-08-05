import { mockPolicies } from '@/mocks/policies';
import {
  materializePolicySearchResponse,
  POLICY_SEARCH_SCENARIO_FIXTURES,
  type PolicySearchMockScenarioId,
} from '@/mocks/policySearchFixtures';
import {
  PolicySearchQueryValidationError,
  resolvePolicySearchQuery,
  type ResolvedPolicySearchQuery,
} from '@/mocks/policySearchRequest';
import {
  POLICY_SEARCH_ENDPOINT,
  type PolicySearchQueryParams,
  type PolicySearchResponse,
} from '@/types/policySearch';

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
    (hit) => hit.policy.data_quality_status !== 'partial',
  );

  return {
    ...response,
    total: items.length,
    items,
  };
}

export function handlePolicySearchMock(
  input: PolicySearchQueryParams | URLSearchParams,
): PolicySearchMockResult {
  const rawQ =
    input instanceof URLSearchParams ? (input.get('q') ?? '') : (input.q ?? '');

  if (rawQ.trim().length === 0) {
    return {
      status: 422,
      body: {
        detail:
          'q is required and must contain non-whitespace characters after trim.',
      },
    };
  }

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
    materializePolicySearchResponse(mockPolicies, fixture, query),
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
