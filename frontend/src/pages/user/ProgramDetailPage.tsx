import { useQueryClient } from '@tanstack/react-query';
import { useState, type ReactNode } from 'react';
import { Link, useParams, useSearchParams } from 'react-router';
import Button from '@/components/common/Button';
import Card from '@/components/common/Card';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import PartialBadge from '@/components/policy/PartialBadge';
import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import EligibilitySummaryCard from '@/components/eligibility/EligibilitySummaryCard';
import PolicyIcsDownloadButton from '@/components/user/PolicyIcsDownloadButton';
import { getPolicyById } from '@/api/policies';
import { useSavedConditions } from '@/hooks/useSavedConditions';
import { useApiErrorToast } from '@/hooks/useApiErrorToast';
import { usePolicyQuery } from '@/hooks/usePoliciesQuery';
import {
  isPolicyDetailApiError,
  mapPolicyDetailErrorToToast,
} from '@/utils/policyDetailErrorToast';
import {
  formatAge,
  formatApplicationPeriod,
  formatApplicationSchedule,
  formatApplicationStatus,
  formatCategoryTags,
  formatCollectedAt,
  formatNullableText,
  formatOrganization,
  formatRegion,
  getDDayLabel,
  POLICY_ELIGIBILITY_NOTICE,
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
    <div className="detail-field">
      <div className="detail-field__label">{label}</div>
      <p className="detail-field__value">{value}</p>
    </div>
  );
}

function DetailShell({
  children,
  title = '정책 상세',
}: {
  children: ReactNode;
  title?: string;
}) {
  return (
    <div className="page">
      <p className="detail-back">
        <Link to="/programs">← 목록으로</Link>
      </p>
      <h1 className="detail-title">{title}</h1>
      {children}
    </div>
  );
}

export default function ProgramDetailPage() {
  const { id } = useParams();
  const [searchParams] = useSearchParams();
  const policyId = parsePolicyId(id);
  const includePartial = searchParams.get('include_partial') === 'true';
  const queryClient = useQueryClient();
  const { showToast } = useApiErrorToast();
  const [isSummaryRefreshing, setIsSummaryRefreshing] = useState(false);
  const [summaryValidationError, setSummaryValidationError] = useState<
    string | null
  >(null);

  const {
    data: policy,
    isLoading,
    isError,
    error,
    refetch,
  } = usePolicyQuery(policyId, includePartial);
  const { conditions: savedConditions } = useSavedConditions();

  const hasCachedPolicy = policy != null;

  const handleSummaryRefresh = () => {
    void (async () => {
      if (policyId === null) {
        return;
      }

      setSummaryValidationError(null);
      setIsSummaryRefreshing(true);

      try {
        const updated = await getPolicyById(policyId, includePartial, {
          summaryRefetch: true,
        });

        queryClient.setQueryData(
          ['policy', policyId, { include_partial: includePartial }],
          updated,
        );
      } catch (refreshError: unknown) {
        if (!isPolicyDetailApiError(refreshError)) {
          return;
        }

        if (refreshError.status === 422) {
          setSummaryValidationError(refreshError.detail);
          return;
        }

        if (refreshError.status >= 500) {
          showToast(mapPolicyDetailErrorToToast(refreshError), {
            onRetry: () => {
              handleSummaryRefresh();
            },
          });
        }
      } finally {
        setIsSummaryRefreshing(false);
      }
    })();
  };

  if (policyId === null) {
    return (
      <DetailShell>
        <ErrorState message="잘못된 정책 식별자입니다." />
      </DetailShell>
    );
  }

  if (isLoading && !hasCachedPolicy) {
    return (
      <DetailShell>
        <LoadingState message="정책 상세를 불러오는 중입니다." />
      </DetailShell>
    );
  }

  if (isError && !hasCachedPolicy) {
    if (isPolicyDetailApiError(error) && error.status === 422) {
      return (
        <DetailShell>
          <ErrorState message={error.detail} />
        </DetailShell>
      );
    }

    return (
      <DetailShell>
        <ErrorState
          message="정책 상세를 불러오지 못했습니다."
          onRetry={() => void refetch()}
        />
      </DetailShell>
    );
  }

  if (!policy) {
    return (
      <DetailShell>
        <EmptyState message="요청한 정책을 찾을 수 없습니다." />
      </DetailShell>
    );
  }

  const categoryTags = formatCategoryTags(policy);

  return (
    <div className="page">
      <p className="detail-back">
        <Link to="/programs">← 목록으로</Link>
      </p>

      <h1 className="detail-title detail-title--with-actions">
        <span className="detail-title__text">
          {policy.title}
          <PartialBadge policy={policy} />
        </span>
        <FavoriteToggleButton
          policyId={policy.id}
          className="detail-title__favorite"
        />
      </h1>

      <Card title="📄 정책 정보">
        <p className="policy-eligibility-notice" role="note">
          {POLICY_ELIGIBILITY_NOTICE}
        </p>
        <DetailField label="기관" value={formatOrganization(policy)} />
        <DetailField label="데이터 출처" value={policy.source_name} />
        <DetailField
          label="수집 시각"
          value={formatCollectedAt(policy.collected_at)}
        />
        <DetailField label="지역" value={formatRegion(policy)} />
        <DetailField label="연령" value={formatAge(policy)} />

        <div className="detail-field">
          <div className="detail-field__label">카테고리</div>
          <div className="tag-list">
            {categoryTags.map((tag) => (
              <span key={tag} className="tag-list__item">
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

        <div className="detail-grid">
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

        <div className="detail-actions">
          <Button
            variant="gradient"
            onClick={() => {
              window.open(policy.source_url, '_blank', 'noopener,noreferrer');
            }}
          >
            원문 링크 열기
          </Button>
          <PolicyIcsDownloadButton policy={policy} />
        </div>
      </Card>

      <Card>
        <EligibilitySummaryCard
          policy={policy}
          summary={policy.eligibility_summary}
          savedConditions={savedConditions}
          onRefresh={handleSummaryRefresh}
          isRefreshing={isSummaryRefreshing}
          validationError={summaryValidationError}
        />
      </Card>
    </div>
  );
}
