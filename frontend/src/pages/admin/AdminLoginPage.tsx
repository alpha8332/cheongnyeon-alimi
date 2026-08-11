import { Link } from 'react-router';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';

export default function AdminLoginPage() {
  return (
    <div className="page placeholder-page">
      <h1 className="placeholder-page__title">관리자 로그인</h1>
      <p>
        4자리 PIN 로그인 UI는 FE3-01에서 구현합니다. API 계약(FE3-00)은 Mock
        session handler로 준비되어 있습니다.
      </p>
      <p className="hint-text">
        PIN·access token은 URL·로그·영구 localStorage에 저장하지 않습니다.
      </p>
      <div style={{ marginTop: '20px' }}>
        <Link to={ADMIN_APP_ROUTES.dashboard}>관리자 홈으로</Link>
      </div>
    </div>
  );
}
