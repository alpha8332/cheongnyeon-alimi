import { Link } from 'react-router';
import CollectionRunQualityTable from '@/components/admin/CollectionRunQualityTable';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { AdminApiError } from '@/api/adminApiError';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminQualityRunSummaries } from '@/hooks/useAdminQualityRunSummaries';
import { useAdminSession } from '@/hooks/useAdminSession';
import { useAdminUnauthorizedRedirect } from '@/hooks/useAdminUnauthorizedRedirect';

export default function DataQualityPage() {
  const { accessToken } = useAdminSession();
  const {
    listResponse,
    summaries,
    isListLoading,
    isListError,
    listError,
    isDetailsLoading,
    refetchAll,
  } = useAdminQualityRunSummaries(accessToken);

  useAdminUnauthorizedRedirect({
    error: listError,
    onRetry: () => void refetchAll(),
  });

  const errorMessage =
    listError instanceof AdminApiError
      ? listError.detail
      : listError instanceof Error
        ? listError.message
        : '데이터 품질 요약을 불러오지 못했습니다.';

  return (
    <div className="page admin-quality-page">
      <header className="greeting">
        <h1 className="greeting__title">데이터 품질</h1>
        <p className="greeting__subtitle">
          최근 CollectionRun 회차별 실패·무효·중복 집계 비교 (Backend 집계 API
          범위)
        </p>
      </header>

      <nav className="admin-dashboard-quick-links" aria-label="관련 화면">
        <Link to={ADMIN_APP_ROUTES.runs} className="admin-dashboard-quick-links__item">
          수집 실행 기록
        </Link>
        <Link to={ADMIN_APP_ROUTES.dashboard} className="admin-dashboard-quick-links__item">
          관리 대시보드
        </Link>
        <Link to={ADMIN_APP_ROUTES.logs} className="admin-dashboard-quick-links__item">
          구조화 Log
        </Link>
      </nav>

      {isListLoading ? (
        <LoadingState message="수집 실행 목록을 불러오는 중입니다." />
      ) : null}

      {isListError && !(listError instanceof AdminApiError) ? (
        <ErrorState message={errorMessage} />
      ) : null}

      {!isListLoading && !isListError && listResponse ? (
        <CollectionRunQualityTable
          summaries={summaries}
          isDetailsLoading={isDetailsLoading}
        />
      ) : null}
    </div>
  );
}
