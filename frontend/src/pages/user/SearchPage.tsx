import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import PolicyCard from '@/components/policy/PolicyCard';
import PolicyFilters from '@/components/policy/PolicyFilters';
import { useProgramsQuery } from '@/hooks/useProgramsQuery';
import {
  collectRegionOptions,
  EMPTY_PROGRAM_FILTERS,
  filterPrograms,
  type ProgramFilterState,
} from '@/utils/policyFilters';

export default function SearchPage() {
  const [searchParams] = useSearchParams();
  const urlSearch = searchParams.get('search') ?? '';
  const [filters, setFilters] = useState<ProgramFilterState>(() => ({
    ...EMPTY_PROGRAM_FILTERS,
    search: urlSearch,
  }));
  const { data: programs = [], isLoading, isError, refetch } = useProgramsQuery();

  const effectiveFilters = useMemo(
    () => ({
      ...filters,
      search: urlSearch || filters.search,
    }),
    [filters, urlSearch],
  );

  const regionOptions = useMemo(
    () => collectRegionOptions(programs),
    [programs],
  );

  const filteredPrograms = useMemo(
    () => filterPrograms(programs, effectiveFilters),
    [programs, effectiveFilters],
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

      {!isLoading && !isError && filteredPrograms.length === 0 ? (
        <EmptyState message="조건에 맞는 정책이 없습니다." />
      ) : null}

      {!isLoading && !isError && filteredPrograms.length > 0 ? (
        <div
          style={{
            display: 'grid',
            gap: '12px',
            gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
          }}
        >
          {filteredPrograms.map((program) => (
            <PolicyCard
              key={`${program.source_id}-${program.external_id}`}
              program={program}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
