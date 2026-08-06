import './PolicySearchSidebar.css';

interface UnconfirmedBannerProps {
  warnings: string[];
}

export default function UnconfirmedBanner({ warnings }: UnconfirmedBannerProps) {
  if (warnings.length === 0) {
    return null;
  }

  return (
    <section
      className="policy-search-query-warning panel"
      aria-label="검색 조건 해석 경고"
    >
      <h3 className="panel-title">⚠️ 조건 해석 주의</h3>
      <ul className="policy-search-query-warning__list">
        {warnings.map((warning) => (
          <li key={warning}>{warning}</li>
        ))}
      </ul>
    </section>
  );
}
