import type { PolicySearchQueryParams } from '../types/policySearch.js';

const DEFAULT_PAGE = 1;

/** Total page count from Backend search envelope fields. */
export function getPolicySearchTotalPages(total: number, limit: number): number {
  if (total <= 0 || limit <= 0) {
    return 1;
  }

  return Math.ceil(total / limit);
}

/** Return URL state with a new 1-based page (clamped to >= 1). */
export function withPolicySearchPage<T extends { page: number }>(
  state: T,
  page: number,
): T {
  const safePage =
    Number.isFinite(page) && page >= 1 ? Math.floor(page) : DEFAULT_PAGE;

  return {
    ...state,
    page: safePage,
  };
}

/**
 * Guard against stale fetch results overwriting the current page view.
 * Compare response envelope `page`/`limit` to the active request.
 */
export function isPolicySearchResponseCurrent(
  response: Pick<PolicySearchQueryParams, 'page' | 'limit'>,
  request: Pick<PolicySearchQueryParams, 'page' | 'limit'>,
): boolean {
  return response.page === request.page && response.limit === request.limit;
}

/**
 * Build visible page numbers for pagination controls.
 * Returns 1-based page indices; totalPages <= 7 yields a full range.
 */
export function buildPolicySearchPageNumbers(
  currentPage: number,
  totalPages: number,
): number[] {
  if (totalPages <= 0) {
    return [1];
  }

  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages = new Set<number>([1, totalPages, currentPage]);

  if (currentPage > 1) {
    pages.add(currentPage - 1);
  }

  if (currentPage < totalPages) {
    pages.add(currentPage + 1);
  }

  if (currentPage <= 3) {
    pages.add(2);
    pages.add(3);
  }

  if (currentPage >= totalPages - 2) {
    pages.add(totalPages - 1);
    pages.add(totalPages - 2);
  }

  return [...pages].sort((left, right) => left - right);
}
