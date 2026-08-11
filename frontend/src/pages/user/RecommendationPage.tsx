import { Link } from 'react-router';
import { RECOMMENDATION_APP_ROUTE } from '@/types/recommendation';

export default function RecommendationPage() {
  return (
    <div className="page placeholder-page">
      <h1 className="placeholder-page__title">맞춤 추천</h1>
      <p role="note" className="policy-eligibility-notice">
        추천 결과는 자격 충족이나 수혜 가능성을 확정하지 않습니다. 조건 입력·결과
        UI는 FE6-01~02에서 구현합니다.
      </p>
      <p>
        이 route(<code>{RECOMMENDATION_APP_ROUTE}</code>)는 자연어 검색(
        <Link to="/search">/search</Link>)과 분리된 맞춤 추천 전용 경로입니다.
      </p>
    </div>
  );
}
