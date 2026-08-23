import CalendarAllDayRow from '@/components/calendar/CalendarAllDayRow';
import CalendarEventChip from '@/components/calendar/CalendarEventChip';
import type { CalendarPolicyEvent } from '@/utils/calendarPolicyEvents';

interface CalendarDayViewProps {
  focusDate: string;
  todayYmd: string;
  eventsByDate: ReadonlyMap<string, readonly CalendarPolicyEvent[]>;
  onSelectEvent: (event: CalendarPolicyEvent) => void;
}

export default function CalendarDayView({
  focusDate,
  todayYmd,
  eventsByDate,
  onSelectEvent,
}: CalendarDayViewProps) {
  const events = eventsByDate.get(focusDate) ?? [];
  const isToday = focusDate === todayYmd;
  const dayNumber = Number(focusDate.slice(8, 10));
  const weekday = new Date(`${focusDate}T00:00:00Z`).getUTCDay();
  const weekdayLabels = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'];

  return (
    <section className="apple-calendar__day-view" aria-label="일간 달력">
      <CalendarAllDayRow
        dates={[focusDate]}
        eventsByDate={eventsByDate}
        todayYmd={todayYmd}
        onSelectEvent={onSelectEvent}
      />

      <header className="apple-calendar__day-header">
        <span className="apple-calendar__day-header-weekday">{weekdayLabels[weekday]}</span>
        <span
          className={`apple-calendar__day-number apple-calendar__day-number--large${isToday ? ' apple-calendar__day-number--today' : ''}`}
        >
          {dayNumber}
        </span>
      </header>

      {events.length === 0 ? (
        <p className="apple-calendar__empty-day">이 날짜에 표시할 신청 시작·마감 일정이 없습니다.</p>
      ) : (
        <ul className="apple-calendar__day-event-list">
          {events.map((event) => (
            <li key={`${event.policy.id}-${event.kind}`}>
              <CalendarEventChip event={event} onSelect={onSelectEvent} />
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
