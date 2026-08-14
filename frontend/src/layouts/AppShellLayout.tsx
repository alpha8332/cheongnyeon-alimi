import { Link, Outlet, useLocation } from 'react-router';
import ApiErrorToastProvider from '@/components/common/ApiErrorToastProvider';
import LayoutErrorBoundary from '@/components/common/LayoutErrorBoundary';
import UserLocalStorageRecoveryBanner from '@/components/user/UserLocalStorageRecoveryBanner';

function navClass(isActive: boolean): string {
  return `app-shell__nav-btn${isActive ? ' app-shell__nav-btn--active' : ''}`;
}

export default function AppShellLayout() {
  const { pathname } = useLocation();

  const isHome = pathname === '/';
  const isSearch = pathname.startsWith('/search');
  const isRecommendations = pathname.startsWith('/recommendations');
  const isPrograms = pathname.startsWith('/programs');
  const isFavorites = pathname.startsWith('/favorites');
  const isNotifications = pathname.startsWith('/notifications');
  const isCalendar = pathname.startsWith('/calendar');
  const isAdmin = pathname.startsWith('/admin');

  return (
    <ApiErrorToastProvider>
    <div className="app-shell">
      <nav className="app-shell__sidebar" aria-label="메인 내비게이션">
        <Link to="/" className="app-shell__logo" title="청년알리미">
          ✦
        </Link>
        <Link to="/" className={navClass(isHome)} title="홈" aria-label="홈">
          🏠
        </Link>
        <Link
          to="/search"
          className={navClass(isSearch)}
          title="정책 검색"
          aria-label="정책 검색"
        >
          🔍
        </Link>
        <Link
          to="/recommendations"
          className={navClass(isRecommendations)}
          title="맞춤 추천"
          aria-label="맞춤 추천"
        >
          🎯
        </Link>
        <Link
          to="/programs"
          className={navClass(isPrograms)}
          title="정책 목록"
          aria-label="정책 목록"
        >
          📋
        </Link>
        <Link
          to="/favorites"
          className={navClass(isFavorites)}
          title="북마크"
          aria-label="북마크"
        >
          🔖
        </Link>
        <Link
          to="/calendar"
          className={navClass(isCalendar)}
          title="마감 달력"
          aria-label="마감 달력"
        >
          📅
        </Link>
        <Link
          to="/notifications"
          className={navClass(isNotifications)}
          title="알림"
          aria-label="알림"
        >
          🔔
        </Link>
        <div className="app-shell__spacer" />
        <Link
          to="/admin"
          className={navClass(isAdmin)}
          title="관리"
          aria-label="관리"
        >
          📊
        </Link>
        <span className="app-shell__avatar" title="프로필">
          Y
        </span>
      </nav>

      <main className="app-shell__main">
        <LayoutErrorBoundary fallbackTitle="저장 데이터 안내를 표시하지 못했습니다">
          <UserLocalStorageRecoveryBanner />
        </LayoutErrorBoundary>
        <LayoutErrorBoundary>
          <Outlet />
        </LayoutErrorBoundary>
      </main>
    </div>
    </ApiErrorToastProvider>
  );
}
