import type { PolicyDto } from '@/types/policy';
import { getPolicyStatusBadge } from '@/utils/policyDetailContent';

interface PolicyStatusBadgeProps {
  policy: PolicyDto;
  compact?: boolean;
}

export default function PolicyStatusBadge({
  policy,
  compact = false,
}: PolicyStatusBadgeProps) {
  const badge = getPolicyStatusBadge(policy);

  return (
    <span
      className={`policy-status-badge policy-status-badge--${badge.variant}${compact ? ' policy-status-badge--compact' : ''}`}
    >
      {badge.label}
    </span>
  );
}
