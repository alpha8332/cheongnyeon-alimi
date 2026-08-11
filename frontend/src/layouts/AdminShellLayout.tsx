import { Link, Outlet, useLocation } from 'react-router';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';

function navClass(isActive: boolean): string {
  return `admin-shell__nav-link${isActive ? ' admin-shell__nav-link--active' : ''}`;
}

const ADMIN_NAV_ITEMS = [
  { to: ADMIN_APP_ROUTES.dashboard, label: '대시보드' },
  { to: ADMIN_APP_ROUTES.runs, label: '실행 기록' },
  { to: ADMIN_APP_ROUTES.collectors, label: '수집기' },
  { to: ADMIN_APP_ROUTES.quality, label: '데이터 품질' },
] as const;

export default function AdminShellLayout() {
  const { pathname } = useLocation();

  return (
    <div className="admin-shell">
      <header className="admin-shell__header">
        <div>
          <h1 className="admin-shell__title">관리자</h1>
          <p className="admin-shell__subtitle">
            CollectionRun·수집 관리 (FE3-00 route shell)
          </p>
        </div>
        <Link to={ADMIN_APP_ROUTES.login} className="admin-shell__login-link">
          로그인
        </Link>
      </header>

      <nav className="admin-shell__nav" aria-label="관리자 내비게이션">
        {ADMIN_NAV_ITEMS.map((item) => {
          const isActive =
            item.to === ADMIN_APP_ROUTES.dashboard
              ? pathname === item.to
              : pathname.startsWith(item.to);

          return (
            <Link
              key={item.to}
              to={item.to}
              className={navClass(isActive)}
              aria-current={isActive ? 'page' : undefined}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>

      <div className="admin-shell__content">
        <Outlet />
      </div>
    </div>
  );
}
