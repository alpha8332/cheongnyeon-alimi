import CalendarAllDayRow from '@/components/calendar/CalendarAllDayRow';
import CalendarEventChip from '@/components/calendar/CalendarEventChip';
import type { CalendarPolicyEvent } from '@/utils/calendarPolicyEvents';
import { getWeekDatesSundayStart } from '@/utils/calendarViewNavigation';

interface CalendarWeekViewProps {
  focusDate: string;
  todayYmd: string;
  eventsByDate: ReadonlyMap<string, readonly CalendarPolicyEvent[]>;
  onSelectDate: (date: string) => void;
  onSelectEvent: (event: CalendarPolicyEvent) => void;
}

const WEEKDAY_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'] as const;

export default function CalendarWeekView({
  focusDate,
  todayYmd,
  eventsByDate,
  onSelectDate,
  onSelectEvent,
}: CalendarWeekViewProps) {
  const weekDates = getWeekDatesSundayStart(focusDate);

  return (
    <section className="apple-calendar__week-view" aria-label="주간 달력">
      <CalendarAllDayRow
        dates={weekDates}
        eventsByDate={eventsByDate}
        todayYmd={todayYmd}
        onSelectEvent={onSelectEvent}
      />

      <div className="apple-calendar__week-header">
        {weekDates.map((date, index) => {
          const isToday = date === todayYmd;
          const dayNumber = Number(date.slice(8, 10));

          return (
            <button
              key={date}
              type="button"
              className={`apple-calendar__week-header-cell${isToday ? ' apple-calendar__week-header-cell--today' : ''}`}
              onClick={() => onSelectDate(date)}
            >
              <span className="apple-calendar__week-header-weekday">{WEEKDAY_SHORT[index]}</span>
              <span
                className={`apple-calendar__day-number${isToday ? ' apple-calendar__day-number--today' : ''}`}
              >
                {dayNumber}
              </span>
            </button>
          );
        })}
      </div>

      <div className="apple-calendar__week-columns">
        {weekDates.map((date) => {
          const events = eventsByDate.get(date) ?? [];

          return (
            <div key={date} className="apple-calendar__week-column">
              {events.length === 0 ? (
                <p className="apple-calendar__empty-day">일정 없음</p>
              ) : (
                <ul className="apple-calendar__week-event-list">
                  {events.map((event) => (
                    <li key={`${event.policy.id}-${event.kind}`}>
                      <CalendarEventChip event={event} onSelect={onSelectEvent} />
                    </li>
                  ))}
                </ul>
              )}
            </div>
          );
        })}
      </div>
    </section>
  );
}
