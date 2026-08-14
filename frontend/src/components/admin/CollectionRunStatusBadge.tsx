import type { CollectionRunStatus } from '@/types/collectionRun';
import { getCollectionRunStatusLabel } from '@/utils/collectionRunDisplay';

interface CollectionRunStatusBadgeProps {
  status: CollectionRunStatus;
  isStale?: boolean;
}

function getStatusVariant(status: CollectionRunStatus): string {
  switch (status) {
    case 'running':
      return 'running';
    case 'succeeded':
      return 'succeeded';
    case 'partial_failure':
      return 'partial';
    case 'failed':
      return 'failed';
    default:
      return 'neutral';
  }
}

export default function CollectionRunStatusBadge({
  status,
  isStale = false,
}: CollectionRunStatusBadgeProps) {
  const variant = getStatusVariant(status);

  return (
    <span className="collection-run-badges">
      <span
        className={`collection-run-badge collection-run-badge--${variant}`}
        aria-label={`상태: ${getCollectionRunStatusLabel(status)}`}
      >
        {getCollectionRunStatusLabel(status)}
      </span>
      {isStale ? (
        <span
          className="collection-run-badge collection-run-badge--stale"
          role="note"
          aria-label="Stale 실행"
        >
          Stale
        </span>
      ) : null}
    </span>
  );
}
