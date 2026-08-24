import RecommendationResultCard from '@/components/recommendation/RecommendationResultCard';
import type { RecommendationResponse } from '@/types/recommendation';
import { RECOMMENDATION_DEFAULT_DISCLAIMER } from '@/types/recommendation';

interface RecommendationResultListProps {
  response: RecommendationResponse;
}

export default function RecommendationResultList({
  response,
}: RecommendationResultListProps) {
  const disclaimer =
    response.items[0]?.disclaimer?.trim() || RECOMMENDATION_DEFAULT_DISCLAIMER;

  return (
    <section className="recommendation-result-list" aria-label="추천 결과">
      <header className="recommendation-result-list__header">
        <h2 className="recommendation-result-list__title">
          추천 정책 {response.total}건
        </h2>
        <p className="recommendation-result-list__meta">
          평가 시각: {new Date(response.evaluated_at).toLocaleString('ko-KR')}
        </p>
      </header>

      <p role="note" className="policy-eligibility-notice recommendation-result-list__disclaimer">
        {disclaimer}
      </p>

      <div className="cards-grid">
        {response.items.map((item) => (
          <RecommendationResultCard key={item.id} item={item} />
        ))}
      </div>
    </section>
  );
}
