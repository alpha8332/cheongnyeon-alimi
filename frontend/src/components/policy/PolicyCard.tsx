import { Link } from 'react-router';
import PartialBadge from '@/components/policy/PartialBadge';
import type { PolicyDto } from '@/types/policy';
import { buildProgramDetailRoutePath } from '@/utils/policyDetailNavigation';
import {
  formatAge,
  formatApplicationStatus,
  formatOrganization,
  formatRegion,
  getDDayLabel,
} from '@/utils/policyDisplay';

interface PolicyCardProps {
  policy: PolicyDto;
}

function getCardTag(policy: PolicyDto): { label: string; variant: '' | 'warn' | 'hot' } {
  if (policy.data_quality_status === 'partial') {
    return { label: '정보 미확인', variant: 'warn' };
  }

  const dDay = getDDayLabel(policy);
  if (dDay.startsWith('D-')) {
    const days = Number(dDay.replace('D-', ''));
    if (!Number.isNaN(days) && days <= 7) {
      return { label: '마감 임박', variant: 'hot' };
    }
  }

  if (policy.application_status === 'open') {
    return { label: '모집중', variant: '' };
  }

  if (policy.application_status) {
    return { label: formatApplicationStatus(policy.application_status), variant: '' };
  }

  return { label: '정책', variant: '' };
}

export default function PolicyCard({ policy }: PolicyCardProps) {
  const tag = getCardTag(policy);
  const detailPath = buildProgramDetailRoutePath(policy.id, {
    includePartial: policy.data_quality_status === 'partial',
  });

  return (
    <article className="policy-card">
      <div className="policy-card__visual">
        <span
          className={`policy-card__tag${tag.variant ? ` policy-card__tag--${tag.variant}` : ''}`}
        >
          {tag.label}
        </span>
      </div>
      <div className="policy-card__body">
        <h3 className="policy-card__title">
          <Link to={detailPath}>{policy.title}</Link>
          <PartialBadge policy={policy} />
        </h3>
        <p className="policy-card__meta">
          {[formatRegion(policy), formatOrganization(policy), getDDayLabel(policy)]
            .filter(Boolean)
            .join(' · ')}
        </p>
        <div className="policy-card__footer">
          <span className="policy-card__eligibility">
            {formatAge(policy)} · {formatRegion(policy)}
          </span>
          <Link to={detailPath} className="policy-card__arrow" aria-label="상세 보기">
            →
          </Link>
        </div>
      </div>
    </article>
  );
}
