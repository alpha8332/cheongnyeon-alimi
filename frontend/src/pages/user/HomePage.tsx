import { useMemo, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import SearchBar from '@/components/policySearch/SearchBar';
import SearchPagination from '@/components/policySearch/SearchPagination';
import PolicySearchResultCard from '@/components/policySearch/PolicySearchResultCard';
import PolicySearchEmptyShell from '@/components/policySearch/PolicySearchEmptyShell';
import PolicySearchErrorShell from '@/components/policySearch/PolicySearchErrorShell';
import PolicySearchLoadingShell from '@/components/policySearch/PolicySearchLoadingShell';
import InterpretedConditionChips from '@/components/policySearch/InterpretedConditionChips';
import PolicySearchSidebar from '@/components/policySearch/PolicySearchSidebar';
import { useHomeRecommendedPolicies } from '@/hooks/useHomeRecommendedPolicies';
import { useSavedConditions } from '@/hooks/useSavedConditions';
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
import { findSelectedHit } from '@/utils/policySearchReason';
import { POLICY_ELIGIBILITY_NOTICE } from '@/utils/policyDisplay';
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
import { buildSavedConditionSearchPreferences } from '@/utils/policySearchSavedConditions';
import { HOME_SAVED_CONDITIONS_RECOMMENDATION_CAPTION } from '@/utils/homeRecommendedPolicies';
import {
  HOME_RECOMMENDED_SEARCHES,
  buildPolicySearchEntryPath,
  getRelatedPolicySearches,
} from '@/utils/policySearchNavigation';
import '@/components/policySearch/PolicySearchSidebar.css';
import './HomePage.css';

export default function HomePage() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedPolicyId, setSelectedPolicyId] = useState<number | null>(null);
  const { conditions: savedConditions } = useSavedConditions();

  const urlState = useMemo(
    () => parsePolicySearchUrl(searchParams),
    [searchParams],
  );
  const effectiveUrlState = urlState;
  const searchPreferences = useMemo(
    () =>
      buildSavedConditionSearchPreferences(
        savedConditions,
        urlState.use_saved_conditions !== false,
      ),
    [savedConditions, urlState.use_saved_conditions],
  );
  const request = useMemo(
    () => toPolicySearchRequest(effectiveUrlState, searchPreferences),
    [effectiveUrlState, searchPreferences],
  );
  const shouldFetch = hasPolicySearchQuery(urlState);
  const relatedSearches = useMemo(
    () => getRelatedPolicySearches(urlState.q),
    [urlState.q],
  );

  const {
    policies: homeRecommendedPolicies,
    isPersonalized: isHomeRecommendationPersonalized,
    isLoading: isHomeRecommendationLoading,
  } = useHomeRecommendedPolicies(savedConditions);

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
  const sidebarResponse = isResponseCurrent ? data : null;
  const activeSelectedPolicyId = useMemo(() => {
    if (!sidebarResponse?.items.length) {
      return null;
    }

    if (
      selectedPolicyId !== null &&
      sidebarResponse.items.some((hit) => hit.policy.id === selectedPolicyId)
    ) {
      return selectedPolicyId;
    }

    return sidebarResponse.items[0]?.policy.id ?? null;
  }, [sidebarResponse, selectedPolicyId]);
  const selectedHit = useMemo(
    () => findSelectedHit(sidebarResponse, activeSelectedPolicyId),
    [sidebarResponse, activeSelectedPolicyId],
  );

  const filterChips = useMemo(
    () => buildInterpretedFilterChips(effectiveUrlState, sidebarResponse),
    [effectiveUrlState, sidebarResponse],
  );

  const applyUrlState = (nextState: ReturnType<typeof parsePolicySearchUrl>) => {
    if (!isPolicySearchUrlStateValid(nextState)) {
      return;
    }

    setSearchParams(buildPolicySearchUrlParams(nextState), { replace: false });
  };

  const submitSearchQuery = (draftQ: string) => {
    const trimmedQ = draftQ.trim();
    if (!trimmedQ) {
      return;
    }

    const nextState = withPolicySearchPage(
      {
        ...urlState,
        q: trimmedQ,
      },
      1,
    );

    applyUrlState(nextState);
  };

  const handleSearchSubmit = (draftQ: string) => {
    submitSearchQuery(draftQ);
  };

  const handleRecommendedSearch = (term: string) => {
    const path = buildPolicySearchEntryPath(term, {
      useSavedConditions: false,
    });
    if (path) {
      navigate(path);
    }
  };

  const handleSearchClear = () => {
    applyUrlState(
      withPolicySearchPage(
        {
          ...urlState,
          q: '',
        },
        1,
      ),
    );
    setSelectedPolicyId(null);
  };

  const handleFilterRemove = (
    dimension: InterpretedFilterChip['dimension'],
  ) => {
    const filterDimension = mapChipDimensionToFilterDimension(dimension);
    if (!filterDimension) {
      return;
    }

    applyUrlState(removePolicySearchFilter(effectiveUrlState, filterDimension));
  };

  const handleFilterUpdate = (
    dimension: InterpretedConditionDimension,
    value: PolicySearchFilterValue,
  ) => {
    applyUrlState(updatePolicySearchFilter(effectiveUrlState, dimension, value));
  };

  const handleFilterAdd = (
    dimension: InterpretedConditionDimension,
    value: PolicySearchFilterValue,
  ) => {
    applyUrlState(updatePolicySearchFilter(effectiveUrlState, dimension, value));
  };

  const handlePageChange = (nextPage: number) => {
    applyUrlState(withPolicySearchPage(effectiveUrlState, nextPage));
  };

  const showLoading =
    shouldFetch && (isLoading || (isFetching && !isResponseCurrent));
  const showError = shouldFetch && isError && !showLoading;
  const showSuccess = shouldFetch && !showLoading && !isError && isResponseCurrent;
  const showEmptyResults =
    showSuccess && data !== undefined && isPolicySearchEmptyResults(data);
  const showResultCards =
    showSuccess && data !== undefined && !isPolicySearchEmptyResults(data);

  const errorPresentation = showError ? mapPolicySearchError(error) : null;
  const emptyPresentation =
    showEmptyResults && data ? mapPolicySearchEmptyResults(data) : null;

  return (
    <div
      className={`page home-page${shouldFetch ? ' home-page--search-active policy-search-page' : ''}`}
    >
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
        onClear={handleSearchClear}
        isSubmitting={showLoading}
      />

      {shouldFetch && relatedSearches.length > 0 ? (
        <section className="home-search-suggestions" aria-label="관련 검색어">
          <p className="chips-label">관련 검색어</p>
          <div className="chips-row home-search-suggestions__row">
            {relatedSearches.map((term) => (
              <button
                key={term}
                type="button"
                className="chip home-search-suggestions__chip"
                onClick={() => submitSearchQuery(term)}
              >
                {term}
              </button>
            ))}
          </div>
        </section>
      ) : null}

      {shouldFetch && searchPreferences ? (
        <p className="home-search-profile-note" role="note">
          저장 프로필은 검색 결과를 제외하지 않고, 관련도가 같은 정책의 우선순위에
          반영됩니다.
        </p>
      ) : null}

      {!shouldFetch ? (
        <>
          <section className="home-search-suggestions" aria-label="예시 검색어">
            <p className="chips-label">예시 검색어</p>
            <div className="chips-row home-search-suggestions__row">
              {HOME_RECOMMENDED_SEARCHES.map((term) => (
                <button
                  key={term}
                  type="button"
                  className="chip home-search-suggestions__chip"
                  onClick={() => handleRecommendedSearch(term)}
                >
                  {term}
                </button>
              ))}
            </div>
          </section>

          {isHomeRecommendationLoading ? (
            <LoadingState message="정책을 불러오는 중입니다." />
          ) : (
            <section
              className="home-recommended-policies"
              aria-label={
                isHomeRecommendationPersonalized
                  ? '저장된 조건 추천 정책'
                  : '추천 정책'
              }
            >
              {isHomeRecommendationPersonalized ? (
                <p className="home-recommended-policies__caption" role="note">
                  {HOME_SAVED_CONDITIONS_RECOMMENDATION_CAPTION}
                </p>
              ) : null}
              {homeRecommendedPolicies.length > 0 ? (
                <div className="cards-grid">
                  {homeRecommendedPolicies.map((policy) => (
                    <PolicyCard key={policy.id} policy={policy} />
                  ))}
                </div>
              ) : isHomeRecommendationPersonalized ? (
                <p className="home-recommended-policies__empty" role="status">
                  저장된 조건에 맞는 추천 정책을 찾지 못했습니다.
                </p>
              ) : null}
            </section>
          )}

          <Card title="📋 더 많은 정책 보기">
            <p className="hint-text">
              자연어 검색은 상단 검색창을, 전체목록은 정책 목록페이지에서 확인할
              수 있습니다.
            </p>
            <div style={{ marginTop: '16px' }}>
              <Button variant="secondary" onClick={() => navigate('/programs')}>
                정책 목록 보기
              </Button>
            </div>
          </Card>
        </>
      ) : (
        <div className="policy-search-layout">
          <div className="policy-search-layout__primary">
            <InterpretedConditionChips
              chips={filterChips}
              onRemove={handleFilterRemove}
              onUpdate={handleFilterUpdate}
              onAdd={handleFilterAdd}
              disabled={showLoading}
            />

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
                <p className="policy-eligibility-notice" role="note">
                  {POLICY_ELIGIBILITY_NOTICE}
                </p>
                <div className="cards-grid">
                  {data.items.map((hit) => (
                    <PolicySearchResultCard
                      key={hit.policy.id}
                      hit={hit}
                      searchIncludePartial={effectiveUrlState.include_partial}
                      isSelected={activeSelectedPolicyId === hit.policy.id}
                      onSelect={(nextHit) =>
                        setSelectedPolicyId(nextHit.policy.id)
                      }
                    />
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

          <PolicySearchSidebar
            response={sidebarResponse}
            selectedHit={selectedHit}
          />
        </div>
      )}
    </div>
  );
}
