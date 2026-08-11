import { Navigate, Outlet, useLocation } from 'react-router';
import { ADMIN_APP_ROUTES } from '@/api/adminRequest';
import { useAdminSession } from '@/hooks/useAdminSession';

export default function AdminProtectedRoute() {
  const { isAuthenticated } = useAdminSession();
  const location = useLocation();

  if (!isAuthenticated) {
    return (
      <Navigate
        to={ADMIN_APP_ROUTES.login}
        replace
        state={{ from: location.pathname }}
      />
    );
  }

  return <Outlet />;
}
