import { useEffect, useMemo, useRef, useState } from 'react';
import { AdminApiError } from '@/api/adminApiError';
import AdminLogEventFilters from '@/components/admin/AdminLogEventFilters';
import AdminLogEventTable, {
  AdminLogEventDetailPanel,
} from '@/components/admin/AdminLogEventTable';
import AdminLogMaintenanceActions from '@/components/admin/AdminLogMaintenanceActions';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import {
  useAdminLogEventListQuery,
  useAdminLogFileListQuery,
} from '@/hooks/useAdminObservabilityQuery';
import { useAdminSession } from '@/hooks/useAdminSession';
import { useAdminUnauthorizedRedirect } from '@/hooks/useAdminUnauthorizedRedirect';
import {
  getAdminLogEventKey,
  type AdminLogEventListResponse,
} from '@/types/adminLog';
import {
  EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT,
  toAdminLogEventListQueryFromDraft,
  type AdminLogEventFilterDraft,
} from '@/utils/adminLogEventFilters';

const PAGE_SIZE = 10;

export default function AdminLogsPage() {
  const { accessToken } = useAdminSession();
  const refreshButtonRef = useRef<HTMLButtonElement>(null);
  const [filterDraft, setFilterDraft] = useState<AdminLogEventFilterDraft>(
    EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT,
  );
  const [appliedFilters, setAppliedFilters] = useState<AdminLogEventFilterDraft>(
    EMPTY_ADMIN_LOG_EVENT_FILTER_DRAFT,
  );
  const [page, setPage] = useState(1);
  const [selectedEventId, setSelectedEventId] = useState<string | null>(null);
  const [cachedEventResponse, setCachedEventResponse] =
    useState<AdminLogEventListResponse | null>(null);

  const eventQuery = useMemo(
    () => toAdminLogEventListQueryFromDraft(appliedFilters, page, PAGE_SIZE),
    [appliedFilters, page],
  );

  const {
    data: fileResponse,
    refetch: refetchFiles,
    isFetching: isFilesFetching,
  } = useAdminLogFileListQuery(accessToken);
  const {
    data: eventResponse,
    isLoading,
    isError,
    error,
    refetch: refetchEvents,
    isFetching: isEventsFetching,
  } = useAdminLogEventListQuery(eventQuery, accessToken);

  useEffect(() => {
    if (!eventResponse) return;
    // eslint-disable-next-line react-hooks/set-state-in-effect -- intentional stale-while-error UX
    setCachedEventResponse(eventResponse);
  }, [eventResponse]);

  const { redirectToLogin } = useAdminUnauthorizedRedirect({
    error,
    onRetry: () => void refetchEvents(),
  });

  const displayEventResponse = eventResponse ?? cachedEventResponse;
  const hasEventItems = (displayEventResponse?.events.length ?? 0) > 0;
  const showEventLoading = isLoading && !hasEventItems;
  const totalPages = displayEventResponse
    ? Math.max(1, Math.ceil(displayEventResponse.total / displayEventResponse.limit))
    : 1;
  const selectedEvent =
    displayEventResponse?.events.find(
      (item) => getAdminLogEventKey(item) === selectedEventId,
    ) ?? null;

  const errorMessage =
    error instanceof AdminApiError
      ? error.detail
      : error instanceof Error
        ? error.message
        : '로그 이벤트를 불러오지 못했습니다.';

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
    void Promise.all([refetchFiles(), refetchEvents()]);
  };

  return (
    <div className="admin-logs-page">
      <header className="admin-page-header">
        <div>
          <p className="admin-page-header__eyebrow">Data operations</p>
          <h1 className="admin-page-header__title">로그 조회 및 정리</h1>
          <p className="admin-page-header__description">
            구조화된 이벤트만 읽기 전용으로 조회하고, 보관 로그만 감사 기록과 함께 정리합니다.
          </p>
        </div>
      </header>

      <section className="admin-log-files" aria-label="로그 파일 목록">
        <h2>로그 파일</h2>
        {fileResponse?.files.map((file) => (
          <p key={file.file_id}>
            <strong>{file.filename}</strong> · {file.is_active ? 'active' : 'archive'} ·{' '}
            {file.size_bytes.toLocaleString()} bytes
          </p>
        ))}
        {isFilesFetching ? <p role="status">파일 목록 새로고침 중…</p> : null}
      </section>

      <AdminLogMaintenanceActions
        files={fileResponse?.files ?? []}
        accessToken={accessToken}
        onMaintenanceComplete={handleRefresh}
        onUnauthorized={redirectToLogin}
      />

      <AdminLogEventFilters
        draft={filterDraft}
        onChange={setFilterDraft}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
        onRefresh={handleRefresh}
        isRefreshing={isEventsFetching}
        refreshButtonRef={refreshButtonRef}
      />

      {showEventLoading ? <LoadingState message="로그 이벤트를 불러오는 중입니다." /> : null}
      {isError && !(error instanceof AdminApiError) ? (
        <ErrorState message={errorMessage} />
      ) : null}
      {!showEventLoading && !isError && eventResponse?.events.length === 0 ? (
        <p className="state-message state-message--empty" role="status">
          조건에 맞는 로그 이벤트가 없습니다.
        </p>
      ) : null}

      <div className="admin-logs-page__layout">
        {hasEventItems && displayEventResponse ? (
          <>
            <AdminLogEventTable
              items={displayEventResponse.events}
              selectedEventId={selectedEventId}
              onSelectEvent={setSelectedEventId}
            />
            <nav className="collection-run-pagination" aria-label="로그 이벤트 페이지">
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page <= 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                이전
              </button>
              <span className="collection-run-pagination__status" role="status">
                {displayEventResponse.page} / {totalPages} 페이지
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                disabled={page >= totalPages}
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              >
                다음
              </button>
            </nav>
          </>
        ) : null}

        <AdminLogEventDetailPanel
          event={selectedEvent}
          onClose={() => setSelectedEventId(null)}
        />
      </div>
    </div>
  );
}
