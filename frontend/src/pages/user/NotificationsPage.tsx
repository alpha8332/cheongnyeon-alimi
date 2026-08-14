import { useMemo } from 'react';
import { Link } from 'react-router';
import { useQueries } from '@tanstack/react-query';
import { getPolicyById } from '@/api/policies';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { useFavorites } from '@/hooks/useFavorites';
import { buildFavoriteDeadlineAlerts } from '@/utils/favoriteDeadlineAlerts';
import { buildProgramDetailRoutePath } from '@/utils/policyDetailNavigation';

export default function NotificationsPage() {
  const { favorites } = useFavorites();

  const policyQueries = useQueries({
    queries: favorites.map((policyId) => ({
      queryKey: ['policy', policyId, { include_partial: true }],
      queryFn: () => getPolicyById(policyId, true),
      enabled: policyId > 0,
    })),
  });

  const resolvedPolicies = useMemo(() => {
    const policies = [];
    for (const query of policyQueries) {
      if (query.data) {
        policies.push(query.data);
      }
    }
    return policies;
  }, [policyQueries]);

  const alerts = useMemo(
    () => buildFavoriteDeadlineAlerts(resolvedPolicies, favorites),
    [resolvedPolicies, favorites],
  );

  const isLoading =
    favorites.length > 0 && policyQueries.some((query) => query.isLoading);
  const isError =
    favorites.length > 0 &&
    policyQueries.some((query) => query.isError) &&
    resolvedPolicies.length === 0;

  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">알림</h1>
        <p className="greeting__subtitle">
          북마크한 정책 중 신청 마감이 임박(D-7 이내)한 항목만 이 앱 화면에
          표시합니다. 외부 push·이메일·Service Worker 알림은 사용하지 않습니다.
        </p>
      </header>

      {isLoading ? <LoadingState message="알림 대상 정책을 불러오는 중입니다." /> : null}

      {!isLoading && isError ? (
        <ErrorState message="알림 대상 정책을 불러오지 못했습니다." />
      ) : null}

      {!isLoading && !isError && favorites.length === 0 ? (
        <EmptyState message="북마크한 정책이 없습니다. 마감 임박 알림은 북마크한 정책에만 표시됩니다." />
      ) : null}

      {!isLoading && !isError && favorites.length > 0 && alerts.length === 0 ? (
        <EmptyState message="마감 임박 알림이 없습니다. 상시·일정 미정·D-7 초과 정책은 알림에 포함되지 않습니다." />
      ) : null}

      {!isLoading && alerts.length > 0 ? (
        <ul className="notification-alert-list" aria-label="마감 임박 알림 목록">
          {alerts.map((alert) => (
            <li key={alert.policyId} className="notification-alert-list__item">
              <div className="notification-alert-list__header">
                <span className="notification-alert-list__badge">{alert.label}</span>
                <span className="notification-alert-list__date">{alert.applicationEnd}</span>
              </div>
              <Link
                className="notification-alert-list__title"
                to={buildProgramDetailRoutePath(alert.policyId, {
                  includePartial: true,
                })}
              >
                {alert.title}
              </Link>
              <p className="notification-alert-list__copy">
                북마크한 정책의 신청 마감이 임박했습니다. 자격 충족을 확정하지
                않으니 원문을 확인하세요.
              </p>
            </li>
          ))}
        </ul>
      ) : null}

      <p className="hint-text" style={{ marginTop: '24px' }}>
        <Link to="/calendar">마감 달력</Link>에서 북마크·전체 정책 마감일을 볼 수
        있습니다.
      </p>
    </div>
  );
}
