import type {
  BookmarkExplorerViewMode,
  BookmarkFolderSort,
} from '@/utils/bookmarkExplorer';

interface BreadcrumbSegment {
  label: string;
  onClick?: () => void;
}

interface BookmarkExplorerToolbarProps {
  breadcrumbs: BreadcrumbSegment[];
  sort: BookmarkFolderSort;
  viewMode: BookmarkExplorerViewMode;
  onSortChange: (sort: BookmarkFolderSort) => void;
  onViewModeChange: (mode: BookmarkExplorerViewMode) => void;
  showSortControls?: boolean;
}

export default function BookmarkExplorerToolbar({
  breadcrumbs,
  sort,
  viewMode,
  onSortChange,
  onViewModeChange,
  showSortControls = true,
}: BookmarkExplorerToolbarProps) {
  return (
    <div className="bookmark-explorer__toolbar">
      <nav className="bookmark-explorer__breadcrumb" aria-label="북마크 경로">
        {breadcrumbs.map((segment, index) => {
          const isLast = index === breadcrumbs.length - 1;

          return (
            <span key={`${segment.label}-${index}`} className="bookmark-explorer__crumb">
              {index > 0 ? (
                <span className="bookmark-explorer__crumb-sep" aria-hidden="true">
                  /
                </span>
              ) : null}
              {segment.onClick && !isLast ? (
                <button
                  type="button"
                  className="bookmark-explorer__crumb-btn"
                  onClick={segment.onClick}
                >
                  {index === 0 ? `< ${segment.label}` : segment.label}
                </button>
              ) : (
                <span
                  className="bookmark-explorer__crumb-current"
                  aria-current={isLast ? 'page' : undefined}
                >
                  {segment.label}
                </span>
              )}
            </span>
          );
        })}
      </nav>

      <div className="bookmark-explorer__controls">
        {showSortControls ? (
          <div
            className="bookmark-explorer__sort-tabs"
            role="tablist"
            aria-label="폴더 정렬"
          >
            <button
              type="button"
              role="tab"
              className={`bookmark-explorer__sort-btn${sort === 'name' ? ' bookmark-explorer__sort-btn--active' : ''}`}
              aria-selected={sort === 'name'}
              onClick={() => onSortChange('name')}
            >
              이름순
            </button>
            <button
              type="button"
              role="tab"
              className={`bookmark-explorer__sort-btn${sort === 'count' ? ' bookmark-explorer__sort-btn--active' : ''}`}
              aria-selected={sort === 'count'}
              onClick={() => onSortChange('count')}
            >
              담긴 개수순
            </button>
          </div>
        ) : null}

        <div
          className="bookmark-explorer__view-toggle"
          role="group"
          aria-label="보기 방식"
        >
          <button
            type="button"
            className={`bookmark-explorer__view-btn${viewMode === 'grid' ? ' bookmark-explorer__view-btn--active' : ''}`}
            aria-pressed={viewMode === 'grid'}
            aria-label="그리드 보기"
            title="그리드 보기"
            onClick={() => onViewModeChange('grid')}
          >
            ▦
          </button>
          <button
            type="button"
            className={`bookmark-explorer__view-btn${viewMode === 'list' ? ' bookmark-explorer__view-btn--active' : ''}`}
            aria-pressed={viewMode === 'list'}
            aria-label="리스트 보기"
            title="리스트 보기"
            onClick={() => onViewModeChange('list')}
          >
            ☰
          </button>
        </div>
      </div>
    </div>
  );
}
