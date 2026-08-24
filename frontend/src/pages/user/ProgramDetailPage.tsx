import type { ReactNode } from 'react';
import { Link, useParams, useSearchParams } from 'react-router';
import Card from '@/components/common/Card';
import EmptyState from '@/components/common/EmptyState';
import ErrorState from '@/components/common/ErrorState';
import LoadingState from '@/components/common/LoadingState';
import EligibilitySummary from '@/components/policy/EligibilitySummary';
import PolicyDetailSummaryHeader from '@/components/policy/detail/PolicyDetailSummaryHeader';
import PolicyDetailTextContent, {
  PolicyDetailSection,
} from '@/components/policy/detail/PolicyDetailSection';
import { usePolicyQuery } from '@/hooks/usePoliciesQuery';
import { isPolicyDetailApiError } from '@/utils/policyDetailErrorToast';
import {
  formatPolicyEmploymentSummary,
  getPolicyEligibilityDisplayText,
  splitPolicyTextToBullets,
} from '@/utils/policyDetailContent';
import {
  formatCollectedAt,
  formatNullableText,
  formatOrganization,
  POLICY_ELIGIBILITY_NOTICE,
} from '@/utils/policyDisplay';
import { parsePolicyId } from '@/utils/policyId';

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

function ConditionList({
  label,
  items,
}: {
  label: string;
  items: readonly string[];
}) {
  if (items.length === 0) {
    return null;
  }

  return (
    <div className="policy-detail-subblock">
      <h3 className="policy-detail-subblock__title">{label}</h3>
      <ul className="policy-detail-text-list">
        {items.map((item) => (
          <li key={`${label}-${item}`} className="policy-detail-text-list__item">
            {item}
          </li>
        ))}
      </ul>
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
    error,
    refetch,
  } = usePolicyQuery(policyId, includePartial);
  const hasCachedPolicy = policy != null;

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

  const documentItems = policy.eligibility_summary.documents.map((item) => item.text);
  const contactItems = policy.eligibility_summary.institutional_contacts;
  const eligibilityDisplayText = getPolicyEligibilityDisplayText(policy);

  return (
    <div className="page policy-detail-page">
      <p className="detail-back">
        <Link to="/programs">← 목록으로</Link>
      </p>

      <PolicyDetailSummaryHeader policy={policy} />

      <p className="policy-eligibility-notice" role="note">
        {POLICY_ELIGIBILITY_NOTICE}
      </p>

      <div className="policy-detail-sections">
        <PolicyDetailSection title="지원 대상 및 자격 요건" id="policy-detail-eligibility">
          <PolicyDetailTextContent
            text={eligibilityDisplayText}
            fallback="공식 원문에서 확인 가능한 자격 요건 요약이 없습니다."
          />
          <ConditionList
            label="취업·학력"
            items={[formatPolicyEmploymentSummary(policy)].filter(
              (item) => item !== '취업·학력 조건 미확인',
            )}
          />
          <ConditionList label="필수 조건" items={policy.required_conditions} />
          <ConditionList label="우대 조건" items={policy.preferred_conditions} />
          <ConditionList label="제외 조건" items={policy.excluded_conditions} />
        </PolicyDetailSection>

        <PolicyDetailSection title="지원 내용 및 혜택" id="policy-detail-support">
          <PolicyDetailTextContent
            text={policy.support_content}
            fallback="지원 내용 정보가 없습니다."
            preferOrdered
          />
          {policy.summary ? (
            <div className="policy-detail-subblock">
              <h3 className="policy-detail-subblock__title">정책 요약</h3>
              <PolicyDetailTextContent text={policy.summary} fallback="" />
            </div>
          ) : null}
        </PolicyDetailSection>

        <PolicyDetailSection title="신청 방법 및 제출 서류" id="policy-detail-application">
          <PolicyDetailTextContent
            text={policy.application_method}
            fallback="신청 방법 정보가 없습니다."
            preferOrdered
          />
          {documentItems.length > 0 ? (
            <div className="policy-detail-subblock">
              <h3 className="policy-detail-subblock__title">필요 서류</h3>
              <ul className="policy-detail-text-list">
                {documentItems.map((item) => (
                  <li key={item} className="policy-detail-text-list__item">
                    {item}
                  </li>
                ))}
              </ul>
            </div>
          ) : null}
        </PolicyDetailSection>

        <PolicyDetailSection title="주관 기관 및 문의처" id="policy-detail-contact">
          <p className="policy-detail-text">
            <strong>{formatOrganization(policy)}</strong>
          </p>
          <p className="policy-detail-text policy-detail-text--muted">
            데이터 출처: {policy.source_name}
          </p>
          {contactItems.length > 0 ? (
            <ul className="policy-detail-contact-list">
              {contactItems.map((contact) => (
                <li key={`${contact.label}-${contact.value}`}>
                  <span className="policy-detail-contact-list__label">{contact.label}</span>
                  <span className="policy-detail-contact-list__value">{contact.value}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="policy-detail-text policy-detail-text--empty">
              공개된 시설 문의처가 없습니다. 아래 핵심 신청 조건 또는 공식 신청 사이트를
              확인해 주세요.
            </p>
          )}
        </PolicyDetailSection>

        <Card title="📄 정책 정보">
          <p className="policy-detail-text policy-detail-text--muted">
            수집 시각: {formatCollectedAt(policy.collected_at)}
          </p>
          <p className="policy-detail-text policy-detail-text--muted">
            원문 URL:{' '}
            {policy.source_url ? (
              <a href={policy.source_url} target="_blank" rel="noreferrer">
                {policy.source_url}
              </a>
            ) : (
              '없음'
            )}
          </p>
          {splitPolicyTextToBullets(policy.application_period_text).length > 0 ? (
            <p className="policy-detail-text">
              신청 기간 원문:{' '}
              {formatNullableText(policy.application_period_text, '신청 기간 미정')}
            </p>
          ) : null}
        </Card>
      </div>

      <EligibilitySummary summary={policy.eligibility_summary} />
    </div>
  );
}
