import { Link } from 'react-router';
import Button from '@/components/common/Button';

export default function NotFoundPage() {
  return (
    <div className="page placeholder-page">
      <h1 className="placeholder-page__title">404</h1>
      <p>페이지를 찾을 수 없습니다.</p>
      <div style={{ marginTop: '20px' }}>
        <Link to="/">
          <Button variant="secondary">메인 홈으로 돌아가기</Button>
        </Link>
      </div>
    </div>
  );
}
