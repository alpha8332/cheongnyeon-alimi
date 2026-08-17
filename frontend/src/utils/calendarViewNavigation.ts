import { addCalendarMonths, addDaysToYmd } from './calendarMonthGrid.js';

export type CalendarViewMode = 'day' | 'week' | 'month' | 'year';

const ENGLISH_MONTHS = [
  'January',
  'February',
  'March',
  'April',
  'May',
  'June',
  'July',
  'August',
  'September',
  'October',
  'November',
  'December',
] as const;

const ENGLISH_MONTHS_SHORT = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
] as const;

function parseYmd(ymd: string): { year: number; month: number; day: number } {
  const [year, month, day] = ymd.split('-').map(Number);
  return { year, month, day };
}

function getWeekdayIndex(ymd: string): number {
  const { year, month, day } = parseYmd(ymd);
  return new Date(Date.UTC(year, month - 1, day)).getUTCDay();
}

export function getWeekDatesSundayStart(focusDate: string): string[] {
  const start = addDaysToYmd(focusDate, -getWeekdayIndex(focusDate));
  return Array.from({ length: 7 }, (_, index) => addDaysToYmd(start, index));
}

export function shiftFocusDate(
  focusDate: string,
  viewMode: CalendarViewMode,
  direction: -1 | 1,
): string {
  const { year, month, day } = parseYmd(focusDate);

  switch (viewMode) {
    case 'day':
      return addDaysToYmd(focusDate, direction);
    case 'week':
      return addDaysToYmd(focusDate, direction * 7);
    case 'month': {
      const next = addCalendarMonths(year, month, direction);
      const clampedDay = Math.min(day, 28);
      return `${next.year}-${String(next.month).padStart(2, '0')}-${String(clampedDay).padStart(2, '0')}`;
    }
    case 'year':
      return `${year + direction}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    default:
      return focusDate;
  }
}

export function formatCalendarToolbarTitle(
  focusDate: string,
  viewMode: CalendarViewMode,
): string {
  const { year, month, day } = parseYmd(focusDate);
  const monthName = ENGLISH_MONTHS[month - 1] ?? 'Month';

  if (viewMode === 'month' || viewMode === 'year') {
    return `${monthName} ${year}`;
  }

  if (viewMode === 'day') {
    return `${monthName} ${day}, ${year}`;
  }

  const weekDates = getWeekDatesSundayStart(focusDate);
  const start = parseYmd(weekDates[0]!);
  const end = parseYmd(weekDates[6]!);
  const startLabel = `${ENGLISH_MONTHS_SHORT[start.month - 1] ?? 'Mon'} ${start.day}`;
  const endLabel =
    start.year === end.year
      ? `${ENGLISH_MONTHS_SHORT[end.month - 1] ?? 'Mon'} ${end.day}, ${end.year}`
      : `${ENGLISH_MONTHS_SHORT[end.month - 1] ?? 'Mon'} ${end.day}, ${end.year}`;

  return `${startLabel} – ${endLabel}`;
}

export function getViewMonthFromFocusDate(focusDate: string): {
  year: number;
  month: number;
} {
  const { year, month } = parseYmd(focusDate);
  return { year, month };
}

export function buildYearMonthCells(): Array<{ month: number; label: string }> {
  return Array.from({ length: 12 }, (_, index) => ({
    month: index + 1,
    label: ENGLISH_MONTHS_SHORT[index] ?? String(index + 1),
  }));
}
