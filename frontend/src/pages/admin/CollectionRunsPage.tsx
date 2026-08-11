import { useEffect, useMemo, useState } from 'react';
import { Link, useNavigate } from 'react-router';
import CollectionRunFilters from '@/components/admin/CollectionRunFilters';
import CollectionRunStatusBadge from '@/components/admin/CollectionRunStatusBadge';
import ManualCollectionRunTrigger from '@/components/admin/ManualCollectionRunTrigger';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';
import { useCollectionRunsQuery } from '@/hooks/useCollectionRunsQuery';
import type { CollectionRunTriggerResponse } from '@/types/collectionRun';
import {
  formatAdminTimestamp,
  formatCollectionRunCounts,
  getCollectionRunTriggerTypeLabel,
  getCollectionRunTypeLabel,
} from '@/utils/collectionRunDisplay';
import {
  EMPTY_COLLECTION_RUN_FILTER_DRAFT,
  toCollectionRunListQueryFromDraft,
  type CollectionRunFilterDraft,
} from '@/utils/collectionRunFilters';
import { clearAdminSession } from '@/utils/adminSessionStorage';

const PAGE_SIZE = 10;

export default function CollectionRunsPage() {
  const navigate = useNavigate();
  const { accessToken, logout } = useAdminSession();
  const [filterDraft, setFilterDraft] = useState<CollectionRunFilterDraft>(
    EMPTY_COLLECTION_RUN_FILTER_DRAFT,
  );
  const [appliedFilters, setAppliedFilters] = useState<CollectionRunFilterDraft>(
    EMPTY_COLLECTION_RUN_FILTER_DRAFT,
  );
  const [page, setPage] = useState(1);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const query = useMemo(
    () => toCollectionRunListQueryFromDraft(appliedFilters, page, PAGE_SIZE),
    [appliedFilters, page],
  );

  const { data: response, isLoading, isError, error, refetch } =
    useCollectionRunsQuery(query, accessToken);

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
        : '실행 기록을 불러오지 못했습니다.';

  const hasRunningRun = (response?.items ?? []).some(
    (item) => item.status === 'running',
  );

  const handleApplyFilters = () => {
    setAppliedFilters(filterDraft);
    setPage(1);
  };

  const handleResetFilters = () => {
    setFilterDraft(EMPTY_COLLECTION_RUN_FILTER_DRAFT);
    setAppliedFilters(EMPTY_COLLECTION_RUN_FILTER_DRAFT);
    setPage(1);
  };

  const handleManualTriggered = (triggerResponse: CollectionRunTriggerResponse) => {
    setSuccessMessage(
      `수동 실행을 요청했습니다 (run_id: ${triggerResponse.run_id.slice(0, 8)}…).`,
    );
    void refetch();
  };

  const handleUnauthorized = () => {
    clearAdminSession();
    logout();
    navigate(ADMIN_APP_ROUTES.login, { replace: true });
  };

  return (
    <div className="page collection-runs-page">
      <header className="greeting">
        <h1 className="greeting__title">수집 실행 기록</h1>
        <p className="greeting__subtitle">
          CollectionRun 실행 이력·필터·pagination (Backend DTO subset only)
        </p>
      </header>

      <ManualCollectionRunTrigger
        accessToken={accessToken}
        disabled={hasRunningRun}
        disabledReason={
          hasRunningRun
            ? '실행 중인 run이 있어 수동 실행을 일시 중지했습니다.'
            : undefined
        }
        onTriggered={handleManualTriggered}
        onUnauthorized={handleUnauthorized}
      />

      {successMessage ? (
        <p className="collection-runs-page__success" role="status">
          {successMessage}
        </p>
      ) : null}

      <CollectionRunFilters
        draft={filterDraft}
        onChange={setFilterDraft}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
      />

      {isLoading ? (
        <LoadingState message="실행 기록을 불러오는 중입니다." />
      ) : null}

      {isError ? <ErrorState message={errorMessage} /> : null}

      {!isLoading && !isError && response && response.items.length === 0 ? (
        <p className="state-message state-message--empty" role="status">
          조건에 맞는 실행 기록이 없습니다.
        </p>
      ) : null}

      {!isLoading && !isError && response && response.items.length > 0 ? (
        <>
          <div className="collection-run-table-wrap">
            <table className="collection-run-table">
              <caption className="collection-run-table__caption">
                CollectionRun 실행 기록 ({response.total}건)
              </caption>
              <thead>
                <tr>
                  <th scope="col">상태</th>
                  <th scope="col">run_id</th>
                  <th scope="col">source</th>
                  <th scope="col">type / trigger</th>
                  <th scope="col">started_at</th>
                  <th scope="col">counts</th>
                </tr>
              </thead>
              <tbody>
                {response.items.map((item) => (
                  <tr key={item.run_id}>
                    <td>
                      <CollectionRunStatusBadge
                        status={item.status}
                        isStale={item.is_stale}
                      />
                    </td>
                    <td>
                      <Link to={ADMIN_APP_ROUTES.runDetail(item.run_id)}>
                        {item.run_id.slice(0, 8)}…
                      </Link>
                    </td>
                    <td>{item.source_id ?? '—'}</td>
                    <td>
                      {getCollectionRunTypeLabel(item.run_type)} /{' '}
                      {getCollectionRunTriggerTypeLabel(item.trigger_type)}
                    </td>
                    <td>{formatAdminTimestamp(item.started_at)}</td>
                    <td>
                      {formatCollectionRunCounts(
                        item.inserted_count,
                        item.updated_count,
                        item.failed_count,
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <nav
            className="collection-run-pagination"
            aria-label="실행 기록 pagination"
          >
            <button
              type="button"
              className="btn btn-secondary"
              disabled={page <= 1}
              onClick={() => setPage((current) => Math.max(1, current - 1))}
            >
              이전
            </button>
            <span className="collection-run-pagination__status" role="status">
              {response.page} / {response.pages} 페이지
            </span>
            <button
              type="button"
              className="btn btn-secondary"
              disabled={page >= response.pages}
              onClick={() =>
                setPage((current) => Math.min(response.pages, current + 1))
              }
            >
              다음
            </button>
          </nav>
        </>
      ) : null}
    </div>
  );
}
