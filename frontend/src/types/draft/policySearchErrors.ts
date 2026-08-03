/**
 * W3-F0 DRAFT — HTTP error and empty-state UX mapping (G1 pending).
 */

export type PolicySearchClientErrorKind =
  | 'empty_query'
  | 'empty_results'
  | 'not_found'
  | 'validation'
  | 'server'
  | 'network';

export interface PolicySearchErrorPresentationDraft {
  kind: PolicySearchClientErrorKind;
  title: string;
  message: string;
  /** When true, show primary "다시 시도" action. */
  retryable: boolean;
  /** When true, keep interpreted chips visible for user edit. */
  preserve_interpreted_conditions: boolean;
}

export function mapHttpStatusToSearchErrorDraft(
  status: number | undefined,
): PolicySearchErrorPresentationDraft {
  if (status === 422) {
    return {
      kind: 'validation',
      title: '검색 조건을 확인해 주세요',
      message:
        '입력한 검색어나 필터 형식이 올바르지 않습니다. 조건을 수정한 뒤 다시 시도해 주세요.',
      retryable: false,
      preserve_interpreted_conditions: true,
    };
  }

  if (status === 404) {
    return {
      kind: 'not_found',
      title: '검색을 처리할 수 없습니다',
      message: '요청한 검색 경로를 찾을 수 없습니다. Gate G1 승인 후 API 연결을 확인하세요.',
      retryable: false,
      preserve_interpreted_conditions: false,
    };
  }

  if (status !== undefined && status >= 500) {
    return {
      kind: 'server',
      title: '일시적인 오류가 발생했습니다',
      message: '잠시 후 다시 시도해 주세요.',
      retryable: true,
      preserve_interpreted_conditions: true,
    };
  }

  return {
    kind: 'network',
    title: '검색 요청에 실패했습니다',
    message: '네트워크 연결을 확인한 뒤 다시 시도해 주세요.',
    retryable: true,
    preserve_interpreted_conditions: true,
  };
}

export const EMPTY_QUERY_ERROR_DRAFT: PolicySearchErrorPresentationDraft = {
  kind: 'empty_query',
  title: '검색어를 입력해 주세요',
  message: '찾고 싶은 지원 조건이나 정책 키워드를 입력해 주세요.',
  retryable: false,
  preserve_interpreted_conditions: false,
};

export const EMPTY_RESULTS_ERROR_DRAFT: PolicySearchErrorPresentationDraft = {
  kind: 'empty_results',
  title: '조건에 맞는 정책이 없습니다',
  message:
    '해석된 조건을 수정하거나 미확인 조건을 포함해 다시 검색해 보세요. partial 정책 포함 옵션도 확인해 주세요.',
  retryable: false,
  preserve_interpreted_conditions: true,
};
