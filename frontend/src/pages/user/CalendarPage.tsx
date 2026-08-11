import { useMemo, useState } from 'react';
import { Link } from 'react-router';
import { useQueries } from '@tanstack/react-query';
import { getPolicyById } from '@/api/policies';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';
import { useFavorites } from '@/hooks/useFavorites';
import type { PolicyDto } from '@/types/policy';
import { buildProgramDetailRoutePath } from '@/utils/policyDetailNavigation';
import {
  getDDayLabel,
  getKstDateString,
  groupPoliciesByApplicationEnd,
} from '@/utils/policyDeadline';

type CalendarScope = 'favorites' | 'all';

function sortDates(dates: Iterable<string>): string[] {
  return [...dates].sort((left, right) => left.localeCompare(right));
}

export default function CalendarPage() {
  const [scope, setScope] = useState<CalendarScope>('favorites');
  const { favorites } = useFavorites();

  const favoriteQueries = useQueries({
    queries: favorites.map((policyId) => ({
      queryKey: ['policy', policyId, { include_partial: true }],
      queryFn: () => getPolicyById(policyId, true),
      enabled: scope === 'favorites' && policyId > 0,
    })),
  });

  const allPoliciesQuery = usePoliciesQuery({
    page: 1,
    limit: 100,
    include_partial: true,
  });

  const policies = useMemo(() => {
    if (scope === 'favorites') {
      const resolved: PolicyDto[] = [];
      for (const query of favoriteQueries) {
        if (query.data) {
          resolved.push(query.data);
        }
      }
      return resolved;
    }

    return allPoliciesQuery.data?.items ?? [];
  }, [scope, favoriteQueries, allPoliciesQuery.data?.items]);

  const grouped = useMemo(
    () => groupPoliciesByApplicationEnd(policies),
    [policies],
  );

  const dates = useMemo(() => sortDates(grouped.keys()), [grouped]);
  const todayKst = getKstDateString();

  const isLoading =
    scope === 'favorites'
      ? favorites.length > 0 && favoriteQueries.some((query) => query.isLoading)
      : allPoliciesQuery.isLoading;
  const isError =
    scope === 'favorites'
      ? favorites.length > 0 &&
        favoriteQueries.some((query) => query.isError) &&
        policies.length === 0
      : allPoliciesQuery.isError;

  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">마감 달력</h1>
        <p className="greeting__subtitle">
          신청 종료일이 있는 정책만 표시합니다. 상시·일정 미정 정책은 달력에
          포함하지 않습니다. 날짜 기준은 Asia/Seoul(KST)입니다.
        </p>
      </header>

      <div className="calendar-scope-toggle" role="tablist" aria-label="달력 범위">
        <button
          type="button"
          role="tab"
          aria-selected={scope === 'favorites'}
          className={`calendar-scope-toggle__btn${scope === 'favorites' ? ' calendar-scope-toggle__btn--active' : ''}`}
          onClick={() => setScope('favorites')}
        >
          북마크
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={scope === 'all'}
          className={`calendar-scope-toggle__btn${scope === 'all' ? ' calendar-scope-toggle__btn--active' : ''}`}
          onClick={() => setScope('all')}
        >
          전체 정책
        </button>
      </div>

      {isLoading ? <LoadingState message="달력 데이터를 불러오는 중입니다." /> : null}

      {!isLoading && isError ? (
        <ErrorState message="달력 데이터를 불러오지 못했습니다." />
      ) : null}

      {!isLoading && !isError && scope === 'favorites' && favorites.length === 0 ? (
        <EmptyState message="북마크한 정책이 없습니다. 정책 카드에서 ☆ 버튼으로 추가해 보세요." />
      ) : null}

      {!isLoading && !isError && policies.length > 0 && dates.length === 0 ? (
        <EmptyState message="표시할 신청 마감일이 있는 정책이 없습니다." />
      ) : null}

      {!isLoading && !isError && dates.length > 0 ? (
        <div className="calendar-deadline-list">
          {dates.map((date) => {
            const items = grouped.get(date) ?? [];
            return (
              <section key={date} className="calendar-deadline-list__day">
                <h2 className="calendar-deadline-list__date">
                  {date}
                  {date === todayKst ? (
                    <span className="calendar-deadline-list__today-badge">오늘</span>
                  ) : null}
                </h2>
                <ul className="calendar-deadline-list__items">
                  {items.map((policy) => (
                    <li key={policy.id} className="calendar-deadline-list__item">
                      <Link
                        to={buildProgramDetailRoutePath(policy.id, {
                          includePartial: policy.data_quality_status === 'partial',
                        })}
                      >
                        {policy.title}
                      </Link>
                      <span className="calendar-deadline-list__dday">
                        {getDDayLabel(policy)}
                      </span>
                    </li>
                  ))}
                </ul>
              </section>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
