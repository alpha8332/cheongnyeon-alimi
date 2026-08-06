import './PolicySearchShell.css';

export default function PolicySearchLoadingShell() {
  return (
    <section
      className="policy-search-shell policy-search-shell--loading"
      aria-busy="true"
      aria-label="검색 결과 로딩 중"
    >
      <div className="policy-search-loading-spinner" aria-hidden="true">
        <span className="policy-search-loading-spinner__ring" />
      </div>

      <div className="cards-grid">
        {Array.from({ length: 3 }, (_, index) => (
          <div
            key={index}
            className="policy-search-skeleton-card"
            aria-hidden="true"
          >
            <div className="policy-search-skeleton-card__visual" />
            <div className="policy-search-skeleton-card__body">
              <div className="policy-search-skeleton policy-search-skeleton--line-lg" />
              <div className="policy-search-skeleton policy-search-skeleton--line-sm" />
              <div className="policy-search-skeleton policy-search-skeleton--line-xs" />
            </div>
          </div>
        ))}
      </div>

      <p className="policy-search-shell__status">검색 결과를 불러오는 중입니다…</p>
    </section>
  );
}
