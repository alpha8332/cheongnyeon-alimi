import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import PolicyFilters from '@/components/policy/PolicyFilters';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';
import type { PolicyDto } from '@/types/policy';
import {
  collectRegionOptions,
  EMPTY_PROGRAM_FILTERS,
  filterPrograms,
  type ProgramFilterState,
} from '@/utils/policyFilters';

const EMPTY_POLICIES: PolicyDto[] = [];

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const urlSearch = searchParams.get('search') ?? '';
  const [filters, setFilters] = useState<ProgramFilterState>(() => ({
    ...EMPTY_PROGRAM_FILTERS,
    search: urlSearch,
  }));
  const {
    data: policyList,
    isLoading,
    isError,
    refetch,
  } = usePoliciesQuery({
    page: 1,
    limit: 100,
    include_partial: filters.includePartial,
  });
  const policies = policyList?.items ?? EMPTY_POLICIES;

  const effectiveFilters = useMemo(
    () => ({
      ...filters,
      search: urlSearch || filters.search,
    }),
    [filters, urlSearch],
  );

  const regionOptions = useMemo(
    () => collectRegionOptions(policies),
    [policies],
  );

  const filteredPolicies = useMemo(
    () => filterPrograms(policies, effectiveFilters),
    [policies, effectiveFilters],
  );

  return (
    <div>
      <h2>정책 검색 및 목록</h2>

      <PolicyFilters
        filters={effectiveFilters}
        regionOptions={regionOptions}
        onChange={setFilters}
      />

      {effectiveFilters.search ? (
        <p style={{ fontWeight: 'bold' }}>
          &apos;{effectiveFilters.search}&apos; 검색 결과 목록입니다.
        </p>
      ) : null}

      {isLoading ? <LoadingState message="정책 목록을 불러오는 중입니다." /> : null}

      {!isLoading && isError ? (
        <ErrorState
          message="정책 목록을 불러오지 못했습니다."
          onRetry={() => void refetch()}
        />
      ) : null}

      {!isLoading && !isError && filteredPolicies.length === 0 ? (
        <EmptyState message="조건에 맞는 정책이 없습니다." />
      ) : null}

      {!isLoading && !isError && filteredPolicies.length > 0 ? (
        <div
          style={{
            display: 'grid',
            gap: '12px',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          }}
        >
          {filteredPolicies.map((policy) => (
            <PolicyCard key={policy.id} policy={policy} />
          ))}
        </div>
      ) : null}
    </div>
  );
}
