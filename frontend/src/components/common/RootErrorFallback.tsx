import { useRouteError } from 'react-router';

export default function RootErrorFallback() {
  const error = useRouteError();
  console.error(error);

  // 버튼 클릭 시 홈으로 전체 새로고침 이동
  const handleGoHome = () => {
    window.location.href = '/';
  };

  return (
    <div>
      <div>일시적인 오류가 발생했습니다</div>
      <button type="button" onClick={handleGoHome}>
        홈으로 돌아가기
      </button>
    </div>
  );
}
