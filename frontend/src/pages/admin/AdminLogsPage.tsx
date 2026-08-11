import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router';
import AdminLogEventFilters from '@/components/admin/AdminLogEventFilters';
import {
  EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT,
  toAdminLogEventListQueryFromDraft,
  type AdminLogEventFilterDraft,
} from '@/utils/adminLogEventFilters';
import AdminLogEventTable, {
  AdminLogEventDetailPanel,
} from '@/components/admin/AdminLogEventTable';
import AdminLogMaintenanceActions from '@/components/admin/AdminLogMaintenanceActions';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';
import {
  useAdminLogEventListQuery,
  useAdminLogFileListQuery,
} from '@/hooks/useAdminObservabilityQuery';
import { findMockAdminLogEventById } from '@/mocks/adminObservabilityFixtures';
import { clearAdminSession } from '@/utils/adminSessionStorage';

const PAGE_SIZE = 10;

export default function AdminLogsPage() {
  const navigate = useNavigate();
  const { accessToken, logout } = useAdminSession();
  const [filterDraft, setFilterDraft] = useState<AdminLogEventFilterDraft>(
    EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT,
  );
  const [appliedFilters, setAppliedFilters] = useState<AdminLogEventFilterDraft>(
    EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT,
  );
  const [page, setPage] = useState(1);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);

  const eventQuery = useMemo(
    () => toAdminLogEventListQueryFromDraft(appliedFilters, page, PAGE_SIZE),
    [appliedFilters, page],
  );

  const {
    data: fileResponse,
    refetch: refetchFiles,
    isFetching: isFilesFetching,
  } = useAdminLogFileListQuery({ page: 1, size: 20 }, accessToken);

  const {
    data: eventResponse,
    isLoading,
    isError,
    error,
    refetch: refetchEvents,
    isFetching: isEventsFetching,
  } = useAdminLogEventListQuery(eventQuery, accessToken);

  useEffect(() => {
    if (!(error instanceof AdminApiError) || error.status !== 401) {
      return;
    }

    clearAdminSession();
    logout();
    navigate(ADMIN_APP_ROUTES.login, { replace: true });
  }, [error, logout, navigate]);

  const errorMessage =
    error instanceof AdminApiError
      ? error.detail
      : error instanceof Error
        ? error.message
        : 'Log event를 불러오지 못했습니다.';

  const selectedEvent =
    eventResponse?.items.find((item) => item.event_id === selectedEventId) ??
    null;
  const selectedEventDetail = selectedEventId
    ? findMockAdminLogEventById(selectedEventId)
    : undefined;
  const selectedEventMessage = selectedEventDetail?.message ?? null;

  const handleApplyFilters = () => {
    setAppliedFilters(filterDraft);
    setPage(1);
    setSelectedEventId(null);
  };

  const handleResetFilters = () => {
    setFilterDraft(EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT);
    setAppliedFilters(EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT);
    setPage(1);
    setSelectedEventId(null);
  };

  const handleRefresh = () => {
    void refetchFiles();
    void refetchEvents();
  };

  const handleMaintenanceComplete = () => {
    void refetchFiles();
    void refetchEvents();
  };

  const handleUnauthorized = () => {
    clearAdminSession();
    logout();
    navigate(ADMIN_APP_ROUTES.login, { replace: true });
  };

  return (
    <div className="page admin-logs-page">
      <header className="greeting">
        <h1 className="greeting__title">구조화 Log</h1>
        <p className="greeting__subtitle">
          log file·event read-only 조회와 archive maintenance (Mock-first)
        </p>
      </header>

      <section className="admin-log-files-summary" aria-label="Log files">
        <h2 className="admin-log-files-summary__title">Log files</h2>
        {isFilesFetching ? <p role="status">파일 목록 갱신 중…</p> : null}
        <ul className="admin-log-files-summary__list">
          {(fileResponse?.items ?? []).map((file) => (
            <li key={file.file_id}>
              <strong>{file.filename}</strong> · {file.status} · {file.file_id}
            </li>
          ))}
        </ul>
      </section>

      <AdminLogMaintenanceActions
        files={fileResponse?.items ?? []}
        accessToken={accessToken}
        onMaintenanceComplete={handleMaintenanceComplete}
        onUnauthorized={handleUnauthorized}
      />

      <AdminLogEventFilters
        draft={filterDraft}
        onChange={setFilterDraft}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
        onRefresh={handleRefresh}
        isRefreshing={isEventsFetching}
      />

      {isLoading ? <LoadingState message="Log event를 불러오는 중입니다." /> : null}
      {isError ? <ErrorState message={errorMessage} /> : null}

      {!isLoading && !isError && eventResponse && eventResponse.items.length === 0 ? (
        <p className="state-message state-message--empty" role="status">
          조건에 맞는 log event가 없습니다.
        </p>
      ) : null}

      <div className="admin-logs-page__layout">
        {!isLoading && !isError && eventResponse && eventResponse.items.length > 0 ? (
          <>
            <AdminLogEventTable
              items={eventResponse.items}
              selectedEventId={selectedEventId}
              onSelectEvent={setSelectedEventId}
            />

            <nav className="collection-run-pagination" aria-label="Log event pagination">
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                이전
              </button>
              <span className="collection-run-pagination__status" role="status">
                {eventResponse.page} / {eventResponse.pages} 페이지
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page >= eventResponse.pages}
                onClick={() =>
                  setPage((current) => Math.min(eventResponse.pages, current + 1))
                }
              >
                다음
              </button>
            </nav>
          </>
        ) : null}

        <AdminLogEventDetailPanel
          event={selectedEvent}
          message={selectedEventMessage}
          onClose={() => setSelectedEventId(null)}
        />
      </div>
    </div>
  );
}
