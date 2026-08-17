import { Link } from 'react-router';
import CollectionRunStatusBadge from '@/components/admin/CollectionRunStatusBadge';
import LoadingState from '@/components/common/LoadingState';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import type { CollectionRunQualitySummary } from '@/hooks/useAdminQualityRunSummaries';
import {
  DATA_QUALITY_COMPARE_METRICS,
  formatAdminMetricCount,
  readAdminQualityMetricValue,
  shouldLinkMetricDrillDown,
  buildCollectionRunDetailDrillDownUrl,
  buildAdminLogsDrillDownUrl,
  shouldShowLogsDrillDown,
} from '@/utils/adminDashboard';
import {
  formatAdminTimestamp,
  getCollectionRunTypeLabel,
} from '@/utils/collectionRunDisplay';

interface CollectionRunQualityTableProps {
  summaries: CollectionRunQualitySummary[];
  isDetailsLoading: boolean;
}

function renderMetricCell(
  summary: CollectionRunQualitySummary,
  metricKey: (typeof DATA_QUALITY_COMPARE_METRICS)[number]['key'],
) {
  const { listItem, detail } = summary;

  if (detail) {
    const value = readAdminQualityMetricValue(detail, metricKey);
    const formatted = formatAdminMetricCount(value);

    if (shouldLinkMetricDrillDown(metricKey, value)) {
      return (
        <Link
          to={buildCollectionRunDetailDrillDownUrl(listItem.run_id)}
          className="admin-quality-table__metric-link"
        >
          {formatted}
        </Link>
      );
    }

    return formatted;
  }

  if (metricKey === 'failed_count') {
    return formatAdminMetricCount(listItem.failed_count);
  }

  if (metricKey === 'inserted_count') {
    return formatAdminMetricCount(listItem.inserted_count);
  }

  if (metricKey === 'updated_count') {
    return formatAdminMetricCount(listItem.updated_count);
  }

  return summary.detailLoading ? '…' : '—';
}

export default function CollectionRunQualityTable({
  summaries,
  isDetailsLoading,
}: CollectionRunQualityTableProps) {
  if (summaries.length === 0) {
    return (
      <p className="state-message state-message--empty" role="status">
        비교할 수집 실행 기록이 없습니다.
      </p>
    );
  }

  return (
    <>
      {isDetailsLoading ? (
        <LoadingState message="회차별 품질 집계를 불러오는 중입니다." />
      ) : null}

      <div className="admin-quality-table-wrap">
        <table className="admin-quality-table">
          <caption className="admin-quality-table__caption">
            최근 수집 회차 품질 집계 (건별 실패·중복 후보 목록은 Backend API
            확정 후 연결)
          </caption>
          <thead>
            <tr>
              <th scope="col">상태</th>
              <th scope="col">시작 시각</th>
              <th scope="col">유형</th>
              {DATA_QUALITY_COMPARE_METRICS.map((metric) => (
                <th key={metric.key} scope="col">
                  {metric.label}
                </th>
              ))}
              <th scope="col">바로가기</th>
            </tr>
          </thead>
          <tbody>
            {summaries.map((summary) => {
              const { listItem, detail } = summary;
              const showLogsLink = detail ? shouldShowLogsDrillDown(detail) : false;

              return (
                <tr key={listItem.run_id}>
                  <td>
                    <CollectionRunStatusBadge
                      status={listItem.status}
                      isStale={listItem.is_stale}
                    />
                  </td>
                  <td>{formatAdminTimestamp(listItem.started_at)}</td>
                  <td>{getCollectionRunTypeLabel(listItem.run_type)}</td>
                  {DATA_QUALITY_COMPARE_METRICS.map((metric) => (
                    <td key={metric.key}>{renderMetricCell(summary, metric.key)}</td>
                  ))}
                  <td>
                    <div className="admin-quality-table__actions">
                      <Link to={ADMIN_APP_ROUTES.runDetail(listItem.run_id)}>
                        실행 상세
                      </Link>
                      {showLogsLink ? (
                        <Link to={buildAdminLogsDrillDownUrl()}>Log</Link>
                      ) : null}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </>
  );
}
