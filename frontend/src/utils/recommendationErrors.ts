import axios from 'axios';
import { RecommendationApiError } from '../api/recommendationApiError.js';
import type { RecommendationResponse } from '../types/recommendation.js';
import type { RecommendationErrorPresentation } from '../types/recommendationErrors.js';

export const RECOMMENDATION_EMPTY_RESULTS_COPY = {
  title: '입력 조건에 맞는 추천 정책이 없습니다',
  message:
    '저장한 지역·연령·관심 분야 조건에 해당하는 정책 후보가 현재 데이터에서 ' +
    '찾아지지 않았습니다. 조건을 바꾸거나 일부 항목을 비워 다시 시도해 보세요.',
  scopeNote:
    '추천 결과는 자격 충족이나 수혜 가능성을 확정하지 않으며, 제공 데이터 범위 ' +
    '밖의 정책은 포함되지 않을 수 있습니다.',
} as const;

const VALIDATION_COPY: RecommendationErrorPresentation = {
  kind: 'validation',
  title: '추천 조건을 확인해 주세요',
  message:
    '연령·limit 등 입력값이 허용 범위를 벗어났습니다. 조건을 수정한 뒤 다시 시도해 주세요.',
  retryable: false,
};

const SERVER_COPY: RecommendationErrorPresentation = {
  kind: 'server',
  title: '추천 서버 오류',
  message:
    '일시적인 서버 오류로 추천 결과를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.',
  retryable: true,
};

const NETWORK_COPY: RecommendationErrorPresentation = {
  kind: 'network',
  title: '네트워크 연결 오류',
  message: '네트워크 연결을 확인한 뒤 다시 시도해 주세요.',
  retryable: true,
};

function mapHttpStatus(
  status: number,
  detail?: string,
): RecommendationErrorPresentation {
  if (status === 422) {
    return {
      ...VALIDATION_COPY,
      message: detail ?? VALIDATION_COPY.message,
    };
  }

  if (status === 400) {
    return {
      kind: 'bad_request',
      title: '추천 조건을 해석할 수 없습니다',
      message:
        detail ??
        '입력하신 조건을 해석하지 못했습니다. 지역·연령·관심 분야를 수정해 주세요.',
      retryable: false,
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
    title: '추천 요청 실패',
    message: detail ?? '추천 요청을 처리하지 못했습니다.',
    retryable: true,
  };
}

export function mapRecommendationError(
  error: unknown,
): RecommendationErrorPresentation {
  if (error instanceof RecommendationApiError) {
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

export function mapRecommendationEmptyResults(): RecommendationErrorPresentation {
  return {
    kind: 'empty_results',
    title: RECOMMENDATION_EMPTY_RESULTS_COPY.title,
    message: [
      RECOMMENDATION_EMPTY_RESULTS_COPY.message,
      RECOMMENDATION_EMPTY_RESULTS_COPY.scopeNote,
    ].join(' '),
    retryable: false,
  };
}

export function isRecommendationEmptyResults(
  response: RecommendationResponse,
): boolean {
  return response.total === 0 && response.items.length === 0;
}
