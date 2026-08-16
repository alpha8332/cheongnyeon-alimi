import type { PolicyCategory } from '@/types/policy';
import { getCalendarCategoryTheme } from '@/utils/calendarCategoryTheme';

interface PolicyCategoryBadgeProps {
  category: PolicyCategory;
  label?: string;
  compact?: boolean;
}

export default function PolicyCategoryBadge({
  category,
  label,
  compact = false,
}: PolicyCategoryBadgeProps) {
  const theme = getCalendarCategoryTheme(category);

  return (
    <span
      className={`policy-category-badge calendar-event-chip ${theme.chipClass}${compact ? ' policy-category-badge--compact' : ''}`}
    >
      {label ?? theme.label}
    </span>
  );
}
