import { useEffect } from 'react';
import { Link } from 'react-router';
import Button from '@/components/common/Button';
import CalendarEventChip from '@/components/calendar/CalendarEventChip';
import type { CalendarPolicyEvent } from '@/utils/calendarPolicyEvents';
import { getCalendarEventKindLabel } from '@/utils/calendarPolicyEvents';
import { buildProgramDetailRoutePath } from '@/utils/policyDetailNavigation';
import { getDDayLabel } from '@/utils/policyDeadline';
import {
  formatAge,
  formatApplicationPeriod,
  formatNullableText,
  formatRegion,
} from '@/utils/policyDisplay';

interface CalendarEventDetailDialogProps {
  event: CalendarPolicyEvent;
  onClose: () => void;
}

export default function CalendarEventDetailDialog({
  event,
  onClose,
}: CalendarEventDetailDialogProps) {
  const policy = event.policy;
  const detailPath = buildProgramDetailRoutePath(policy.id, {
    includePartial: policy.data_quality_status === 'partial',
  });

  useEffect(() => {
    const onKeyDown = (keyboardEvent: KeyboardEvent) => {
      if (keyboardEvent.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  return (
    <div className="calendar-modal-overlay" onClick={onClose}>
      <div
        className="calendar-modal calendar-modal--event-detail"
        role="dialog"
        aria-modal="true"
        aria-labelledby="calendar-event-detail-title"
        onClick={(clickEvent) => clickEvent.stopPropagation()}
      >
        <h2 id="calendar-event-detail-title" className="calendar-modal__title">
          {policy.title}
        </h2>
        <p className="calendar-modal__description">
          {getCalendarEventKindLabel(event.kind)} · {event.date} (Asia/Seoul)
        </p>

        <div className="calendar-modal__event-item calendar-modal__event-item--single">
          <div className="calendar-modal__event-header">
            <CalendarEventChip event={event} showKindLabel />
            {event.kind === 'end' ? (
              <span className="calendar-modal__dday">{getDDayLabel(policy)}</span>
            ) : null}
          </div>
          <p className="calendar-modal__event-meta">
            신청 기간: {formatApplicationPeriod(policy)}
          </p>
          <p className="calendar-modal__event-meta">
            지원 대상:{' '}
            {formatNullableText(
              policy.eligibility_text,
              `${formatAge(policy)} · ${formatRegion(policy)}`,
            )}
          </p>
          {policy.application_method ? (
            <p className="calendar-modal__event-meta">{policy.application_method}</p>
          ) : null}
          <div className="calendar-modal__event-links">
            <Link to={detailPath}>정책 상세</Link>
            {policy.source_url ? (
              <a href={policy.source_url} target="_blank" rel="noreferrer">
                신청 링크
              </a>
            ) : null}
          </div>
        </div>

        <div className="calendar-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </div>
  );
}
