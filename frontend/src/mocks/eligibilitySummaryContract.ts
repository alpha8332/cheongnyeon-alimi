import type {
  EligibilitySummaryDto,
  EligibilitySummaryStatus,
  ItemEvidenceDto,
} from '../types/eligibilitySummary.js';
import {
  ELIGIBILITY_CONDITION_CATEGORIES,
  ELIGIBILITY_SUMMARY_STATUSES,
} from '../types/eligibilitySummary.js';

const PUBLIC_EVIDENCE_KEYS = [
  'source_id',
  'source_url',
  'collected_at',
] as const satisfies readonly (keyof ItemEvidenceDto)[];

const FORBIDDEN_EVIDENCE_KEYS = [
  'raw_document_id',
  'db_id',
  'internal_id',
  'credential',
  'password',
  'pin',
  'token',
  'selector',
  'field',
  'snippet',
] as const;

export function isEligibilitySummaryStatus(
  value: unknown,
): value is EligibilitySummaryStatus {
  return (
    typeof value === 'string' &&
    (ELIGIBILITY_SUMMARY_STATUSES as readonly string[]).includes(value)
  );
}

function assertPlainObject(
  value: unknown,
  label: string,
): asserts value is Record<string, unknown> {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error(`${label} must be a plain object`);
  }
}

function assertString(value: unknown, label: string): asserts value is string {
  if (typeof value !== 'string') {
    throw new Error(`${label} must be a string`);
  }
}

function assertStringArray(
  value: unknown,
  label: string,
): asserts value is string[] {
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string')) {
    throw new Error(`${label} must be a string array`);
  }
}

function assertItemEvidence(value: unknown, label: string): void {
  if (value === null) {
    return;
  }

  assertPlainObject(value, label);

  for (const key of PUBLIC_EVIDENCE_KEYS) {
    assertString(value[key], `${label}.${key}`);
  }

  for (const key of Object.keys(value)) {
    if (!(PUBLIC_EVIDENCE_KEYS as readonly string[]).includes(key)) {
      throw new Error(`${label} contains unexpected key: ${key}`);
    }
  }

  for (const forbiddenKey of FORBIDDEN_EVIDENCE_KEYS) {
    if (forbiddenKey in value) {
      throw new Error(`${label} must not expose ${forbiddenKey}`);
    }
  }
}

function assertItemConditionArray(value: unknown, label: string): void {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array`);
  }

  for (const [index, item] of value.entries()) {
    const itemLabel = `${label}[${index}]`;
    assertPlainObject(item, itemLabel);
    assertString(item.category, `${itemLabel}.category`);
    assertString(item.content, `${itemLabel}.content`);
    assertItemEvidence(item.evidence, `${itemLabel}.evidence`);
  }
}

function assertItemDocumentArray(value: unknown, label: string): void {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array`);
  }

  for (const [index, item] of value.entries()) {
    const itemLabel = `${label}[${index}]`;
    assertPlainObject(item, itemLabel);
    assertString(item.name, `${itemLabel}.name`);

    if (item.content !== null && typeof item.content !== 'string') {
      throw new Error(`${itemLabel}.content must be string or null`);
    }

    assertItemEvidence(item.evidence, `${itemLabel}.evidence`);
  }
}

function assertInstitutionalContacts(value: unknown, label: string): void {
  if (!Array.isArray(value)) {
    throw new Error(`${label} must be an array`);
  }

  for (const [index, item] of value.entries()) {
    const itemLabel = `${label}[${index}]`;
    assertPlainObject(item, itemLabel);
    assertString(item.label, `${itemLabel}.label`);
    assertString(item.value, `${itemLabel}.value`);
    assertString(item.contact_type, `${itemLabel}.contact_type`);

    if (!['phone', 'url', 'email'].includes(item.contact_type)) {
      throw new Error(`${itemLabel}.contact_type must be phone, url, or email`);
    }
  }
}

/** Validates Integration 08 / Backend draft eligibility_summary envelope shape. */
export function assertEligibilitySummaryContract(
  summary: unknown,
): asserts summary is EligibilitySummaryDto {
  assertPlainObject(summary, 'eligibility_summary');

  if (!isEligibilitySummaryStatus(summary.status)) {
    throw new Error('eligibility_summary.status must be complete, partial, or unknown');
  }

  assertItemConditionArray(summary.requirements, 'eligibility_summary.requirements');
  assertItemConditionArray(summary.exclusions, 'eligibility_summary.exclusions');
  assertItemConditionArray(summary.preferences, 'eligibility_summary.preferences');
  assertItemDocumentArray(
    summary.required_documents,
    'eligibility_summary.required_documents',
  );
  assertStringArray(
    summary.unknown_conditions,
    'eligibility_summary.unknown_conditions',
  );
  assertInstitutionalContacts(
    summary.institutional_contacts,
    'eligibility_summary.institutional_contacts',
  );
}

export function isKnownEligibilityCategory(category: string): boolean {
  return (ELIGIBILITY_CONDITION_CATEGORIES as readonly string[]).includes(
    category,
  );
}
