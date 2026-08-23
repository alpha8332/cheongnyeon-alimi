import CalendarEventChip from '@/components/calendar/CalendarEventChip';
import {
  CALENDAR_MAX_VISIBLE_BADGES_PER_DAY,
  type CalendarPolicyEvent,
} from '@/utils/calendarPolicyEvents';
import {
  buildMonthlyCalendarGrid,
  getCalendarWeekdayLabels,
  type CalendarMonthCell,
} from '@/utils/calendarMonthGrid';

interface CalendarMonthViewProps {
  year: number;
  month: number;
  todayYmd: string;
  focusDate: string;
  eventsByDate: ReadonlyMap<string, readonly CalendarPolicyEvent[]>;
  onSelectDate: (date: string) => void;
  onSelectEvent: (event: CalendarPolicyEvent) => void;
  onOpenDay: (date: string, events: readonly CalendarPolicyEvent[]) => void;
}

function MonthDayCell({
  cell,
  events,
  isFocused,
  onSelectDate,
  onSelectEvent,
  onOpenDay,
}: {
  cell: CalendarMonthCell;
  events: readonly CalendarPolicyEvent[];
  isFocused: boolean;
  onSelectDate: (date: string) => void;
  onSelectEvent: (event: CalendarPolicyEvent) => void;
  onOpenDay: (date: string, events: readonly CalendarPolicyEvent[]) => void;
}) {
  const visibleEvents = events.slice(0, CALENDAR_MAX_VISIBLE_BADGES_PER_DAY);
  const hiddenCount = events.length - visibleEvents.length;

  return (
    <div
      className={`monthly-calendar__day apple-calendar__month-day${cell.inCurrentMonth ? '' : ' monthly-calendar__day--outside'}${cell.isToday ? ' monthly-calendar__day--today apple-calendar__month-day--today' : ''}${isFocused ? ' apple-calendar__month-day--focused' : ''}`}
      role="gridcell"
    >
      <div className="monthly-calendar__day-button apple-calendar__month-day-button">
        <button
          type="button"
          className="apple-calendar__day-select"
          aria-label={`${cell.date} 일정 ${events.length}건`}
          onClick={() => {
            onSelectDate(cell.date);
            if (events.length > 0) {
              onOpenDay(cell.date, events);
            }
          }}
        >
          <span
            className={`monthly-calendar__day-number apple-calendar__day-number${cell.isToday ? ' apple-calendar__day-number--today' : ''}`}
          >
            {cell.day}
          </span>
        </button>
        <div className="monthly-calendar__badges apple-calendar__month-badges">
          {visibleEvents.map((event) => (
            <CalendarEventChip
              key={`${event.policy.id}-${event.kind}`}
              event={event}
              compact
              onSelect={(selectedEvent) => {
                onSelectEvent(selectedEvent);
              }}
            />
          ))}
          {hiddenCount > 0 ? (
            <button
              type="button"
              className="monthly-calendar__more-badge"
              onClick={() => onOpenDay(cell.date, events)}
            >
              +{hiddenCount}개 더보기
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function CalendarMonthView({
  year,
  month,
  todayYmd,
  focusDate,
  eventsByDate,
  onSelectDate,
  onSelectEvent,
  onOpenDay,
}: CalendarMonthViewProps) {
  const cells = buildMonthlyCalendarGrid(year, month, todayYmd);
  const weekdayLabels = getCalendarWeekdayLabels();

  return (
    <section className="monthly-calendar apple-calendar__month-view" aria-label="월간 달력">
      <div className="monthly-calendar__weekdays apple-calendar__weekday-row" aria-hidden="true">
        {weekdayLabels.map((label) => (
          <div key={label} className="monthly-calendar__weekday">
            {label}
          </div>
        ))}
      </div>

      <div className="monthly-calendar__grid apple-calendar__month-grid" role="grid" aria-readonly="true">
        {cells.map((cell) => (
          <MonthDayCell
            key={cell.date}
            cell={cell}
            events={eventsByDate.get(cell.date) ?? []}
            isFocused={cell.date === focusDate}
            onSelectDate={onSelectDate}
            onSelectEvent={onSelectEvent}
            onOpenDay={onOpenDay}
          />
        ))}
      </div>
    </section>
  );
}
