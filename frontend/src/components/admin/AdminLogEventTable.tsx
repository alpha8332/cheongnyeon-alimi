import {
  getAdminLogEventKey,
  type AdminLogEventListItemDto,
} from '@/types/adminLog';

interface AdminLogEventTableProps {
  items: AdminLogEventListItemDto[];
  selectedEventId: string | null;
  onSelectEvent: (eventId: string) => void;
}

export default function AdminLogEventTable({
  items,
  selectedEventId,
  onSelectEvent,
}: AdminLogEventTableProps) {
  return (
    <div className="admin-log-event-table-wrap">
      <table className="admin-log-event-table">
        <caption className="admin-log-event-table__caption">
          로그 이벤트 (현재 페이지 {items.length}건)
        </caption>
        <thead>
          <tr>
            <th scope="col">timestamp</th>
            <th scope="col">level</th>
            <th scope="col">component</th>
            <th scope="col">event</th>
            <th scope="col">수집 실행 ID</th>
            <th scope="col">error_type</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => {
            const eventId = getAdminLogEventKey(item);
            return (
              <tr
                key={eventId}
                className={
                  selectedEventId === eventId
                    ? 'admin-log-event-table__row admin-log-event-table__row--selected'
                    : 'admin-log-event-table__row'
                }
              >
                <td>
                  <button
                    type="button"
                    className="admin-log-event-table__select-btn"
                    onClick={() => onSelectEvent(eventId)}
                  >
                    {new Date(item.timestamp).toLocaleString('ko-KR')}
                  </button>
                </td>
                <td>{item.level}</td>
                <td>{item.component}</td>
                <td>{item.event}</td>
                <td>{item.collection_run_id ?? '—'}</td>
                <td>{item.error_type ?? '—'}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

interface AdminLogEventDetailPanelProps {
  event: AdminLogEventListItemDto | null;
  onClose: () => void;
}

export function AdminLogEventDetailPanel({
  event,
  onClose,
}: AdminLogEventDetailPanelProps) {
  if (!event) return null;

  return (
    <aside className="admin-log-event-detail" aria-label="로그 이벤트 상세">
      <header className="admin-log-event-detail__header">
        <h3 className="admin-log-event-detail__title">이벤트 상세</h3>
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          닫기
        </button>
      </header>
      <dl className="admin-log-event-detail__grid">
        <div><dt>timestamp</dt><dd>{event.timestamp}</dd></div>
        <div><dt>level</dt><dd>{event.level}</dd></div>
        <div><dt>component</dt><dd>{event.component}</dd></div>
        <div><dt>event</dt><dd>{event.event}</dd></div>
        <div><dt>request_id</dt><dd>{event.request_id ?? '—'}</dd></div>
        <div><dt>수집 실행 ID (collection_run_id)</dt><dd>{event.collection_run_id ?? '—'}</dd></div>
        <div><dt>source_id</dt><dd>{event.source_id ?? '—'}</dd></div>
        <div><dt>duration_ms</dt><dd>{event.duration_ms ?? '—'}</dd></div>
        <div><dt>error_type</dt><dd>{event.error_type ?? '—'}</dd></div>
      </dl>
      <p className="admin-log-event-detail__note" role="note">
        스택 추적, 자격 증명, 원문 및 SQL 매개변수는 표시하지 않습니다.
      </p>
    </aside>
  );
}
