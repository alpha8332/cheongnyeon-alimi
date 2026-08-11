import { useCallback, useState } from 'react';
import { Link } from 'react-router';
import RecommendationConditionForm from '@/components/recommendation/RecommendationConditionForm';
import RecommendationEmptyShell from '@/components/recommendation/RecommendationEmptyShell';
import RecommendationErrorShell from '@/components/recommendation/RecommendationErrorShell';
import RecommendationLoadingShell from '@/components/recommendation/RecommendationLoadingShell';
import RecommendationResultList from '@/components/recommendation/RecommendationResultList';
import RecommendationUnconfirmedBanner from '@/components/recommendation/RecommendationUnconfirmedBanner';
import { postRecommendations } from '@/api/recommendation';
import type { RecommendationResponse } from '@/types/recommendation';
import { RECOMMENDATION_APP_ROUTE } from '@/types/recommendation';
import type { UserSavedConditions } from '@/types/userLocalStorage';
import {
  isRecommendationEmptyResults,
  mapRecommendationEmptyResults,
  mapRecommendationError,
} from '@/utils/recommendationErrors';
import { toRecommendationRequestFromConditions } from '@/utils/savedConditionsForm';
import { USER_CROSS_ROUTE_PATHS } from '@/utils/userRouteIdentity';

type FetchPhase = 'idle' | 'loading' | 'success' | 'error';

export default function RecommendationPage() {
  const [phase, setPhase] = useState<FetchPhase>('idle');
  const [response, setResponse] = useState<RecommendationResponse | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [lastRequest, setLastRequest] = useState<UserSavedConditions | null>(
    null,
  );

  const fetchRecommendations = useCallback(
    async (conditions: UserSavedConditions) => {
      setPhase('loading');
      setError(null);
      setLastRequest(conditions);

      try {
        const data = await postRecommendations(
          toRecommendationRequestFromConditions(conditions),
        );
        setResponse(data);
        setPhase('success');
      } catch (nextError) {
        setError(nextError);
        setResponse(null);
        setPhase('error');
      }
    },
    [],
  );

  const handleRetry = () => {
    if (lastRequest) {
      void fetchRecommendations(lastRequest);
    }
  };

  const showEmpty =
    phase === 'success' && response !== null && isRecommendationEmptyResults(response);
  const showResults =
    phase === 'success' && response !== null && !isRecommendationEmptyResults(response);
  const showError = phase === 'error';

  return (
    <div className="page recommendation-page">
      <header className="greeting">
        <h1 className="greeting__title">맞춤 추천</h1>
        <p className="greeting__subtitle">
          저장한 지역·연령·관심 분야 조건으로 정책 후보를 추천합니다.
        </p>
      </header>

      <p role="note" className="policy-eligibility-notice">
        추천 결과는 자격 충족이나 수혜 가능성을 확정하지 않습니다. 자연어 검색은{' '}
        <Link to={USER_CROSS_ROUTE_PATHS.search}>/search</Link> route를
        사용하세요. 이 route(<code>{RECOMMENDATION_APP_ROUTE}</code>)는 구조화
        조건 추천 전용입니다.
      </p>

      <RecommendationConditionForm
        onSubmit={(conditions) => void fetchRecommendations(conditions)}
        isSubmitting={phase === 'loading'}
      />

      {phase === 'loading' ? <RecommendationLoadingShell /> : null}

      {showError ? (
        <RecommendationErrorShell
          presentation={mapRecommendationError(error)}
          onRetry={
            mapRecommendationError(error).retryable ? handleRetry : undefined
          }
        />
      ) : null}

      {showEmpty ? (
        <RecommendationEmptyShell presentation={mapRecommendationEmptyResults()} />
      ) : null}

      {showResults && response ? (
        <>
          <RecommendationUnconfirmedBanner response={response} />
          <RecommendationResultList response={response} />
        </>
      ) : null}
    </div>
  );
}
