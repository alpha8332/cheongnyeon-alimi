import type { ApplicationStatus, PolicyCategory, PolicyDto } from '../types/policy.js';
import type { RecommendationItemDto } from '../types/recommendation.js';

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

export function normalizeRecommendationCategory(
  category: string,
): PolicyCategory {
  return POLICY_CATEGORIES.has(category as PolicyCategory)
    ? (category as PolicyCategory)
    : 'other';
}

function normalizeRecommendationApplicationStatus(
  status: string,
): ApplicationStatus | null {
  return APPLICATION_STATUSES.has(status as ApplicationStatus)
    ? (status as ApplicationStatus)
    : null;
}

export function recommendationItemToPolicyDto(
  item: RecommendationItemDto,
): PolicyDto {
  const categories = Array.from(
    new Set(
      (item.categories?.length ? item.categories : [item.category]).map(
        normalizeRecommendationCategory,
      ),
    ),
  );

  return {
    schema_version: '1.2.0',
    source_id: item.source_id,
    source_name: item.source_id,
    external_id: item.external_id,
    title: item.title,
    organization: null,
    summary: null,
    category_text: null,
    categories,
    application_period_text: null,
    application_start: item.application_start,
    application_end: item.application_end,
    application_schedule:
      item.application_start || item.application_end ? 'fixed_period' : null,
    application_status: normalizeRecommendationApplicationStatus(
      item.application_status,
    ),
    region_text: null,
    regions: item.regions,
    age_min: item.min_age,
    age_max: item.max_age,
    age_condition_text: null,
    eligibility_text: null,
    support_content: null,
    application_method: null,
    education_statuses: [],
    employment_statuses: [],
    required_conditions: [],
    preferred_conditions: [],
    excluded_conditions: [],
    source_url: '',
    collected_at: new Date(0).toISOString(),
    data_quality_status: item.data_quality_status as PolicyDto['data_quality_status'],
    id: item.id,
    created_at: new Date(0).toISOString(),
    updated_at: new Date(0).toISOString(),
  };
}
