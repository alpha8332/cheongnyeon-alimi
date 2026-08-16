import CalendarEventChip from '@/components/calendar/CalendarEventChip';
import type { CalendarPolicyEvent } from '@/utils/calendarPolicyEvents';

interface CalendarAllDayRowProps {
  dates: readonly string[];
  eventsByDate: ReadonlyMap<string, readonly CalendarPolicyEvent[]>;
  todayYmd: string;
  onSelectEvent: (event: CalendarPolicyEvent) => void;
}

function formatColumnHeader(date: string, todayYmd: string): string {
  const day = Number(date.slice(8, 10));
  return date === todayYmd ? String(day) : String(day);
}

export default function CalendarAllDayRow({
  dates,
  eventsByDate,
  todayYmd,
  onSelectEvent,
}: CalendarAllDayRowProps) {
  const hasAnyEvents = dates.some((date) => (eventsByDate.get(date)?.length ?? 0) > 0);
  if (!hasAnyEvents) {
    return null;
  }

  return (
    <div className="apple-calendar__all-day" aria-label="종일 일정">
      <div className="apple-calendar__all-day-label">all-day</div>
      <div
        className="apple-calendar__all-day-columns"
        style={{ gridTemplateColumns: `repeat(${dates.length}, minmax(0, 1fr))` }}
      >
        {dates.map((date) => {
          const events = eventsByDate.get(date) ?? [];
          const isToday = date === todayYmd;

          return (
            <div key={date} className="apple-calendar__all-day-column">
              <span
                className={`apple-calendar__all-day-date${isToday ? ' apple-calendar__all-day-date--today' : ''}`}
                aria-hidden="true"
              >
                {formatColumnHeader(date, todayYmd)}
              </span>
              <div className="apple-calendar__all-day-chips">
                {events.map((event) => (
                  <CalendarEventChip
                    key={`${event.policy.id}-${event.kind}`}
                    event={event}
                    compact
                    onSelect={onSelectEvent}
                  />
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
