import type { PolicyCategory, PolicyDto } from '../types/policy.js';

export interface ProgramFilterState {
  search: string;
  region: string;
  category: PolicyCategory | '';
  age: string;
  includePartial: boolean;
}

export const EMPTY_PROGRAM_FILTERS: ProgramFilterState = {
  search: '',
  region: '',
  category: '',
  age: '',
  includePartial: true,
};

function normalizeSearch(value: string): string {
  return value.trim().toLowerCase();
}

function matchesSearch(policy: PolicyDto, search: string): boolean {
  if (!search) {
    return true;
  }

  const haystack = [
    policy.title,
    policy.organization,
    policy.support_content,
    policy.category_text,
    policy.eligibility_text,
    policy.region_text,
    policy.age_condition_text,
  ]
    .filter((value): value is string => value !== null)
    .join(' ')
    .toLowerCase();

  return haystack.includes(search);
}

function matchesRegion(policy: PolicyDto, region: string): boolean {
  if (!region) {
    return true;
  }

  if (policy.regions.includes('전국')) {
    return true;
  }

  return policy.regions.includes(region);
}

function matchesCategory(
  policy: PolicyDto,
  category: PolicyCategory | '',
): boolean {
  if (!category) {
    return true;
  }

  return policy.categories.includes(category);
}

function matchesAge(policy: PolicyDto, ageValue: string): boolean {
  if (!ageValue.trim()) {
    return true;
  }

  const age = Number(ageValue);
  if (!Number.isInteger(age) || age < 0 || age > 150) {
    return false;
  }

  if (policy.age_min === null && policy.age_max === null) {
    return true;
  }

  const min = policy.age_min ?? 0;
  const max = policy.age_max ?? 150;
  return age >= min && age <= max;
}

export function filterPrograms(
  policies: PolicyDto[],
  filters: ProgramFilterState,
): PolicyDto[] {
  const search = normalizeSearch(filters.search);

  return policies.filter(
    (policy) =>
      matchesSearch(policy, search) &&
      matchesRegion(policy, filters.region) &&
      matchesCategory(policy, filters.category) &&
      matchesAge(policy, filters.age),
  );
}

export function collectRegionOptions(policies: PolicyDto[]): string[] {
  const regions = new Set<string>();

  for (const policy of policies) {
    for (const region of policy.regions) {
      if (region !== '전국') {
        regions.add(region);
      }
    }
  }

  return [...regions].sort((left, right) => left.localeCompare(right, 'ko'));
}
