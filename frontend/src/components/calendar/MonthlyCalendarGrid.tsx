import {
  CALENDAR_MAX_VISIBLE_BADGES_PER_DAY,
  type CalendarPolicyEvent,
} from '@/utils/calendarPolicyEvents';
import { getCalendarEventKindLabel } from '@/utils/calendarPolicyEvents';
import {
  addCalendarMonths,
  buildMonthlyCalendarGrid,
  formatCalendarMonthLabel,
  getCalendarWeekdayLabels,
  type CalendarMonthCell,
} from '@/utils/calendarMonthGrid';

interface MonthlyCalendarGridProps {
  year: number;
  month: number;
  todayYmd: string;
  eventsByDate: ReadonlyMap<string, readonly CalendarPolicyEvent[]>;
  onMonthChange: (year: number, month: number) => void;
  onOpenDay: (date: string, events: readonly CalendarPolicyEvent[]) => void;
}

function MonthNavButton({
  label,
  onClick,
}: {
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      className="monthly-calendar__nav-btn"
      aria-label={label}
      onClick={onClick}
    >
      {label}
    </button>
  );
}

function DayCell({
  cell,
  events,
  onOpenDay,
}: {
  cell: CalendarMonthCell;
  events: readonly CalendarPolicyEvent[];
  onOpenDay: (date: string, events: readonly CalendarPolicyEvent[]) => void;
}) {
  const visibleEvents = events.slice(0, CALENDAR_MAX_VISIBLE_BADGES_PER_DAY);
  const hiddenCount = events.length - visibleEvents.length;

  return (
    <div
      className={`monthly-calendar__day${cell.inCurrentMonth ? '' : ' monthly-calendar__day--outside'}${cell.isToday ? ' monthly-calendar__day--today' : ''}`}
    >
      <button
        type="button"
        className="monthly-calendar__day-button"
        aria-label={`${cell.date} 일정 ${events.length}건`}
        onClick={() => {
          if (events.length > 0) {
            onOpenDay(cell.date, events);
          }
        }}
      >
        <span className="monthly-calendar__day-number">{cell.day}</span>
        <div className="monthly-calendar__badges">
          {visibleEvents.map((event) => (
            <span
              key={`${event.policy.id}-${event.kind}`}
              className={`calendar-event-badge calendar-event-badge--compact calendar-event-badge--${event.kind}`}
              title={event.policy.title}
            >
              {getCalendarEventKindLabel(event.kind)}
            </span>
          ))}
          {hiddenCount > 0 ? (
            <span className="monthly-calendar__more-badge">+{hiddenCount}개 더보기</span>
          ) : null}
        </div>
      </button>
    </div>
  );
}

export default function MonthlyCalendarGrid({
  year,
  month,
  todayYmd,
  eventsByDate,
  onMonthChange,
  onOpenDay,
}: MonthlyCalendarGridProps) {
  const cells = buildMonthlyCalendarGrid(year, month, todayYmd);
  const weekdayLabels = getCalendarWeekdayLabels();
  const { year: prevYear, month: prevMonth } = addCalendarMonths(year, month, -1);
  const { year: nextYear, month: nextMonth } = addCalendarMonths(year, month, 1);

  return (
    <section className="monthly-calendar" aria-label="월간 마감 달력">
      <div className="monthly-calendar__header">
        <MonthNavButton
          label="이전 달"
          onClick={() => onMonthChange(prevYear, prevMonth)}
        />
        <h2 className="monthly-calendar__month-label">
          {formatCalendarMonthLabel(year, month)}
        </h2>
        <MonthNavButton
          label="다음 달"
          onClick={() => onMonthChange(nextYear, nextMonth)}
        />
      </div>

      <div className="monthly-calendar__weekdays" aria-hidden="true">
        {weekdayLabels.map((label) => (
          <div key={label} className="monthly-calendar__weekday">
            {label}
          </div>
        ))}
      </div>

      <div className="monthly-calendar__grid" role="grid" aria-readonly="true">
        {cells.map((cell) => (
          <DayCell
            key={cell.date}
            cell={cell}
            events={eventsByDate.get(cell.date) ?? []}
            onOpenDay={onOpenDay}
          />
        ))}
      </div>
    </section>
  );
}
