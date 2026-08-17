import FavoriteToggleButton from '@/components/policy/FavoriteToggleButton';
import PartialBadge from '@/components/policy/PartialBadge';
import PolicyCategoryBadge from '@/components/policy/PolicyCategoryBadge';
import PolicyDetailStatusBadges from '@/components/policy/PolicyDetailStatusBadges';
import PolicyDetailHeaderActions from '@/components/policy/detail/PolicyDetailHeaderActions';
import type { PolicyDetailDto } from '@/types/policy';
import { getPrimaryPolicyCategory } from '@/utils/calendarCategoryTheme';
import {
  formatAge,
  formatApplicationPeriodDisplay,
  formatOrganization,
  formatRegion,
  getDDayLabel,
  getCategoryLabel,
  getPolicyDisplayTitle,
} from '@/utils/policyDisplay';
import {
  formatPolicyIncomeSummary,
  sanitizePolicyText,
  splitCircleBulletLines,
} from '@/utils/policyDetailContent';

interface PolicyDetailSummaryHeaderProps {
  policy: PolicyDetailDto;
}

function MetaItem({ label, value }: { label: string; value: string }) {
  const circleLines = splitCircleBulletLines(value);
  const lines =
    circleLines.length >= 2
      ? circleLines
      : value
          .split(/\n+/)
          .flatMap((part) =>
            part.includes(' · ') ? part.split(/\s·\s/) : [part],
          )
          .map((part) => part.trim())
          .filter(Boolean);

  return (
    <div className="policy-detail-meta-card__item">
      <span className="policy-detail-meta-card__label">{label}</span>
      <div className="policy-detail-meta-card__value-stack">
        {lines.map((line) => (
          <span key={`${label}-${line}`} className="policy-detail-meta-card__value-line">
            {line}
          </span>
        ))}
      </div>
    </div>
  );
}

function PolicyBenefitHighlight({ text }: { text: string }) {
  const lines = splitCircleBulletLines(text);

  if (lines.length <= 1) {
    return <p className="policy-detail-summary__benefit">{text}</p>;
  }

  return (
    <div className="policy-detail-summary__benefit policy-detail-summary__benefit--stacked">
      {lines.map((line) => (
        <p key={line} className="policy-detail-summary__benefit-line">
          ○ {line}
        </p>
      ))}
    </div>
  );
}

export default function PolicyDetailSummaryHeader({
  policy,
}: PolicyDetailSummaryHeaderProps) {
  const dDayLabel = getDDayLabel(policy);
  const supportHighlight =
    sanitizePolicyText(policy.support_content) || sanitizePolicyText(policy.summary);
  const categories =
    policy.categories.length > 0 ? policy.categories : [getPrimaryPolicyCategory(policy)];

  return (
    <header className="policy-detail-summary panel">
      <div className="policy-detail-summary__head">
        <div className="policy-detail-summary__head-main">
          <div className="policy-detail-summary__badges">
            <PolicyDetailStatusBadges policy={policy} />
            {dDayLabel !== '상시' && dDayLabel !== '일정 미정' && dDayLabel !== '마감' ? (
              <span className="policy-status-badge policy-status-badge--dday">{dDayLabel}</span>
            ) : null}
            {categories.map((category) => (
              <PolicyCategoryBadge key={category} category={category} />
            ))}
            <PartialBadge policy={policy} />
          </div>

          <h1 className="policy-detail-summary__title">{getPolicyDisplayTitle(policy)}</h1>
        </div>

        <FavoriteToggleButton
          policyId={policy.id}
          className="policy-detail-summary__bookmark"
        />
      </div>

      {supportHighlight ? <PolicyBenefitHighlight text={supportHighlight} /> : null}

      <div className="policy-detail-meta-card" aria-label="핵심 신청 조건">
        <MetaItem label="신청 기간" value={formatApplicationPeriodDisplay(policy)} />
        <MetaItem label="대상 연령" value={formatAge(policy)} />
        <MetaItem label="거주 지역" value={formatRegion(policy)} />
        <MetaItem label="소득 기준" value={formatPolicyIncomeSummary(policy)} />
      </div>

      <div className="policy-detail-summary__meta-footer">
        <span className="policy-detail-summary__organization">
          {formatOrganization(policy)}
        </span>
        {policy.categories.length > 1 ? (
          <span className="policy-detail-summary__category-line">
            {policy.categories.map(getCategoryLabel).join(' · ')}
          </span>
        ) : null}
      </div>

      <PolicyDetailHeaderActions policy={policy} />
    </header>
  );
}
