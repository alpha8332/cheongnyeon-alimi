import type { PolicyDto } from '@/types/policy';
import { getPolicyDetailStatusBadges } from '@/utils/policyDetailContent';

interface PolicyDetailStatusBadgesProps {
  policy: PolicyDto;
}

export default function PolicyDetailStatusBadges({
  policy,
}: PolicyDetailStatusBadgesProps) {
  const badges = getPolicyDetailStatusBadges(policy);

  return (
    <>
      {badges.map((badge) => (
        <span
          key={`${badge.variant}-${badge.label}`}
          className={`policy-status-badge policy-status-badge--${badge.variant}`}
        >
          {badge.label}
        </span>
      ))}
    </>
  );
}
