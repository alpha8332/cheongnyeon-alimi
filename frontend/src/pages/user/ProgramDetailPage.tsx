import { Link, useParams, useSearchParams } from 'react-router-dom';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import PartialBadge from '@/components/policy/PartialBadge';
import { usePolicyQuery } from '@/hooks/usePoliciesQuery';
import {
  formatAge,
  formatApplicationPeriod,
  formatApplicationSchedule,
  formatApplicationStatus,
  formatCategoryTags,
  formatNullableText,
  formatOrganization,
  formatRegion,
  getDDayLabel,
} from '@/utils/policyDisplay';
import { parsePolicyId } from '@/utils/policyId';

function DetailField({
  label,
  value,
}: {
  label: string;
  value: string;
}) {
  return (
    <div style={{ marginBottom: '12px' }}>
      <strong>{label}</strong>
      <p
        style={{
          margin: '4px 0 0',
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
        }}
        title={value}
      >
        {value}
      </p>
    </div>
  );
}

export default function ProgramDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const policyId = parsePolicyId(id);
  const includePartial = searchParams.get('include_partial') === 'true';
  const {
    data: policy,
    isLoading,
    isError,
    refetch,
  } = usePolicyQuery(policyId, includePartial);

  if (policyId === null) {
    return (
      <div>
        <h2>정책 상세</h2>
        <ErrorState message="잘못된 정책 식별자입니다." />
        <p style={{ marginTop: '12px' }}>
          <Link to="/programs">목록으로 돌아가기</Link>
        </p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div>
        <h2>정책 상세</h2>
        <LoadingState message="정책 상세를 불러오는 중입니다." />
      </div>
    );
  }

  if (isError) {
    return (
      <div>
        <h2>정책 상세</h2>
        <ErrorState
          message="정책 상세를 불러오지 못했습니다."
          onRetry={() => void refetch()}
        />
        <p style={{ marginTop: '12px' }}>
          <Link to="/programs">목록으로 돌아가기</Link>
        </p>
      </div>
    );
  }

  if (!policy) {
    return (
      <div>
        <h2>정책 상세</h2>
        <EmptyState message="요청한 정책을 찾을 수 없습니다." />
        <p style={{ marginTop: '12px' }}>
          <Link to="/programs">목록으로 돌아가기</Link>
        </p>
      </div>
    );
  }

  const categoryTags = formatCategoryTags(policy);

  return (
    <div>
      <p>
        <Link to="/programs">← 목록으로</Link>
      </p>

      <h2>
        {policy.title}
        <PartialBadge policy={policy} />
      </h2>

      <Card>
        <DetailField label="기관" value={formatOrganization(policy)} />
        <DetailField label="지역" value={formatRegion(policy)} />
        <DetailField label="연령" value={formatAge(policy)} />

        <div style={{ marginBottom: '12px' }}>
          <strong>카테고리</strong>
          <div style={{ marginTop: '4px' }}>
            {categoryTags.map((tag) => (
              <span
                key={tag}
                style={{
                  border: '1px solid black',
                  padding: '2px 6px',
                  marginRight: '6px',
                  fontSize: '12px',
                  display: 'inline-block',
                }}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>

        <DetailField
          label="지원 내용"
          value={formatNullableText(policy.support_content, '지원 내용 없음')}
        />
        <DetailField
          label="자격 요건"
          value={formatNullableText(policy.eligibility_text, '자격 정보 없음')}
        />
        <DetailField
          label="신청 방법"
          value={formatNullableText(policy.application_method, '신청 방법 없음')}
        />

        <div style={{ display: 'grid', gap: '12px', gridTemplateColumns: '1fr 1fr' }}>
          <DetailField
            label="일정 유형"
            value={formatApplicationSchedule(policy.application_schedule)}
          />
          <DetailField
            label="접수 상태"
            value={formatApplicationStatus(policy.application_status)}
          />
        </div>

        <DetailField
          label="신청 기간"
          value={formatApplicationPeriod(policy)}
        />
        <DetailField label="D-Day" value={getDDayLabel(policy)} />

        <div style={{ marginTop: '12px' }}>
          <Button
            onClick={() => {
              window.open(policy.source_url, '_blank', 'noopener,noreferrer');
            }}
          >
            원문 링크 열기
          </Button>
        </div>
      </Card>
    </div>
  );
}
