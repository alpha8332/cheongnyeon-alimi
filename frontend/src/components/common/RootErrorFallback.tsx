import { isRouteErrorResponse, useRouteError } from 'react-router';
import Button from '@/components/common/Button';

export default function RootErrorFallback() {
  const error = useRouteError();

  if (isRouteErrorResponse(error) && error.status === 404) {
    return (
      <div className="page placeholder-page">
        <h1 className="placeholder-page__title">404</h1>
        <p>페이지를 찾을 수 없습니다.</p>
        <div style={{ marginTop: '20px' }}>
          <Button type="button" variant="secondary" onClick={() => {
            window.location.href = '/';
          }}>
            메인 홈으로 돌아가기
          </Button>
        </div>
      </div>
    );
  }

  console.error('[RootErrorFallback]', error);

  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <div className="page layout-error-boundary" role="alert">
      <h1 className="layout-error-boundary__title">일시적인 오류가 발생했습니다</h1>
      <p className="layout-error-boundary__message">
        화면을 불러오는 중 문제가 발생했습니다. 새로고침하거나 홈으로
        돌아가 주세요.
      </p>
      <div className="layout-error-boundary__actions">
        <Button type="button" onClick={() => window.location.reload()}>
          새로고침
        </Button>
        <Button type="button" variant="secondary" onClick={handleGoHome}>
          홈으로 돌아가기
        </Button>
      </div>
    </div>
  );
}
