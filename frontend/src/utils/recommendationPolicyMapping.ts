import type { ApplicationStatus, PolicyCategory, PolicyDto } from '../types/policy.js';
import type { RecommendationItemDto } from '../types/recommendation.js';

export function recommendationItemToPolicyDto(
  item: RecommendationItemDto,
): PolicyDto {
  return {
    schema_version: '1.2.0',
    source_id: item.source_id,
    source_name: item.source_id,
    external_id: item.external_id,
    title: item.title,
    organization: null,
    summary: null,
    category_text: null,
    categories: [item.category as PolicyCategory],
    application_period_text: null,
    application_start: item.application_start,
    application_end: item.application_end,
    application_schedule: 'fixed_period',
    application_status: item.application_status as ApplicationStatus,
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
