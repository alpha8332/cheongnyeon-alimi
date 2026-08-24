import type { PolicyCategory } from '@/types/policy';
import {
  CALENDAR_FILTER_CATEGORIES,
  getCalendarCategoryTheme,
} from '@/utils/calendarCategoryTheme';

interface CalendarCategoryFiltersProps {
  enabledCategories: ReadonlySet<PolicyCategory>;
  onToggleCategory: (category: PolicyCategory) => void;
}

export default function CalendarCategoryFilters({
  enabledCategories,
  onToggleCategory,
}: CalendarCategoryFiltersProps) {
  return (
    <div className="apple-calendar__filters" aria-label="분야별 필터">
      <h3 className="apple-calendar__sidebar-title">분야</h3>
      <ul className="apple-calendar__filter-list">
        {CALENDAR_FILTER_CATEGORIES.map((category) => {
          const theme = getCalendarCategoryTheme(category);
          const checked = enabledCategories.has(category);
          const inputId = `calendar-filter-${category}`;

          return (
            <li key={category}>
              <label className="apple-calendar__filter-item" htmlFor={inputId}>
                <input
                  id={inputId}
                  type="checkbox"
                  className="apple-calendar__filter-checkbox"
                  checked={checked}
                  onChange={() => onToggleCategory(category)}
                />
                <span
                  className={`apple-calendar__category-dot ${theme.dotClass}`}
                  aria-hidden="true"
                />
                <span>{theme.label}</span>
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
