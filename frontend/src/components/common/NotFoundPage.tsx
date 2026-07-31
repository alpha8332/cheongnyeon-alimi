import { Link } from 'react-router';

export default function NotFoundPage() {
  return (
    <div>
      <div>404 - 페이지를 찾을 수 없습니다</div>
      <Link to="/"><button type="button">메인 홈으로 돌아가기</button></Link>
    </div>
  );
}
