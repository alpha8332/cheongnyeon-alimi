import Button from '@/components/common/Button';
import type { RecommendationErrorPresentation } from '@/types/recommendationErrors';
import '@/components/policySearch/PolicySearchShell.css';

interface RecommendationErrorShellProps {
  presentation: RecommendationErrorPresentation;
  onRetry?: () => void;
}

export default function RecommendationErrorShell({
  presentation,
  onRetry,
}: RecommendationErrorShellProps) {
  return (
    <section
      className="policy-search-shell policy-search-shell--error"
      role="alert"
      aria-label="추천 오류"
    >
      <div className="policy-search-shell__icon" aria-hidden="true">
        ⚠️
      </div>
      <h2 className="policy-search-shell__title">{presentation.title}</h2>
      <p className="policy-search-shell__message">{presentation.message}</p>
      {presentation.retryable && onRetry ? (
        <div className="policy-search-shell__actions">
          <Button variant="primary" onClick={onRetry}>
            다시 시도
          </Button>
        </div>
      ) : null}
    </section>
  );
}
