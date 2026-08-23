import type { CalendarPolicyEvent } from '@/utils/calendarPolicyEvents';
import { getCalendarEventKindLabel } from '@/utils/calendarPolicyEvents';
import {
  getCalendarCategoryTheme,
  getPrimaryPolicyCategory,
} from '@/utils/calendarCategoryTheme';
import { getPolicyDisplayTitle } from '@/utils/policyDisplay';

interface CalendarEventChipProps {
  event: CalendarPolicyEvent;
  compact?: boolean;
  /** Modal 등에서만 kind 라벨(신청 시작·마감) 표시. 달력 칸 칩은 항상 정책명. */
  showKindLabel?: boolean;
  onSelect?: (event: CalendarPolicyEvent) => void;
}

export default function CalendarEventChip({
  event,
  compact = false,
  showKindLabel = false,
  onSelect,
}: CalendarEventChipProps) {
  const category = getPrimaryPolicyCategory(event.policy);
  const theme = getCalendarCategoryTheme(category);
  const displayTitle = getPolicyDisplayTitle(event.policy);
  const label = showKindLabel
    ? getCalendarEventKindLabel(event.kind)
    : displayTitle;

  const className = [
    'calendar-event-badge',
    'calendar-event-chip',
    theme.chipClass,
    `calendar-event-badge--${event.kind}`,
    compact ? 'calendar-event-badge--compact calendar-event-chip--compact' : '',
  ]
    .filter(Boolean)
    .join(' ');

  const labelNode = <span className="calendar-event-chip__text">{label}</span>;

  if (onSelect) {
    return (
      <button
        type="button"
        className={className}
        title={displayTitle}
        aria-label={`${getCalendarEventKindLabel(event.kind)}: ${displayTitle}`}
        onClick={(clickEvent) => {
          clickEvent.stopPropagation();
          onSelect(event);
        }}
      >
        {labelNode}
      </button>
    );
  }

  return (
    <span className={className} title={displayTitle}>
      {labelNode}
    </span>
  );
}
