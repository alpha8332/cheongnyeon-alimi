import { createBrowserRouter } from 'react-router';
import AppShellLayout from '@/layouts/AppShellLayout';
import AdminShellLayout from '@/layouts/AdminShellLayout';
import AdminProtectedRoute from '@/components/admin/AdminProtectedRoute';

// user 페이지
import HomePage from '@/pages/user/HomePage';
import SearchPage from '@/pages/user/SearchPage';
import PolicySearchPage from '@/pages/user/PolicySearchPage';
import RecommendationPage from '@/pages/user/RecommendationPage';
import ProgramDetailPage from '@/pages/user/ProgramDetailPage';
import FavoritesPage from '@/pages/user/FavoritesPage';
import NotificationsPage from '@/pages/user/NotificationsPage';
import CalendarPage from '@/pages/user/CalendarPage';

// admin 페이지
import DashboardPage from '@/pages/admin/DashboardPage';
import AdminLoginPage from '@/pages/admin/AdminLoginPage';
import CollectorPage from '@/pages/admin/CollectorPage';
import CollectionRunsPage from '@/pages/admin/CollectionRunsPage';
import CollectionRunDetailPage from '@/pages/admin/CollectionRunDetailPage';
import DataQualityPage from '@/pages/admin/DataQualityPage';
import AdminPolicyDataPage from '@/pages/admin/AdminPolicyDataPage';
import AdminLogsPage from '@/pages/admin/AdminLogsPage';

// 에러 페이지
import NotFoundPage from '@/components/common/NotFoundPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShellLayout />,
    errorElement: <NotFoundPage />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'search', element: <PolicySearchPage /> },
      { path: 'recommendations', element: <RecommendationPage /> },
      { path: 'programs', element: <SearchPage /> },
      { path: 'programs/:id', element: <ProgramDetailPage /> },
      { path: 'favorites', element: <FavoritesPage /> },
      { path: 'notifications', element: <NotificationsPage /> },
      { path: 'calendar', element: <CalendarPage /> },
      { path: 'admin/login', element: <AdminLoginPage /> },
      {
        path: 'admin',
        element: <AdminProtectedRoute />,
        children: [
          {
            element: <AdminShellLayout />,
            children: [
              { index: true, element: <DashboardPage /> },
              { path: 'collectors', element: <CollectorPage /> },
              { path: 'runs', element: <CollectionRunsPage /> },
              { path: 'runs/:runId', element: <CollectionRunDetailPage /> },
              { path: 'quality', element: <DataQualityPage /> },
              { path: 'policies', element: <AdminPolicyDataPage /> },
              { path: 'logs', element: <AdminLogsPage /> },
            ],
          },
        ],
      },
    ],
  },
]);
