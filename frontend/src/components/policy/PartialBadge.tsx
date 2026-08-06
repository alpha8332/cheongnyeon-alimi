import type { PolicyDto } from '@/types/policy';
import {
  PARTIAL_QUALITY_BADGE_HELP,
  PARTIAL_QUALITY_BADGE_LABEL,
} from '@/constants/policySearchDisplay';

interface PartialBadgeProps {
  policy: PolicyDto;
}

export default function PartialBadge({ policy }: PartialBadgeProps) {
  if (policy.data_quality_status !== 'partial') {
    return null;
  }

  return (
    <span className="badge-partial" title={PARTIAL_QUALITY_BADGE_HELP}>
      {PARTIAL_QUALITY_BADGE_LABEL}
    </span>
  );
}
