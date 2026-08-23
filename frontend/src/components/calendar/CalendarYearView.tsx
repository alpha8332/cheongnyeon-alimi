import { buildYearMonthCells } from '@/utils/calendarViewNavigation';
import { isYmdWithinMonth } from '@/utils/calendarMonthGrid';
import type { CalendarPolicyEvent } from '@/utils/calendarPolicyEvents';

interface CalendarYearViewProps {
  year: number;
  eventsByDate: ReadonlyMap<string, readonly CalendarPolicyEvent[]>;
  onSelectMonth: (year: number, month: number) => void;
}

function countEventsInMonth(
  eventsByDate: ReadonlyMap<string, readonly CalendarPolicyEvent[]>,
  year: number,
  month: number,
): number {
  let count = 0;
  for (const [date, events] of eventsByDate) {
    if (isYmdWithinMonth(date, year, month)) {
      count += events.length;
    }
  }
  return count;
}

export default function CalendarYearView({
  year,
  eventsByDate,
  onSelectMonth,
}: CalendarYearViewProps) {
  const months = buildYearMonthCells();

  return (
    <section className="apple-calendar__year-view" aria-label="연간 달력">
      <div className="apple-calendar__year-grid">
        {months.map(({ month, label }) => {
          const eventCount = countEventsInMonth(eventsByDate, year, month);

          return (
            <button
              key={month}
              type="button"
              className="apple-calendar__year-month"
              onClick={() => onSelectMonth(year, month)}
            >
              <span className="apple-calendar__year-month-label">{label}</span>
              <span className="apple-calendar__year-month-count">
                {eventCount > 0 ? `${eventCount}건` : '일정 없음'}
              </span>
            </button>
          );
        })}
      </div>
    </section>
  );
}
