import { Link, useParams } from 'react-router';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';

export default function CollectionRunDetailPage() {
  const { runId = '' } = useParams();

  return (
    <div className="page placeholder-page">
      <h1 className="placeholder-page__title">실행 상세</h1>
      <p>
        CollectionRun 상세·stale 표시는 FE3-03에서 구현합니다. run id:{' '}
        <code>{runId}</code>
      </p>
      <div style={{ marginTop: '20px' }}>
        <Link to={ADMIN_APP_ROUTES.runs}>실행 기록 목록</Link>
      </div>
    </div>
  );
}
