import type { PolicyCategory, PolicyDto } from '../types/policy.js';
import { getCategoryLabel } from './policyDisplay.js';

export const CALENDAR_FILTER_CATEGORIES: PolicyCategory[] = [
  'housing',
  'employment',
  'finance',
  'welfare',
  'startup',
  'education',
  'other',
];

const KNOWN_CALENDAR_CATEGORIES = new Set<PolicyCategory>(
  CALENDAR_FILTER_CATEGORIES,
);

export interface CalendarCategoryTheme {
  label: string;
  chipClass: string;
  dotClass: string;
}

const CATEGORY_THEME: Record<PolicyCategory, CalendarCategoryTheme> = {
  housing: {
    label: getCategoryLabel('housing'),
    chipClass: 'calendar-chip--housing',
    dotClass: 'calendar-category-dot--housing',
  },
  employment: {
    label: getCategoryLabel('employment'),
    chipClass: 'calendar-chip--employment',
    dotClass: 'calendar-category-dot--employment',
  },
  finance: {
    label: getCategoryLabel('finance'),
    chipClass: 'calendar-chip--finance',
    dotClass: 'calendar-category-dot--finance',
  },
  welfare: {
    label: getCategoryLabel('welfare'),
    chipClass: 'calendar-chip--welfare',
    dotClass: 'calendar-category-dot--welfare',
  },
  startup: {
    label: getCategoryLabel('startup'),
    chipClass: 'calendar-chip--startup',
    dotClass: 'calendar-category-dot--startup',
  },
  education: {
    label: getCategoryLabel('education'),
    chipClass: 'calendar-chip--education',
    dotClass: 'calendar-category-dot--education',
  },
  other: {
    label: getCategoryLabel('other'),
    chipClass: 'calendar-chip--other',
    dotClass: 'calendar-category-dot--other',
  },
};

export function getCalendarCategoryTheme(
  category: PolicyCategory,
): CalendarCategoryTheme {
  return CATEGORY_THEME[category];
}

export function getPrimaryPolicyCategory(
  policy: Pick<PolicyDto, 'categories'>,
): PolicyCategory {
  const [first] = policy.categories;
  if (first && KNOWN_CALENDAR_CATEGORIES.has(first)) {
    return first;
  }
  return 'other';
}

export function policyMatchesCategoryFilters(
  policy: Pick<PolicyDto, 'categories'>,
  enabledCategories: ReadonlySet<PolicyCategory>,
): boolean {
  if (policy.categories.length === 0) {
    return enabledCategories.has('other');
  }

  return policy.categories.some((category) => {
    const normalizedCategory = KNOWN_CALENDAR_CATEGORIES.has(category)
      ? category
      : 'other';
    return enabledCategories.has(normalizedCategory);
  });
}

export function createDefaultEnabledCategories(): Set<PolicyCategory> {
  return new Set(CALENDAR_FILTER_CATEGORIES);
}
