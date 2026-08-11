import { useMemo } from 'react';
import { useQueries } from '@tanstack/react-query';
import { getPolicyById } from '@/api/policies';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import { useFavorites } from '@/hooks/useFavorites';
import type { PolicyDto } from '@/types/policy';

export default function FavoritesPage() {
  const { favorites } = useFavorites();

  const policyQueries = useQueries({
    queries: favorites.map((policyId) => ({
      queryKey: ['policy', policyId, { include_partial: true }],
      queryFn: () => getPolicyById(policyId, true),
      enabled: policyId > 0,
    })),
  });

  const resolvedPolicies = useMemo(() => {
    const policies: PolicyDto[] = [];

    for (const query of policyQueries) {
      if (query.data) {
        policies.push(query.data);
      }
    }

    return policies;
  }, [policyQueries]);

  const isLoading =
    favorites.length > 0 && policyQueries.some((query) => query.isLoading);
  const isError =
    favorites.length > 0 &&
    policyQueries.some((query) => query.isError) &&
    resolvedPolicies.length === 0;
  const missingCount = favorites.length - resolvedPolicies.length;

  if (favorites.length === 0) {
    return (
      <div className="page">
        <header className="greeting">
          <h1 className="greeting__title">북마크</h1>
          <p className="greeting__subtitle">
            저장한 정책을 모아볼 수 있습니다. 브라우저에만 저장되며 서버와
            동기화되지 않습니다.
          </p>
        </header>
        <EmptyState message="저장한 정책이 없습니다. 정책 카드의 ☆ 버튼으로 북마크를 추가해 보세요." />
      </div>
    );
  }

  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">북마크</h1>
        <p className="greeting__subtitle">
          저장한 정책 {favorites.length}건 · 브라우저에만 저장됩니다
        </p>
      </header>

      {isLoading ? (
        <LoadingState message="북마크한 정책을 불러오는 중입니다." />
      ) : null}

      {!isLoading && isError ? (
        <ErrorState message="북마크한 정책을 불러오지 못했습니다." />
      ) : null}

      {!isLoading && !isError && resolvedPolicies.length === 0 ? (
        <EmptyState message="북마크한 정책을 찾지 못했습니다. 목록에서 북마크를 다시 확인해 주세요." />
      ) : null}

      {!isLoading && resolvedPolicies.length > 0 ? (
        <>
          {missingCount > 0 ? (
            <p className="favorites-page__note" role="status">
              {missingCount}건의 북마크는 현재 데이터에서 찾을 수 없습니다.
            </p>
          ) : null}
          <div className="cards-grid">
            {resolvedPolicies.map((policy) => (
              <PolicyCard key={policy.id} policy={policy} />
            ))}
          </div>
        </>
      ) : null}
    </div>
  );
}
