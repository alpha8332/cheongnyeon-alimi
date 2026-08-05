import type { PolicyDto } from '@/types/policy';

interface PartialBadgeProps {
  policy: PolicyDto;
}

export default function PartialBadge({ policy }: PartialBadgeProps) {
  if (policy.data_quality_status !== 'partial') {
    return null;
  }

  return <span className="badge-partial">정보 미확인</span>;
}
