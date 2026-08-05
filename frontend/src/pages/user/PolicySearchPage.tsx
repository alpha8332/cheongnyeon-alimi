import { useMemo } from 'react';
import { useSearchParams } from 'react-router';
import SearchBar from '@/components/policySearch/SearchBar';
import PolicySearchResultCard from '@/components/policySearch/PolicySearchResultCard';
import PolicySearchEmptyShell from '@/components/policySearch/PolicySearchEmptyShell';
import PolicySearchErrorShell from '@/components/policySearch/PolicySearchErrorShell';
import PolicySearchLoadingShell from '@/components/policySearch/PolicySearchLoadingShell';
import UrlFilterChips from '@/components/policySearch/UrlFilterChips';
import { usePolicySearchQuery } from '@/hooks/usePolicySearchQuery';
import { buildUrlFilterChips } from '@/utils/policySearchFilterChips';
import {
  isPolicySearchEmptyResults,
  mapPolicySearchEmptyResults,
  mapPolicySearchError,
} from '@/utils/policySearchErrors';
import {
  buildPolicySearchUrlParams,
  hasPolicySearchQuery,
  isPolicySearchUrlStateValid,
  parsePolicySearchUrl,
  toPolicySearchRequest,
} from '@/utils/policySearchUrl';

export default function PolicySearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const urlState = useMemo(
    () => parsePolicySearchUrl(searchParams),
    [searchParams],
  );
  const filterChips = useMemo(() => buildUrlFilterChips(urlState), [urlState]);
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

  const handleSearchSubmit = (draftQ: string) => {
    const trimmedQ = draftQ.trim();
    if (!trimmedQ) {
      return;
    }

    const nextState = {
      ...urlState,
      q: trimmedQ,
      page: 1,
    };

    if (!isPolicySearchUrlStateValid(nextState)) {
      return;
    }

    setSearchParams(buildPolicySearchUrlParams(nextState), { replace: false });
  };

  const showLoading = shouldFetch && (isLoading || isFetching);
  const showError = shouldFetch && isError && !showLoading;
  const showSuccess = shouldFetch && !showLoading && !isError && data;
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

      <UrlFilterChips chips={filterChips} />

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
        </section>
      ) : null}
    </div>
  );
}
