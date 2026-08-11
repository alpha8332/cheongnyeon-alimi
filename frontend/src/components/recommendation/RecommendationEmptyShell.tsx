import type { RecommendationErrorPresentation } from '@/types/recommendationErrors';
import '@/components/policySearch/PolicySearchShell.css';

interface RecommendationEmptyShellProps {
  presentation: RecommendationErrorPresentation;
}

export default function RecommendationEmptyShell({
  presentation,
}: RecommendationEmptyShellProps) {
  return (
    <section
      className="policy-search-shell policy-search-shell--empty"
      aria-label="추천 결과 없음"
    >
      <div className="policy-search-shell__icon" aria-hidden="true">
        🎯
      </div>
      <h2 className="policy-search-shell__title">{presentation.title}</h2>
      <p className="policy-search-shell__message">{presentation.message}</p>
      <ul className="policy-search-shell__tips">
        <li>지역·연령·관심 분야 조건을 수정한 뒤 다시 추천 받기를 눌러 보세요.</li>
        <li>결과가 없다고 해당 정책이 없다고 단정하지 않습니다.</li>
      </ul>
    </section>
  );
}
