import { useCallback, useMemo, useState } from 'react';
import { useQueries } from '@tanstack/react-query';
import { getPolicyById } from '@/api/policies';
import AppleCalendarLayout from '@/components/calendar/AppleCalendarLayout';
import CalendarDayDetailDialog from '@/components/calendar/CalendarDayDetailDialog';
import CalendarDayView from '@/components/calendar/CalendarDayView';
import CalendarEventDetailDialog from '@/components/calendar/CalendarEventDetailDialog';
import CalendarMonthView from '@/components/calendar/CalendarMonthView';
import CalendarToolbar from '@/components/calendar/CalendarToolbar';
import CalendarWeekView from '@/components/calendar/CalendarWeekView';
import CalendarYearView from '@/components/calendar/CalendarYearView';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';
import { useFavorites } from '@/hooks/useFavorites';
import type { PolicyCategory, PolicyDto } from '@/types/policy';
import {
  createDefaultEnabledCategories,
  policyMatchesCategoryFilters,
} from '@/utils/calendarCategoryTheme';
import {
  collectCalendarPolicyEvents,
  groupCalendarEventsByDate,
  type CalendarPolicyEvent,
} from '@/utils/calendarPolicyEvents';
import { getKstDateString } from '@/utils/policyDeadline';
import type { CalendarViewMode } from '@/utils/calendarViewNavigation';
import {
  getViewMonthFromFocusDate,
  shiftFocusDate,
} from '@/utils/calendarViewNavigation';

type CalendarScope = 'favorites' | 'all';

export default function CalendarPage() {
  const todayKst = getKstDateString();
  const [scope, setScope] = useState<CalendarScope>('favorites');
  const [focusDate, setFocusDate] = useState(todayKst);
  const [viewMode, setViewMode] = useState<CalendarViewMode>('month');
  const [enabledCategories, setEnabledCategories] = useState<Set<PolicyCategory>>(
    createDefaultEnabledCategories,
  );
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<CalendarPolicyEvent | null>(null);
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

  const filteredPolicies = useMemo(
    () => policies.filter((policy) => policyMatchesCategoryFilters(policy, enabledCategories)),
    [policies, enabledCategories],
  );

  const eventsByDate = useMemo(() => {
    const events = collectCalendarPolicyEvents(filteredPolicies);
    return groupCalendarEventsByDate(events);
  }, [filteredPolicies]);

  const hasAnyCalendarEvents = eventsByDate.size > 0;
  const { year: viewYear, month: viewMonth } = getViewMonthFromFocusDate(focusDate);

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

  const handleToggleCategory = useCallback((category: PolicyCategory) => {
    setEnabledCategories((previous) => {
      const next = new Set(previous);
      if (next.has(category)) {
        next.delete(category);
      } else {
        next.add(category);
      }
      return next;
    });
  }, []);

  const handleSelectDate = useCallback((date: string) => {
    setFocusDate(date);
    setSidebarOpen(false);
  }, []);

  const handleNavigate = useCallback(
    (direction: -1 | 1) => {
      setFocusDate((previous) => shiftFocusDate(previous, viewMode, direction));
    },
    [viewMode],
  );

  const handleToday = useCallback(() => {
    setFocusDate(todayKst);
  }, [todayKst]);

  const handleSelectMonth = useCallback((year: number, month: number) => {
    setFocusDate(`${year}-${String(month).padStart(2, '0')}-01`);
    setViewMode('month');
  }, []);

  const handleMiniPickerMonthChange = useCallback((year: number, month: number) => {
    setFocusDate((previous) => {
      const day = Number(previous.slice(8, 10));
      const clampedDay = Math.min(day, 28);
      return `${year}-${String(month).padStart(2, '0')}-${String(clampedDay).padStart(2, '0')}`;
    });
  }, []);

  const renderCalendarView = () => {
    switch (viewMode) {
      case 'day':
        return (
          <CalendarDayView
            focusDate={focusDate}
            todayYmd={todayKst}
            eventsByDate={eventsByDate}
            onSelectEvent={setSelectedEvent}
          />
        );
      case 'week':
        return (
          <CalendarWeekView
            focusDate={focusDate}
            todayYmd={todayKst}
            eventsByDate={eventsByDate}
            onSelectDate={setFocusDate}
            onSelectEvent={setSelectedEvent}
          />
        );
      case 'year':
        return (
          <CalendarYearView
            year={viewYear}
            eventsByDate={eventsByDate}
            onSelectMonth={handleSelectMonth}
          />
        );
      case 'month':
      default:
        return (
          <CalendarMonthView
            year={viewYear}
            month={viewMonth}
            todayYmd={todayKst}
            focusDate={focusDate}
            eventsByDate={eventsByDate}
            onSelectDate={setFocusDate}
            onSelectEvent={setSelectedEvent}
            onOpenDay={(date, events) => setSelectedDay({ date, events })}
          />
        );
    }
  };

  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">마감 달력</h1>
        <p className="greeting__subtitle">
          신청 시작·마감일이 있는 정책을 macOS 캘린더 스타일 2패널 UI로 확인합니다. 상시·일정
          미정 정책은 포함하지 않습니다. 날짜 기준은 Asia/Seoul(KST)입니다.
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

      {!isLoading && !isError && policies.length > 0 ? (
        <AppleCalendarLayout
          sidebarOpen={sidebarOpen}
          onSidebarToggle={() => setSidebarOpen((previous) => !previous)}
          enabledCategories={enabledCategories}
          onToggleCategory={handleToggleCategory}
          miniPickerYear={viewYear}
          miniPickerMonth={viewMonth}
          todayYmd={todayKst}
          focusDate={focusDate}
          onMiniPickerMonthChange={handleMiniPickerMonthChange}
          onSelectDate={handleSelectDate}
          toolbar={
            <CalendarToolbar
              focusDate={focusDate}
              viewMode={viewMode}
              onViewModeChange={setViewMode}
              onNavigate={handleNavigate}
              onToday={handleToday}
            />
          }
        >
          {renderCalendarView()}
        </AppleCalendarLayout>
      ) : null}

      {selectedEvent ? (
        <CalendarEventDetailDialog
          event={selectedEvent}
          onClose={() => setSelectedEvent(null)}
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
