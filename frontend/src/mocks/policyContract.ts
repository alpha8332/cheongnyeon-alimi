import type {
  EligibilitySummaryDto,
  PolicyDetailDto,
  PolicyDto,
  PolicyListResponse,
  PublicDataQualityStatus,
} from '../types/policy.js';
import {
  resolvePolicyListQuery,
  type ResolvedPolicyListQuery,
} from '../api/policyRequest.js';
import { sortByPolicy } from '../utils/policySort.js';

type SeedQualityStatus = PublicDataQualityStatus | 'invalid';

export interface SeedPolicyProgram
  extends Omit<
    PolicyDetailDto,
    'id' | 'created_at' | 'updated_at' | 'data_quality_status'
  > {
  provenance: unknown[];
  keywords: string[];
  life_stages: string[];
  target_groups: string[];
  coverage_scope: 'nationwide' | 'regional' | 'unknown';
  region_rules: unknown[];
  data_quality_status: SeedQualityStatus;
}

const MOCK_DATABASE_TIMESTAMP = '2026-07-30T00:00:00Z';

function toPolicyDto(program: SeedPolicyProgram, id: number): PolicyDto {
  if (program.data_quality_status === 'invalid') {
    throw new Error('Invalid seed programs cannot be exposed by the Policy API.');
  }

  return {
    schema_version: program.schema_version,
    source_id: program.source_id,
    source_name: program.source_name,
    external_id: program.external_id,
    title: program.title,
    organization: program.organization,
    summary: program.summary,
    category_text: program.category_text,
    categories: [...program.categories],
    application_period_text: program.application_period_text,
    application_start: program.application_start,
    application_end: program.application_end,
    application_schedule: program.application_schedule,
    application_status: program.application_status,
    region_text: program.region_text,
    regions: [...program.regions],
    age_min: program.age_min,
    age_max: program.age_max,
    age_condition_text: program.age_condition_text,
    eligibility_text: program.eligibility_text,
    support_content: program.support_content,
    application_method: program.application_method,
    education_statuses: [...program.education_statuses],
    employment_statuses: [...program.employment_statuses],
    required_conditions: [...program.required_conditions],
    preferred_conditions: [...program.preferred_conditions],
    excluded_conditions: [...program.excluded_conditions],
    source_url: program.source_url,
    collected_at: program.collected_at,
    data_quality_status: program.data_quality_status,
    id,
    created_at: MOCK_DATABASE_TIMESTAMP,
    updated_at: MOCK_DATABASE_TIMESTAMP,
  };
}

function cloneEligibilitySummary(
  summary: EligibilitySummaryDto,
): EligibilitySummaryDto {
  return structuredClone(summary);
}

function toPolicyDetailDto(
  program: SeedPolicyProgram,
  id: number,
): PolicyDetailDto {
  return {
    ...toPolicyDto(program, id),
    eligibility_summary: cloneEligibilitySummary(
      program.eligibility_summary,
    ),
  };
}

export function createMockPolicies(
  seedPrograms: readonly SeedPolicyProgram[],
): PolicyDto[] {
  return seedPrograms.flatMap((program, index) =>
    program.data_quality_status === 'invalid'
      ? []
      : [toPolicyDto(program, index + 1)],
  );
}

export function createMockPolicyDetails(
  seedPrograms: readonly SeedPolicyProgram[],
): PolicyDetailDto[] {
  return seedPrograms.flatMap((program, index) =>
    program.data_quality_status === 'invalid'
      ? []
      : [toPolicyDetailDto(program, index + 1)],
  );
}

function matchesQuery(
  policy: PolicyDto,
  query: ResolvedPolicyListQuery,
): boolean {
  if (
    policy.data_quality_status === 'partial' &&
    !query.include_partial
  ) {
    return false;
  }

  if (query.category && !policy.categories.includes(query.category)) {
    return false;
  }

  if (query.region && !policy.regions.includes(query.region)) {
    return false;
  }

  return !query.status || policy.application_status === query.status;
}

export function createMockPolicyListResponse(
  policies: readonly PolicyDto[],
  query = resolvePolicyListQuery(),
): PolicyListResponse {
  const filteredPolicies = sortByPolicy(
    policies.filter((policy) => matchesQuery(policy, query)),
    (policy) => policy,
    query.sort,
  );
  const offset = (query.page - 1) * query.limit;

  return {
    total: filteredPolicies.length,
    page: query.page,
    limit: query.limit,
    items: filteredPolicies.slice(offset, offset + query.limit),
  };
}

export function findMockPolicyById(
  policies: readonly PolicyDetailDto[],
  policyId: number,
  includePartial = false,
): PolicyDetailDto | null {
  const policy = policies.find((candidate) => candidate.id === policyId);

  if (
    !policy ||
    (policy.data_quality_status === 'partial' && !includePartial)
  ) {
    return null;
  }

  return policy;
}
