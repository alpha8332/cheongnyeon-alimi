export interface CalendarMonthCell {
  /** YYYY-MM-DD (KST calendar date). */
  date: string;
  day: number;
  inCurrentMonth: boolean;
  isToday: boolean;
}

const WEEKDAY_LABELS = ['일', '월', '화', '수', '목', '금', '토'] as const;

export function getCalendarWeekdayLabels(): readonly string[] {
  return WEEKDAY_LABELS;
}

export function formatCalendarMonthLabel(year: number, month: number): string {
  return `${year}년 ${String(month).padStart(2, '0')}월`;
}

export function addCalendarMonths(
  year: number,
  month: number,
  delta: number,
): { year: number; month: number } {
  const anchor = new Date(Date.UTC(year, month - 1 + delta, 1));
  return {
    year: anchor.getUTCFullYear(),
    month: anchor.getUTCMonth() + 1,
  };
}

function formatUtcYmd(date: Date): string {
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

export function addDaysToYmd(ymd: string, deltaDays: number): string {
  const [year, month, day] = ymd.split('-').map(Number);
  const next = new Date(Date.UTC(year, month - 1, day + deltaDays));
  return formatUtcYmd(next);
}

function getDaysInMonth(year: number, month: number): number {
  return new Date(Date.UTC(year, month, 0)).getUTCDate();
}

function getWeekdayIndex(ymd: string): number {
  const [year, month, day] = ymd.split('-').map(Number);
  return new Date(Date.UTC(year, month - 1, day)).getUTCDay();
}

/** Build a 6-row Sunday-start month grid including leading/trailing dimmed days. */
export function buildMonthlyCalendarGrid(
  year: number,
  month: number,
  todayYmd: string,
): CalendarMonthCell[] {
  const monthStart = `${year}-${String(month).padStart(2, '0')}-01`;
  const daysInMonth = getDaysInMonth(year, month);
  const leadingDays = getWeekdayIndex(monthStart);
  const gridStart = addDaysToYmd(monthStart, -leadingDays);

  const cells: CalendarMonthCell[] = [];
  for (let offset = 0; offset < 42; offset += 1) {
    const date = addDaysToYmd(gridStart, offset);
    const day = Number(date.slice(8, 10));
    const inCurrentMonth =
      Number(date.slice(5, 7)) === month && Number(date.slice(0, 4)) === year;

    cells.push({
      date,
      day,
      inCurrentMonth,
      isToday: date === todayYmd,
    });
  }

  const monthEnd = `${year}-${String(month).padStart(2, '0')}-${String(daysInMonth).padStart(2, '0')}`;
  void monthEnd;

  return cells;
}

export function isYmdWithinMonth(ymd: string, year: number, month: number): boolean {
  const [y, m] = ymd.split('-').map(Number);
  return y === year && m === month;
}
