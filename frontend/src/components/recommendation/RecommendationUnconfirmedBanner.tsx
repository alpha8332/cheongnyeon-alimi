import type { RecommendationResponse } from '@/types/recommendation';
import { buildRecommendationQueryWarningMessage } from '@/utils/recommendationReasonHelpers';

interface RecommendationUnconfirmedBannerProps {
  response: RecommendationResponse;
}

export default function RecommendationUnconfirmedBanner({
  response,
}: RecommendationUnconfirmedBannerProps) {
  const message = buildRecommendationQueryWarningMessage(response);

  if (!message) {
    return null;
  }

  return (
    <div
      className="recommendation-unconfirmed-banner"
      role="note"
      aria-label="미확정 조건 안내"
    >
      <strong className="recommendation-unconfirmed-banner__title">
        추가 확인 필요
      </strong>
      <p className="recommendation-unconfirmed-banner__message">{message}</p>
    </div>
  );
}
