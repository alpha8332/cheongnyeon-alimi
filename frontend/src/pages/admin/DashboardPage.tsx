import { Link } from 'react-router';
import AdminMetricCard from '@/components/admin/AdminMetricCard';
import CollectionRunStatusBadge from '@/components/admin/CollectionRunStatusBadge';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';
import { useAdminUnauthorizedRedirect } from '@/hooks/useAdminUnauthorizedRedirect';
import {
  useCollectionRunDetailQuery,
  useCollectionRunsQuery,
} from '@/hooks/useCollectionRunsQuery';
import {
  DASHBOARD_SUMMARY_METRICS,
  buildAdminLogsDrillDownUrl,
  buildCollectionRunDetailDrillDownUrl,
  formatAdminMetricCount,
  getAdminMetricCardVariant,
  readAdminQualityMetricValue,
  shouldLinkMetricDrillDown,
  shouldShowLogsDrillDown,
} from '@/utils/adminDashboard';
import {
  formatAdminTimestamp,
  getCollectionRunTypeLabel,
  getCollectionRunTriggerTypeLabel,
} from '@/utils/collectionRunDisplay';

export default function DashboardPage() {
  const { accessToken } = useAdminSession();

  const {
    data: listResponse,
    isLoading: isListLoading,
    isError: isListError,
    error: listError,
    refetch: refetchList,
  } = useCollectionRunsQuery({ page: 1, size: 1 }, accessToken);

  const latestRun = listResponse?.items[0] ?? null;
  const latestRunId = latestRun?.run_id ?? '';

  const {
    data: latestRunDetail,
    isLoading: isDetailLoading,
    isError: isDetailError,
    error: detailError,
    refetch: refetchDetail,
  } = useCollectionRunDetailQuery(latestRunId, accessToken);

  const combinedError = listError ?? detailError;
  const isLoading = isListLoading || (latestRunId.length > 0 && isDetailLoading);
  const hasNonAdminError =
    (isListError && !(listError instanceof AdminApiError)) ||
    (isDetailError && !(detailError instanceof AdminApiError));

  const handleRetry = () => {
    void refetchList();
    if (latestRunId.length > 0) {
      void refetchDetail();
    }
  };

  useAdminUnauthorizedRedirect({
    error: combinedError,
    onRetry: handleRetry,
  });

  const errorMessage =
    combinedError instanceof AdminApiError
      ? combinedError.detail
      : combinedError instanceof Error
        ? combinedError.message
        : '대시보드 데이터를 불러오지 못했습니다.';

  return (
    <div className="page admin-dashboard-page">
      <header className="greeting">
        <h1 className="greeting__title">관리 대시보드</h1>
      </header>

      {isLoading ? (
        <LoadingState message="최신 수집 실행을 불러오는 중입니다." />
      ) : null}

      {hasNonAdminError ? <ErrorState message={errorMessage} /> : null}

      {!isLoading && !isListError && !latestRun ? (
        <p className="state-message state-message--empty" role="status">
          아직 수집 실행 기록이 없습니다.{' '}
          <Link to={ADMIN_APP_ROUTES.runs}>실행 기록</Link>에서 수동 실행을
          요청할 수 있습니다.
        </p>
      ) : null}

      {!isLoading && latestRun ? (
        <section className="admin-dashboard-latest-run" aria-labelledby="latest-run-heading">
          <div className="admin-dashboard-latest-run__header">
            <h2 id="latest-run-heading" className="admin-dashboard-section-title">
              최신 수집 실행
            </h2>
            <CollectionRunStatusBadge
              status={latestRun.status}
              isStale={latestRun.is_stale}
            />
          </div>

          <dl className="admin-dashboard-latest-run__meta">
            <div className="admin-dashboard-latest-run__meta-item">
              <dt>run_id</dt>
              <dd>
                <Link to={buildCollectionRunDetailDrillDownUrl(latestRun.run_id)}>
                  <code>{latestRun.run_id.slice(0, 8)}…</code>
                </Link>
              </dd>
            </div>
            <div className="admin-dashboard-latest-run__meta-item">
              <dt>source</dt>
              <dd>{latestRun.source_id ?? '—'}</dd>
            </div>
            <div className="admin-dashboard-latest-run__meta-item">
              <dt>유형 / trigger</dt>
              <dd>
                {getCollectionRunTypeLabel(latestRun.run_type)} /{' '}
                {getCollectionRunTriggerTypeLabel(latestRun.trigger_type)}
              </dd>
            </div>
            <div className="admin-dashboard-latest-run__meta-item">
              <dt>started_at</dt>
              <dd>{formatAdminTimestamp(latestRun.started_at)}</dd>
            </div>
            <div className="admin-dashboard-latest-run__meta-item">
              <dt>finished_at</dt>
              <dd>{formatAdminTimestamp(latestRun.finished_at)}</dd>
            </div>
          </dl>

          {latestRunDetail ? (
            <>
              <div className="admin-dashboard-metrics">
                {DASHBOARD_SUMMARY_METRICS.map((metric) => {
                  const value = readAdminQualityMetricValue(
                    latestRunDetail,
                    metric.key,
                  );
                  const drillDownUrl = shouldLinkMetricDrillDown(metric.key, value)
                    ? buildCollectionRunDetailDrillDownUrl(latestRun.run_id)
                    : undefined;

                  return (
                    <AdminMetricCard
                      key={metric.key}
                      label={metric.label}
                      value={formatAdminMetricCount(value)}
                      description={metric.description}
                      to={drillDownUrl}
                      variant={getAdminMetricCardVariant(metric.key, value)}
                    />
                  );
                })}
              </div>

              {shouldShowLogsDrillDown(latestRunDetail) ? (
                <p className="admin-dashboard-latest-run__logs-link">
                  <Link to={buildAdminLogsDrillDownUrl()}>
                    실패·부분 실패 관련 Log 보기 →
                  </Link>
                </p>
              ) : null}
            </>
          ) : isDetailLoading ? (
            <LoadingState message="집계 상세를 불러오는 중입니다." />
          ) : isDetailError && !(detailError instanceof AdminApiError) ? (
            <ErrorState message={errorMessage} />
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
