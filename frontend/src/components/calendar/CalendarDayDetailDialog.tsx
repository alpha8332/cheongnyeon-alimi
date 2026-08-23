import { useEffect } from 'react';
import { Link } from 'react-router';
import Button from '@/components/common/Button';
import type { CalendarPolicyEvent } from '@/utils/calendarPolicyEvents';
import { getCalendarEventKindLabel } from '@/utils/calendarPolicyEvents';
import { buildProgramDetailRoutePath } from '@/utils/policyDetailNavigation';
import { getDDayLabel } from '@/utils/policyDeadline';
import { formatApplicationPeriod } from '@/utils/policyDisplay';

interface CalendarDayDetailDialogProps {
  date: string;
  events: readonly CalendarPolicyEvent[];
  onClose: () => void;
}

export default function CalendarDayDetailDialog({
  date,
  events,
  onClose,
}: CalendarDayDetailDialogProps) {
  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, [onClose]);

  return (
    <div className="calendar-modal-overlay" onClick={onClose}>
      <div
        className="calendar-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="calendar-day-detail-title"
        onClick={(event) => event.stopPropagation()}
      >
        <h2 id="calendar-day-detail-title" className="calendar-modal__title">
          {date} 일정
        </h2>
        <p className="calendar-modal__description">
          신청 시작·마감 일정입니다. 날짜 기준은 Asia/Seoul(KST)입니다.
        </p>

        <ul className="calendar-modal__event-list">
          {events.map((event) => {
            const policy = event.policy;
            const detailPath = buildProgramDetailRoutePath(policy.id, {
              includePartial: policy.data_quality_status === 'partial',
            });

            return (
              <li key={`${policy.id}-${event.kind}`} className="calendar-modal__event-item">
                <div className="calendar-modal__event-header">
                  <span
                    className={`calendar-event-badge calendar-event-badge--${event.kind}`}
                  >
                    {getCalendarEventKindLabel(event.kind)}
                  </span>
                  {event.kind === 'end' ? (
                    <span className="calendar-modal__dday">{getDDayLabel(policy)}</span>
                  ) : null}
                </div>
                <Link to={detailPath} className="calendar-modal__event-title">
                  {policy.title}
                </Link>
                <p className="calendar-modal__event-meta">
                  {formatApplicationPeriod(policy)}
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
              </li>
            );
          })}
        </ul>

        <div className="calendar-modal__actions">
          <Button type="button" variant="secondary" onClick={onClose}>
            닫기
          </Button>
        </div>
      </div>
    </div>
  );
}
