import {
  addCalendarMonths,
  buildMonthlyCalendarGrid,
} from '@/utils/calendarMonthGrid';

interface CalendarMiniMonthPickerProps {
  year: number;
  month: number;
  todayYmd: string;
  focusDate: string;
  onSelectDate: (date: string) => void;
  onMonthChange: (year: number, month: number) => void;
}

export default function CalendarMiniMonthPicker({
  year,
  month,
  todayYmd,
  focusDate,
  onSelectDate,
  onMonthChange,
}: CalendarMiniMonthPickerProps) {
  const cells = buildMonthlyCalendarGrid(year, month, todayYmd);
  const { year: prevYear, month: prevMonth } = addCalendarMonths(year, month, -1);
  const { year: nextYear, month: nextMonth } = addCalendarMonths(year, month, 1);

  return (
    <div className="apple-calendar__mini-picker" aria-label="미니 달력">
      <div className="apple-calendar__mini-header">
        <button
          type="button"
          className="apple-calendar__mini-nav"
          aria-label="이전 달"
          onClick={() => onMonthChange(prevYear, prevMonth)}
        >
          ‹
        </button>
        <span className="apple-calendar__mini-label">
          {year}년 {String(month).padStart(2, '0')}월
        </span>
        <button
          type="button"
          className="apple-calendar__mini-nav"
          aria-label="다음 달"
          onClick={() => onMonthChange(nextYear, nextMonth)}
        >
          ›
        </button>
      </div>

      <div className="apple-calendar__mini-weekdays" aria-hidden="true">
        {['일', '월', '화', '수', '목', '금', '토'].map((label) => (
          <span key={label}>{label}</span>
        ))}
      </div>

      <div className="apple-calendar__mini-grid">
        {cells.map((cell) => {
          const isSelected = cell.date === focusDate;
          const className = [
            'apple-calendar__mini-day',
            cell.inCurrentMonth ? '' : 'apple-calendar__mini-day--outside',
            cell.isToday ? 'apple-calendar__mini-day--today' : '',
            isSelected ? 'apple-calendar__mini-day--selected' : '',
          ]
            .filter(Boolean)
            .join(' ');

          return (
            <button
              key={cell.date}
              type="button"
              className={className}
              aria-label={cell.date}
              aria-pressed={isSelected}
              onClick={() => onSelectDate(cell.date)}
            >
              <span>{cell.day}</span>
            </button>
          );
        })}
      </div>
    </div>
  );
}
