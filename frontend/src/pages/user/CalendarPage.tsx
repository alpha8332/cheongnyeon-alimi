import { useMemo, useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import { getPolicyById } from '@/api/policies';
import CalendarDayDetailDialog from '@/components/calendar/CalendarDayDetailDialog';
import MonthlyCalendarGrid from '@/components/calendar/MonthlyCalendarGrid';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';
import { useFavorites } from '@/hooks/useFavorites';
import type { PolicyDto } from '@/types/policy';
import {
  collectCalendarPolicyEvents,
  groupCalendarEventsByDate,
  type CalendarPolicyEvent,
} from '@/utils/calendarPolicyEvents';
import { getKstDateString } from '@/utils/policyDeadline';

type CalendarScope = 'favorites' | 'all';

interface CalendarViewMonth {
  year: number;
  month: number;
}

function parseViewMonthFromToday(todayYmd: string): CalendarViewMonth {
  const [year, month] = todayYmd.split('-').map(Number);
  return { year, month };
}

export default function CalendarPage() {
  const todayKst = getKstDateString();
  const [scope, setScope] = useState<CalendarScope>('favorites');
  const [viewMonth, setViewMonth] = useState<CalendarViewMonth>(() =>
    parseViewMonthFromToday(todayKst),
  );
  const [selectedDay, setSelectedDay] = useState<{
    date: string;
    events: readonly CalendarPolicyEvent[];
  } | null>(null);

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

  const eventsByDate = useMemo(() => {
    const events = collectCalendarPolicyEvents(policies);
    return groupCalendarEventsByDate(events);
  }, [policies]);

  const hasAnyCalendarEvents = eventsByDate.size > 0;

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
          신청 시작·마감일이 있는 정책을 월간 달력으로 확인합니다. 상시·일정 미정
          정책은 포함하지 않습니다. 날짜 기준은 Asia/Seoul(KST)입니다.
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

      {!isLoading && !isError && policies.length > 0 && !hasAnyCalendarEvents ? (
        <EmptyState message="표시할 신청 시작·마감일이 있는 정책이 없습니다." />
      ) : null}

      {!isLoading && !isError ? (
        <MonthlyCalendarGrid
          year={viewMonth.year}
          month={viewMonth.month}
          todayYmd={todayKst}
          eventsByDate={eventsByDate}
          onMonthChange={(year, month) => setViewMonth({ year, month })}
          onOpenDay={(date, events) => setSelectedDay({ date, events })}
        />
      ) : null}

      {selectedDay ? (
        <CalendarDayDetailDialog
          date={selectedDay.date}
          events={selectedDay.events}
          onClose={() => setSelectedDay(null)}
        />
      ) : null}
    </div>
  );
}
