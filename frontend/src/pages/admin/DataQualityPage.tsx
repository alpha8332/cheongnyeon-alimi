import Card from '@/components/common/Card';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import { usePoliciesQuery } from '@/hooks/usePoliciesQuery';

export default function DataQualityPage() {
  const {
    data: policyList,
    isLoading,
    isError,
    refetch,
  } = usePoliciesQuery({
    page: 1,
    limit: 100,
    include_partial: true,
  });
  const policies = policyList?.items ?? [];

  if (isLoading) {
    return (
      <div>
        <h2>공개 데이터 품질 (관리자)</h2>
        <LoadingState />
      </div>
    );
  }

  if (isError) {
    return (
      <div>
        <h2>공개 데이터 품질 (관리자)</h2>
        <ErrorState
          message="품질 데이터를 불러오지 못했습니다."
          onRetry={() => void refetch()}
        />
      </div>
    );
  }

  return (
    <div>
      <h2>공개 데이터 품질 (관리자)</h2>
      <p>
        공개 Policy API가 제공하는 valid·partial 상태만 표시합니다. provenance는
        공개 DTO에 포함되지 않으며 별도 관리자 API가 필요합니다.
      </p>

      {policies.map((policy) => (
        <Card key={policy.id}>
          <h3>{policy.title}</h3>
          <p>
            식별: {policy.id} / {policy.source_id} /{' '}
            {policy.external_id ?? 'external ID 없음'}
          </p>
          <p>품질 상태: {policy.data_quality_status}</p>
        </Card>
      ))}
    </div>
  );
}
