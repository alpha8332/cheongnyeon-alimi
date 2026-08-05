import { useMemo } from 'react';
import { useSearchParams } from 'react-router';
import SearchBar from '@/components/policySearch/SearchBar';
import LoadingState from '@/components/common/LoadingState';
import { usePolicySearchQuery } from '@/hooks/usePolicySearchQuery';
import {
  buildPolicySearchUrlParams,
  hasPolicySearchQuery,
  isPolicySearchUrlStateValid,
  parsePolicySearchUrl,
  toPolicySearchRequest,
} from '@/utils/policySearchUrl';
import './PolicySearchPage.css';

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

  const showResults = shouldFetch && !isLoading && !isError && data;
  const showLoading = shouldFetch && (isLoading || isFetching);
  const showError = shouldFetch && isError;

  return (
    <div className="policy-search-page">
      <header className="policy-search-page__greeting">
        <h1 className="policy-search-page__title">정책 검색</h1>
        <p className="policy-search-page__subtitle">
          자연어로 원하는 조건을 입력하면 맞춤 정책을 찾아드립니다.
        </p>
      </header>

      <SearchBar
        key={searchParams.toString()}
        initialQ={urlState.q}
        onSubmit={handleSearchSubmit}
        disabled={showLoading}
      />

      {!shouldFetch ? (
        <p className="policy-search-page__hint">
          검색어를 입력하고 검색 버튼을 눌러 주세요. URL에{' '}
          <code>?q=...</code> 형태로 공유할 수 있습니다.
        </p>
      ) : null}

      {showLoading ? (
        <LoadingState message="검색 결과를 불러오는 중입니다." />
      ) : null}

      {showError ? (
        <p role="alert" style={{ color: '#b45309' }}>
          {error instanceof Error ? error.message : '검색 요청에 실패했습니다.'}
        </p>
      ) : null}

      {showResults ? (
        <section aria-label="검색 결과">
          <div className="policy-search-page__section-head">
            <h2 className="policy-search-page__section-title">검색 결과</h2>
            <span className="policy-search-page__section-badge">
              {data.total}건
            </span>
          </div>

          {data.items.length === 0 ? (
            <p className="policy-search-page__hint">
              조건에 맞는 정책이 없습니다. 다른 검색어를 시도해 보세요.
            </p>
          ) : (
            <div className="policy-search-page__cards-grid">
              {data.items.map((hit) => (
                <article
                  key={hit.policy.id}
                  className="policy-search-page__card"
                >
                  <div className="policy-search-page__card-visual">
                    <span className="policy-search-page__card-tag">
                      {hit.policy.categories[0] ?? 'policy'}
                    </span>
                  </div>
                  <div className="policy-search-page__card-body">
                    <h3 className="policy-search-page__card-title">
                      {hit.policy.title}
                    </h3>
                    <p className="policy-search-page__card-meta">
                      {hit.policy.organization ?? '기관 정보 없음'}
                    </p>
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      ) : null}
    </div>
  );
}
