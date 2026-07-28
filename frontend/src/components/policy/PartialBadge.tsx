import type { NormalizedProgram } from '@/types/policy';

interface PartialBadgeProps {
  program: NormalizedProgram;
}

export default function PartialBadge({ program }: PartialBadgeProps) {
  if (program.data_quality_status !== 'partial') {
    return null;
  }

  return (
    <span
      style={{
        border: '1px solid black',
        padding: '2px 6px',
        marginLeft: '8px',
        fontSize: '12px',
      }}
    >
      정보 일부 누락
    </span>
  );
}
