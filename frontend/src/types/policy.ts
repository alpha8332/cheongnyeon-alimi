export type PolicyCategory =
  | 'housing'
  | 'finance'
  | 'welfare'
  | 'employment'
  | 'startup'
  | 'education'
  | 'other';

export type ApplicationSchedule =
  | 'fixed_period'
  | 'always'
  | 'until_budget_exhausted';

export type ApplicationStatus = 'open' | 'closed' | 'scheduled';

export type DataQualityStatus = 'valid' | 'partial' | 'invalid';

export type DocumentRole =
  | 'list_response'
  | 'list_item'
  | 'detail_response';

export interface RawProvenance {
  raw_document_id: string;
  document_role: DocumentRole;
  content_hash: string;
  collected_at: string;
  source_url: string;
}

export interface NormalizedProgram {
  schema_version: '1.0.0';
  source_id: string;
  source_name: string;
  external_id: string | null;
  title: string;
  organization: string | null;
  summary: string | null;
  category_text: string | null;
  categories: PolicyCategory[];
  application_period_text: string | null;
  application_start: string | null;
  application_end: string | null;
  application_schedule: ApplicationSchedule | null;
  application_status: ApplicationStatus | null;
  region_text: string | null;
  regions: string[];
  age_min: number | null;
  age_max: number | null;
  age_condition_text: string | null;
  eligibility_text: string | null;
  support_content: string | null;
  application_method: string | null;
  education_statuses: string[];
  employment_statuses: string[];
  required_conditions: string[];
  preferred_conditions: string[];
  excluded_conditions: string[];
  source_url: string;
  collected_at: string;
  provenance: RawProvenance[];
  data_quality_status: DataQualityStatus;
}
