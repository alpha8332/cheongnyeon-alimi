import { createBrowserRouter } from 'react-router-dom';
import RootLayout from '@/layouts/RootLayout';
import HomePage from '@/pages/user/HomePage';
import ProgramListPage from '@/pages/user/SearchPage';
import ProgramDetailPage from '@/pages/user/ProgramDetailPage';
import NotFoundPage from '@/components/common/NotFoundPage';
import RootErrorFallback from '@/components/common/RootErrorFallback';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <RootLayout />,
    errorElement: <RootErrorFallback />,
    children: [
      { index: true, element: <HomePage /> },
      { path: 'programs', element: <ProgramListPage /> },
      { path: 'programs/:id', element: <ProgramDetailPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]);