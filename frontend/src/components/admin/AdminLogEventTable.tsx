import type { AdminLogEventListItemDto } from '@/types/adminLog';

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
          Log events ({items.length} rows on page)
        </caption>
        <thead>
          <tr>
            <th scope="col">timestamp</th>
            <th scope="col">level</th>
            <th scope="col">component</th>
            <th scope="col">event</th>
            <th scope="col">run_id</th>
            <th scope="col">error_type</th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr
              key={item.event_id}
              className={
                selectedEventId === item.event_id
                  ? 'admin-log-event-table__row admin-log-event-table__row--selected'
                  : 'admin-log-event-table__row'
              }
            >
              <td>
                <button
                  type="button"
                  className="admin-log-event-table__select-btn"
                  onClick={() => onSelectEvent(item.event_id)}
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
          ))}
        </tbody>
      </table>
    </div>
  );
}

interface AdminLogEventDetailPanelProps {
  event: AdminLogEventListItemDto | null;
  message: string | null;
  onClose: () => void;
}

export function AdminLogEventDetailPanel({
  event,
  message,
  onClose,
}: AdminLogEventDetailPanelProps) {
  if (!event) {
    return null;
  }

  return (
    <aside className="admin-log-event-detail" aria-label="Log event 상세">
      <header className="admin-log-event-detail__header">
        <h3 className="admin-log-event-detail__title">Event 상세</h3>
        <button type="button" className="btn btn-secondary" onClick={onClose}>
          닫기
        </button>
      </header>
      <dl className="admin-log-event-detail__grid">
        <div>
          <dt>event_id</dt>
          <dd>{event.event_id}</dd>
        </div>
        <div>
          <dt>file_id</dt>
          <dd>{event.file_id}</dd>
        </div>
        <div>
          <dt>level</dt>
          <dd>{event.level}</dd>
        </div>
        <div>
          <dt>component</dt>
          <dd>{event.component}</dd>
        </div>
        <div>
          <dt>event</dt>
          <dd>{event.event}</dd>
        </div>
        <div>
          <dt>request_id</dt>
          <dd>{event.request_id ?? '—'}</dd>
        </div>
        <div>
          <dt>collection_run_id</dt>
          <dd>{event.collection_run_id ?? '—'}</dd>
        </div>
        <div>
          <dt>source_id</dt>
          <dd>{event.source_id ?? '—'}</dd>
        </div>
        <div>
          <dt>duration_ms</dt>
          <dd>{event.duration_ms ?? '—'}</dd>
        </div>
        <div>
          <dt>error_type</dt>
          <dd>{event.error_type ?? '—'}</dd>
        </div>
        {message ? (
          <div className="admin-log-event-detail__full">
            <dt>message</dt>
            <dd>{message}</dd>
          </div>
        ) : null}
      </dl>
      <p className="admin-log-event-detail__note" role="note">
        stack trace·credential·SQL parameter는 표시하지 않습니다.
      </p>
    </aside>
  );
}
