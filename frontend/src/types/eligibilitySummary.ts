/**
 * Integration 08 W4-G0 eligibility_summary proposal (Backend draft aligned).
 * @see docs/development/develop_plan/integration/08_eligibility_evidence_summary.md
 */

export type EligibilitySummaryStatus = 'complete' | 'partial' | 'unknown';

export type EligibilityConditionCategory =
  | 'age'
  | 'region'
  | 'income'
  | 'asset'
  | 'employment'
  | 'education'
  | 'housing'
  | 'household'
  | 'other';

export type InstitutionalContactType = 'phone' | 'url' | 'email';

/** Public evidence metadata exposed on policy detail (no DB or credential fields). */
export interface ItemEvidenceDto {
  source_id: string;
  source_url: string;
  collected_at: string;
}

export interface ItemConditionDto {
  category: EligibilityConditionCategory | (string & {});
  content: string;
  evidence: ItemEvidenceDto | null;
}

export interface ItemDocumentDto {
  name: string;
  content: string | null;
  evidence: ItemEvidenceDto | null;
}

export interface InstitutionalContactDto {
  label: string;
  value: string;
  contact_type: InstitutionalContactType;
}

export interface EligibilitySummaryDto {
  status: EligibilitySummaryStatus;
  requirements: ItemConditionDto[];
  exclusions: ItemConditionDto[];
  preferences: ItemConditionDto[];
  required_documents: ItemDocumentDto[];
  unknown_conditions: string[];
  institutional_contacts: InstitutionalContactDto[];
}

export const ELIGIBILITY_SUMMARY_STATUSES: readonly EligibilitySummaryStatus[] = [
  'complete',
  'partial',
  'unknown',
] as const;

export const ELIGIBILITY_CONDITION_CATEGORIES: readonly EligibilityConditionCategory[] =
  [
    'age',
    'region',
    'income',
    'asset',
    'employment',
    'education',
    'housing',
    'household',
    'other',
  ] as const;
