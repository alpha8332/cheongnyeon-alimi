import type { PolicyDto, PolicySort } from '../types/policy.js';

export const POLICY_SORT_OPTIONS: ReadonlyArray<{
  value: PolicySort;
  label: string;
}> = [
  { value: 'default', label: '기본순' },
  { value: 'title_asc', label: '가나다순' },
  { value: 'title_desc', label: '가나다 역순' },
  { value: 'deadline_asc', label: '마감 임박순' },
  { value: 'deadline_desc', label: '마감 여유순' },
  { value: 'collected_desc', label: '최근 데이터 수집순' },
  { value: 'collected_asc', label: '오래된 데이터 수집순' },
];

const POLICY_SORT_VALUES = new Set<PolicySort>(
  POLICY_SORT_OPTIONS.map((option) => option.value),
);

export function isPolicySort(value: unknown): value is PolicySort {
  return typeof value === 'string' && POLICY_SORT_VALUES.has(value as PolicySort);
}

function compareNullableDate(
  left: string | null,
  right: string | null,
  direction: 1 | -1,
): number {
  if (left === null && right === null) {
    return 0;
  }
  if (left === null) {
    return 1;
  }
  if (right === null) {
    return -1;
  }
  return direction * left.localeCompare(right);
}

export function comparePolicies(
  left: PolicyDto,
  right: PolicyDto,
  sort: PolicySort,
): number {
  let compared = 0;
  if (sort === 'title_asc' || sort === 'title_desc') {
    compared = left.title.localeCompare(right.title, 'ko-KR');
    if (sort === 'title_desc') {
      compared *= -1;
    }
  } else if (sort === 'deadline_asc') {
    compared = compareNullableDate(left.application_end, right.application_end, 1);
  } else if (sort === 'deadline_desc') {
    compared = compareNullableDate(left.application_end, right.application_end, -1);
  } else if (sort === 'collected_desc') {
    compared = right.collected_at.localeCompare(left.collected_at);
  } else if (sort === 'collected_asc') {
    compared = left.collected_at.localeCompare(right.collected_at);
  }

  return compared || left.id - right.id;
}

export function sortByPolicy<T>(
  items: readonly T[],
  getPolicy: (item: T) => PolicyDto,
  sort: PolicySort,
): T[] {
  if (sort === 'default') {
    return [...items];
  }
  return [...items].sort((left, right) =>
    comparePolicies(getPolicy(left), getPolicy(right), sort),
  );
}
