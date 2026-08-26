import { useId, useState } from 'react';

const DEFAULT_MAX_VISIBLE = 2;

interface RegionListCollapseProps {
  regions: string[];
  fallback?: string | null;
  maxVisible?: number;
  className?: string;
}

export default function RegionListCollapse({
  regions,
  fallback = null,
  maxVisible = DEFAULT_MAX_VISIBLE,
  className = '',
}: RegionListCollapseProps) {
  const controlId = useId();
  const [expanded, setExpanded] = useState(false);

  if (regions.length === 0) {
    return <span className={className}>{fallback ?? '지역 미정'}</span>;
  }

  const visibleCount = Math.max(1, Math.floor(maxVisible));
  const needsCollapse = regions.length > visibleCount;
  const visibleRegions = expanded ? regions : regions.slice(0, visibleCount);
  const hiddenCount = regions.length - visibleCount;

  return (
    <span className={`region-list-collapse${className ? ` ${className}` : ''}`}>
      <span id={controlId}>{visibleRegions.join(', ')}</span>
      {needsCollapse ? (
        <>
          {!expanded && hiddenCount > 0 ? (
            <span className="region-list-collapse__more" aria-hidden="true">
              {' '}
              외 {hiddenCount}곳
            </span>
          ) : null}
          <button
            type="button"
            className="region-list-collapse__toggle"
            aria-expanded={expanded}
            aria-controls={controlId}
            onClick={() => setExpanded((current) => !current)}
          >
            {expanded ? '접기' : '더 보기'}
          </button>
        </>
      ) : null}
    </span>
  );
}
