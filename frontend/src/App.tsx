import { createBrowserRouter } from 'react-router';
import AppShellLayout from '@/layouts/AppShellLayout';

// user 페이지
import HomePage from '@/pages/user/HomePage';
import SearchPage from '@/pages/user/SearchPage';
import PolicySearchPage from '@/pages/user/PolicySearchPage';
import ProgramDetailPage from '@/pages/user/ProgramDetailPage';
import FavoritesPage from '@/pages/user/FavoritesPage';
import NotificationsPage from '@/pages/user/NotificationsPage';

// admin 페이지
import DashboardPage from '@/pages/admin/DashboardPage';
import CollectorPage from '@/pages/admin/CollectorPage';
import CollectionRunsPage from '@/pages/admin/CollectionRunsPage';
import DataQualityPage from '@/pages/admin/DataQualityPage';

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
      { path: 'programs', element: <SearchPage /> },
      { path: 'programs/:id', element: <ProgramDetailPage /> },
      { path: 'favorites', element: <FavoritesPage /> },
      { path: 'notifications', element: <NotificationsPage /> },
      { path: 'admin', element: <DashboardPage /> },
      { path: 'admin/collectors', element: <CollectorPage /> },
      { path: 'admin/runs', element: <CollectionRunsPage /> },
      { path: 'admin/quality', element: <DataQualityPage /> },
    ],
  },
]);
