import type { CalendarViewMode } from '@/utils/calendarViewNavigation';
import { formatCalendarToolbarTitle } from '@/utils/calendarViewNavigation';

const VIEW_MODES: CalendarViewMode[] = ['day', 'week', 'month', 'year'];

const VIEW_MODE_LABELS: Record<CalendarViewMode, string> = {
  day: 'Day',
  week: 'Week',
  month: 'Month',
  year: 'Year',
};

interface CalendarToolbarProps {
  focusDate: string;
  viewMode: CalendarViewMode;
  onViewModeChange: (mode: CalendarViewMode) => void;
  onNavigate: (direction: -1 | 1) => void;
  onToday: () => void;
}

export default function CalendarToolbar({
  focusDate,
  viewMode,
  onViewModeChange,
  onNavigate,
  onToday,
}: CalendarToolbarProps) {
  return (
    <div className="apple-calendar__toolbar">
      <h2 className="apple-calendar__toolbar-title">
        {formatCalendarToolbarTitle(focusDate, viewMode)}
      </h2>

      <div
        className="apple-calendar__view-segments"
        role="tablist"
        aria-label="달력 보기 전환"
      >
        {VIEW_MODES.map((mode) => (
          <button
            key={mode}
            type="button"
            role="tab"
            aria-selected={viewMode === mode}
            className={`apple-calendar__view-segment${viewMode === mode ? ' apple-calendar__view-segment--active' : ''}`}
            onClick={() => onViewModeChange(mode)}
          >
            {VIEW_MODE_LABELS[mode]}
          </button>
        ))}
      </div>

      <div className="apple-calendar__toolbar-nav">
        <button
          type="button"
          className="apple-calendar__toolbar-nav-btn"
          aria-label="이전"
          onClick={() => onNavigate(-1)}
        >
          ‹
        </button>
        <button
          type="button"
          className="apple-calendar__toolbar-nav-btn apple-calendar__toolbar-nav-btn--today"
          onClick={onToday}
        >
          Today
        </button>
        <button
          type="button"
          className="apple-calendar__toolbar-nav-btn"
          aria-label="다음"
          onClick={() => onNavigate(1)}
        >
          ›
        </button>
      </div>
    </div>
  );
}
