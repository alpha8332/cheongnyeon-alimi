import {
  buildPolicySearchPageNumbers,
  getPolicySearchTotalPages,
} from '@/utils/policySearchUrl';
import './SearchPagination.css';

interface SearchPaginationProps {
  total: number;
  page: number;
  limit: number;
  onPageChange: (page: number) => void;
  disabled?: boolean;
}

function formatResultRange(page: number, limit: number, total: number): string {
  if (total <= 0) {
    return '0건';
  }

  const start = (page - 1) * limit + 1;
  const end = Math.min(page * limit, total);
  return `${start.toLocaleString('ko-KR')}-${end.toLocaleString('ko-KR')} / ${total.toLocaleString('ko-KR')}건`;
}

export default function SearchPagination({
  total,
  page,
  limit,
  onPageChange,
  disabled = false,
}: SearchPaginationProps) {
  const totalPages = getPolicySearchTotalPages(total, limit);
  const pageNumbers = buildPolicySearchPageNumbers(page, totalPages);
  const canGoPrev = page > 1;
  const canGoNext = page < totalPages;

  if (totalPages <= 1) {
    return null;
  }

  return (
    <nav
      className="search-pagination"
      aria-label="검색 결과 페이지"
    >
      <p className="search-pagination__summary">
        {formatResultRange(page, limit, total)} · 페이지 {page} / {totalPages}
      </p>

      <div className="search-pagination__controls">
        <button
          type="button"
          className="search-pagination__nav"
          onClick={() => onPageChange(page - 1)}
          disabled={disabled || !canGoPrev}
          aria-label="이전 페이지"
        >
          ← 이전
        </button>

        {pageNumbers.map((pageNumber, index) => {
          const previousPageNumber = pageNumbers[index - 1];
          const showEllipsis =
            previousPageNumber !== undefined && pageNumber - previousPageNumber > 1;

          return (
            <span key={pageNumber} style={{ display: 'contents' }}>
              {showEllipsis ? (
                <span className="search-pagination__ellipsis" aria-hidden="true">
                  …
                </span>
              ) : null}
              <button
                type="button"
                className={
                  pageNumber === page
                    ? 'search-pagination__page search-pagination__page--active'
                    : 'search-pagination__page'
                }
                onClick={() => onPageChange(pageNumber)}
                disabled={disabled || pageNumber === page}
                aria-current={pageNumber === page ? 'page' : undefined}
                aria-label={`${pageNumber}페이지`}
              >
                {pageNumber}
              </button>
            </span>
          );
        })}

        <button
          type="button"
          className="search-pagination__nav"
          onClick={() => onPageChange(page + 1)}
          disabled={disabled || !canGoNext}
          aria-label="다음 페이지"
        >
          다음 →
        </button>
      </div>
    </nav>
  );
}
