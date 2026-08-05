import { useMemo } from 'react';
import { useSearchParams } from 'react-router';
import SearchBar from '@/components/policySearch/SearchBar';
import SearchPagination from '@/components/policySearch/SearchPagination';
import PolicySearchResultCard from '@/components/policySearch/PolicySearchResultCard';
import PolicySearchEmptyShell from '@/components/policySearch/PolicySearchEmptyShell';
import PolicySearchErrorShell from '@/components/policySearch/PolicySearchErrorShell';
import PolicySearchLoadingShell from '@/components/policySearch/PolicySearchLoadingShell';
import InterpretedConditionChips from '@/components/policySearch/InterpretedConditionChips';
import { usePolicySearchQuery } from '@/hooks/usePolicySearchQuery';
import {
  buildInterpretedFilterChips,
  mapChipDimensionToFilterDimension,
} from '@/utils/interpretedConditionChips';
import {
  removePolicySearchFilter,
  updatePolicySearchFilter,
} from '@/utils/policySearchFilterMutations';
import type { InterpretedConditionDimension } from '@/types/policySearch';
import type { PolicySearchFilterValue } from '@/utils/policySearchFilterMutations';
import type { InterpretedFilterChip } from '@/utils/interpretedConditionChips';
import {
  isPolicySearchEmptyResults,
  mapPolicySearchEmptyResults,
  mapPolicySearchError,
} from '@/utils/policySearchErrors';
import {
  buildPolicySearchUrlParams,
  getPolicySearchTotalPages,
  hasPolicySearchQuery,
  isPolicySearchResponseCurrent,
  isPolicySearchUrlStateValid,
  parsePolicySearchUrl,
  toPolicySearchRequest,
  withPolicySearchPage,
} from '@/utils/policySearchUrl';

export default function PolicySearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlState = useMemo(
    () => parsePolicySearchUrl(searchParams),
    [searchParams],
  );
  const request = useMemo(() => toPolicySearchRequest(urlState), [urlState]);
  const shouldFetch = hasPolicySearchQuery(urlState);

  const {
    data,
    isLoading,
    isError,
    error,
    isFetching,
    refetch,
  } = usePolicySearchQuery(request);

  const isResponseCurrent =
    data !== undefined && isPolicySearchResponseCurrent(data, request);
  const filterChips = useMemo(
    () => buildInterpretedFilterChips(urlState, isResponseCurrent ? data : null),
    [urlState, data, isResponseCurrent],
  );

  const applyUrlState = (nextState: ReturnType<typeof parsePolicySearchUrl>) => {
    if (!isPolicySearchUrlStateValid(nextState)) {
      return;
    }

    setSearchParams(buildPolicySearchUrlParams(nextState), { replace: false });
  };

  const handleSearchSubmit = (draftQ: string) => {
    const trimmedQ = draftQ.trim();
    if (!trimmedQ) {
      return;
    }

    applyUrlState(
      withPolicySearchPage(
        {
          ...urlState,
          q: trimmedQ,
        },
        1,
      ),
    );
  };

  const handleFilterRemove = (
    dimension: InterpretedFilterChip['dimension'],
  ) => {
    const filterDimension = mapChipDimensionToFilterDimension(dimension);
    if (!filterDimension) {
      return;
    }

    applyUrlState(removePolicySearchFilter(urlState, filterDimension));
  };

  const handleFilterUpdate = (
    dimension: InterpretedConditionDimension,
    value: PolicySearchFilterValue,
  ) => {
    applyUrlState(updatePolicySearchFilter(urlState, dimension, value));
  };

  const handleFilterAdd = (
    dimension: InterpretedConditionDimension,
    value: PolicySearchFilterValue,
  ) => {
    applyUrlState(updatePolicySearchFilter(urlState, dimension, value));
  };

  const handlePageChange = (nextPage: number) => {
    applyUrlState(withPolicySearchPage(urlState, nextPage));
  };

  const showLoading =
    shouldFetch && (isLoading || (isFetching && !isResponseCurrent));
  const showError = shouldFetch && isError && !showLoading;
  const showSuccess = shouldFetch && !showLoading && !isError && isResponseCurrent;
  const showEmptyResults =
    showSuccess && data !== undefined && isPolicySearchEmptyResults(data);
  const showResultCards =
    showSuccess && data !== undefined && !isPolicySearchEmptyResults(data);

  const errorPresentation = showError
    ? mapPolicySearchError(error)
    : null;
  const emptyPresentation =
    showEmptyResults && data
      ? mapPolicySearchEmptyResults(data)
      : null;

  return (
    <div className="page">
      <header className="greeting">
        <h1 className="greeting__title">안녕하세요, 청년님 👋</h1>
        <p className="greeting__subtitle">
          맞춤 지원금·정책을 한 문장으로 찾아보세요
        </p>
      </header>

      <SearchBar
        key={urlState.q}
        defaultQ={urlState.q}
        onSubmit={handleSearchSubmit}
        isSubmitting={showLoading}
      />

      {shouldFetch ? (
        <InterpretedConditionChips
          chips={filterChips}
          onRemove={handleFilterRemove}
          onUpdate={handleFilterUpdate}
          onAdd={handleFilterAdd}
          disabled={showLoading}
        />
      ) : null}

      {!shouldFetch ? (
        <p className="hint-text">
          검색어를 입력하고 검색하기 버튼을 눌러 주세요. URL에{' '}
          <code>?q=...</code> 형태로 공유할 수 있습니다.
        </p>
      ) : null}

      {showLoading ? <PolicySearchLoadingShell /> : null}

      {showError && errorPresentation ? (
        <PolicySearchErrorShell
          presentation={errorPresentation}
          onRetry={
            errorPresentation.retryable ? () => void refetch() : undefined
          }
        />
      ) : null}

      {showEmptyResults && emptyPresentation ? (
        <PolicySearchEmptyShell presentation={emptyPresentation} />
      ) : null}

      {showResultCards && data ? (
        <section aria-label="검색 결과">
          <div className="section-head">
            <h2 className="section-title">
              조건 맞춤 TOP {Math.min(data.items.length, 3)} 추천
            </h2>
            <span className="section-badge">
              검색 결과 기반 · {data.total}건
            </span>
          </div>

          <div className="cards-grid">
            {data.items.map((hit) => (
              <PolicySearchResultCard key={hit.policy.id} hit={hit} />
            ))}
          </div>

          {getPolicySearchTotalPages(data.total, data.limit) > 1 ? (
            <SearchPagination
              total={data.total}
              page={data.page}
              limit={data.limit}
              onPageChange={handlePageChange}
              disabled={showLoading}
            />
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
