import type { NormalizedProgram, PolicyCategory } from '@/types/policy';

export interface ProgramFilterState {
  search: string;
  region: string;
  category: PolicyCategory | '';
  age: string;
}

export const EMPTY_PROGRAM_FILTERS: ProgramFilterState = {
  search: '',
  region: '',
  category: '',
  age: '',
};

function normalizeSearch(value: string): string {
  return value.trim().toLowerCase();
}

function matchesSearch(program: NormalizedProgram, search: string): boolean {
  if (!search) {
    return true;
  }

  const haystack = [
    program.title,
    program.organization,
    program.support_content,
    program.category_text,
    program.eligibility_text,
    program.region_text,
    program.age_condition_text,
  ]
    .filter((value): value is string => value !== null)
    .join(' ')
    .toLowerCase();

  return haystack.includes(search);
}

function matchesRegion(program: NormalizedProgram, region: string): boolean {
  if (!region) {
    return true;
  }

  if (program.regions.includes('전국')) {
    return true;
  }

  return program.regions.includes(region);
}

function matchesCategory(
  program: NormalizedProgram,
  category: PolicyCategory | '',
): boolean {
  if (!category) {
    return true;
  }

  return program.categories.includes(category);
}

function matchesAge(program: NormalizedProgram, ageValue: string): boolean {
  if (!ageValue.trim()) {
    return true;
  }

  const age = Number(ageValue);
  if (!Number.isInteger(age) || age < 0 || age > 150) {
    return false;
  }

  if (program.age_min === null && program.age_max === null) {
    return true;
  }

  const min = program.age_min ?? 0;
  const max = program.age_max ?? 150;
  return age >= min && age <= max;
}

export function filterPrograms(
  programs: NormalizedProgram[],
  filters: ProgramFilterState,
): NormalizedProgram[] {
  const search = normalizeSearch(filters.search);

  return programs.filter(
    (program) =>
      matchesSearch(program, search) &&
      matchesRegion(program, filters.region) &&
      matchesCategory(program, filters.category) &&
      matchesAge(program, filters.age),
  );
}

export function collectRegionOptions(programs: NormalizedProgram[]): string[] {
  const regions = new Set<string>();

  for (const program of programs) {
    for (const region of program.regions) {
      if (region !== '전국') {
        regions.add(region);
      }
    }
  }

  return [...regions].sort((left, right) => left.localeCompare(right, 'ko'));
}
