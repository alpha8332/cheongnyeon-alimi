import type { ReactNode } from 'react';
import CalendarCategoryFilters from '@/components/calendar/CalendarCategoryFilters';
import CalendarMiniMonthPicker from '@/components/calendar/CalendarMiniMonthPicker';
import type { PolicyCategory } from '@/types/policy';

interface AppleCalendarLayoutProps {
  sidebarOpen: boolean;
  onSidebarToggle: () => void;
  enabledCategories: ReadonlySet<PolicyCategory>;
  onToggleCategory: (category: PolicyCategory) => void;
  miniPickerYear: number;
  miniPickerMonth: number;
  todayYmd: string;
  focusDate: string;
  onMiniPickerMonthChange: (year: number, month: number) => void;
  onSelectDate: (date: string) => void;
  toolbar: ReactNode;
  children: ReactNode;
}

export default function AppleCalendarLayout({
  sidebarOpen,
  onSidebarToggle,
  enabledCategories,
  onToggleCategory,
  miniPickerYear,
  miniPickerMonth,
  todayYmd,
  focusDate,
  onMiniPickerMonthChange,
  onSelectDate,
  toolbar,
  children,
}: AppleCalendarLayoutProps) {
  return (
    <div className="apple-calendar">
      <button
        type="button"
        className="apple-calendar__sidebar-toggle"
        aria-expanded={sidebarOpen}
        onClick={onSidebarToggle}
      >
        필터·미니 달력
      </button>

      <aside
        className={`apple-calendar__sidebar${sidebarOpen ? ' apple-calendar__sidebar--open' : ''}`}
        aria-label="달력 사이드바"
      >
        <CalendarCategoryFilters
          enabledCategories={enabledCategories}
          onToggleCategory={onToggleCategory}
        />
        <CalendarMiniMonthPicker
          year={miniPickerYear}
          month={miniPickerMonth}
          todayYmd={todayYmd}
          focusDate={focusDate}
          onSelectDate={onSelectDate}
          onMonthChange={onMiniPickerMonthChange}
        />
      </aside>

      <div className="apple-calendar__main">
        {toolbar}
        <div className="apple-calendar__view-body">{children}</div>
      </div>
    </div>
  );
}
