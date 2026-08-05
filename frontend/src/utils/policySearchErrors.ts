import axios from 'axios';
import { PolicySearchApiError } from '../api/policySearchApiError.js';
import type { PolicySearchResponse } from '../types/policySearch.js';
import type {
  PolicySearchClientErrorKind,
  PolicySearchErrorPresentation,
} from '../types/policySearchErrors.js';

/** Golden Query Empty UX copy (Forest plan FE4-03 / FE4-15). */
export const POLICY_SEARCH_EMPTY_RESULTS_COPY = {
  title: '조건에 맞는 정책을 찾지 못했습니다',
  message:
    '입력하신 조건에 해당하는 정책이 현재 제공 데이터에서 검색되지 않았습니다. ' +
    '이는 해당 정책이 존재하지 않는다는 뜻이 아닙니다. ' +
    '검색어·지역·연령 등 조건을 바꿔 다시 시도해 보세요.',
  scopeNote:
    'Release 1 검색 데이터는 canonical Seed 기반이며, 실제 전국·전체 정책과 ' +
    '차이가 있을 수 있습니다.',
} as const;

const VALIDATION_COPY: PolicySearchErrorPresentation = {
  kind: 'validation',
  title: '검색 조건을 확인해 주세요',
  message:
    '검색어(q)가 비어 있거나 허용 범위를 벗어났습니다. ' +
    '검색어를 입력하고 다시 시도해 주세요.',
  retryable: false,
  preserve_filter_chips: true,
};

const SERVER_COPY: PolicySearchErrorPresentation = {
  kind: 'server',
  title: '검색 서버 오류',
  message:
    '일시적인 서버 오류로 검색 결과를 불러오지 못했습니다. ' +
    '잠시 후 다시 시도해 주세요.',
  retryable: true,
  preserve_filter_chips: true,
};

const NETWORK_COPY: PolicySearchErrorPresentation = {
  kind: 'network',
  title: '네트워크 연결 오류',
  message:
    '네트워크 연결을 확인한 뒤 다시 시도해 주세요.',
  retryable: true,
  preserve_filter_chips: true,
};

function summarizeInterpretedConditions(
  response: PolicySearchResponse,
): string | null {
  const { interpreted_conditions: interpreted } = response;
  const parts: string[] = [];

  if (interpreted.conditions.length > 0) {
    const labels = interpreted.conditions.map(
      (condition: PolicySearchResponse['interpreted_conditions']['conditions'][number]) =>
        `${condition.dimension}: ${String(condition.value)}`,
    );
    parts.push(`해석된 조건 — ${labels.join(', ')}`);
  }

  if (interpreted.uninterpreted_terms.length > 0) {
    parts.push(
      `미해석 키워드 — ${interpreted.uninterpreted_terms.join(', ')}`,
    );
  }

  return parts.length > 0 ? parts.join(' · ') : null;
}

/** Map 200 response with zero hits to empty_results presentation. */
export function mapPolicySearchEmptyResults(
  response: PolicySearchResponse,
): PolicySearchErrorPresentation {
  const interpretedSummary = summarizeInterpretedConditions(response);

  return {
    kind: 'empty_results',
    title: POLICY_SEARCH_EMPTY_RESULTS_COPY.title,
    message: [
      POLICY_SEARCH_EMPTY_RESULTS_COPY.message,
      interpretedSummary,
      POLICY_SEARCH_EMPTY_RESULTS_COPY.scopeNote,
    ]
      .filter(Boolean)
      .join(' '),
    retryable: false,
    preserve_filter_chips: true,
  };
}

function mapHttpStatus(
  status: number,
  detail?: string,
): PolicySearchErrorPresentation {
  if (status === 422) {
    return {
      ...VALIDATION_COPY,
      message: detail ?? VALIDATION_COPY.message,
    };
  }

  if (status === 400) {
    return {
      kind: 'bad_request',
      title: '검색 조건을 해석할 수 없습니다',
      message:
        detail ??
        '입력하신 조건을 해석하지 못했습니다. 검색어·필터를 수정해 주세요.',
      retryable: false,
      preserve_filter_chips: true,
    };
  }

  if (status === 404) {
    return {
      kind: 'not_found',
      title: '검색 API를 찾을 수 없습니다',
      message: detail ?? '요청한 검색 경로가 올바르지 않습니다.',
      retryable: false,
      preserve_filter_chips: false,
    };
  }

  if (status >= 500) {
    return {
      ...SERVER_COPY,
      message: detail ?? SERVER_COPY.message,
    };
  }

  if (status === 0) {
    return NETWORK_COPY;
  }

  return {
    kind: 'server',
    title: '검색 요청 실패',
    message: detail ?? '검색 요청을 처리하지 못했습니다.',
    retryable: true,
    preserve_filter_chips: true,
  };
}

/** Map fetch/query errors to FE4-03 Error UX presentation. */
export function mapPolicySearchError(
  error: unknown,
): PolicySearchErrorPresentation {
  if (error instanceof PolicySearchApiError) {
    return mapHttpStatus(error.status, error.detail);
  }

  if (axios.isAxiosError(error)) {
    const status = error.response?.status ?? 0;
    const detail =
      typeof error.response?.data === 'object' &&
      error.response?.data !== null &&
      'detail' in error.response.data &&
      typeof (error.response.data as { detail: unknown }).detail === 'string'
        ? (error.response.data as { detail: string }).detail
        : error.message;

    return mapHttpStatus(status, detail);
  }

  if (error instanceof Error) {
    return {
      ...NETWORK_COPY,
      message: error.message || NETWORK_COPY.message,
    };
  }

  return SERVER_COPY;
}

export function isPolicySearchEmptyResults(
  response: PolicySearchResponse,
): boolean {
  return response.total === 0 && response.items.length === 0;
}

export type { PolicySearchClientErrorKind, PolicySearchErrorPresentation };
