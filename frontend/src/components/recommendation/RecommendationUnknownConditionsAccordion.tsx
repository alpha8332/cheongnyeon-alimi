import { useId, useState } from 'react';

interface RecommendationUnknownConditionsAccordionProps {
  conditions: readonly string[];
}

export default function RecommendationUnknownConditionsAccordion({
  conditions,
}: RecommendationUnknownConditionsAccordionProps) {
  const [expanded, setExpanded] = useState(false);
  const panelId = useId();
  const count = conditions.length;

  if (count === 0) {
    return null;
  }

  return (
    <div className="recommendation-unknown-accordion">
      <button
        type="button"
        className="recommendation-unknown-accordion__toggle"
        aria-expanded={expanded}
        aria-controls={panelId}
        aria-label={`추가 확인 필요 ${count}건, ${expanded ? '접기' : '펼치기'}`}
        onClick={() => setExpanded((current) => !current)}
      >
        <span className="recommendation-unknown-accordion__label">
          추가 확인 필요 {count}건
        </span>
        <span className="recommendation-unknown-accordion__icon" aria-hidden="true">
          {expanded ? '▾' : '▸'}
        </span>
      </button>
      {expanded ? (
        <ul
          id={panelId}
          className="recommendation-unknown-accordion__list"
          role="list"
          aria-label="미확정 조건 목록"
        >
          {conditions.map((condition) => (
            <li key={condition} className="recommendation-unknown-accordion__item">
              {condition}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
