import React from 'react';
import { Navigate, RouteObject } from 'react-router-dom';

import { LoadingSpinner } from '@/components/common/LoadingSpinner';

// Lazy load components
const DashboardPage = React.lazy(() => 
  import('@/pages/DashboardPage').then(module => ({
    default: () => <module.DashboardPage />
  }))
);

const MeetingsListPage = React.lazy(() => 
  import('@/pages/meetings/MeetingsListPage').then(module => ({
    default: () => <module.MeetingsListPage />
  }))
);

const NewRecordingPage = React.lazy(() => 
  import('@/pages/recording/NewRecordingPage').then(module => ({
    default: () => <module.NewRecordingPage />
  }))
);

// Wrap lazy components with Suspense
const withSuspense = (Component: React.LazyExoticComponent<React.ComponentType>) => (
  <React.Suspense fallback={<LoadingSpinner />}>
    <Component />
  </React.Suspense>
);

const routes: RouteObject[] = [
  {
    path: '/',
    element: <Navigate to="/dashboard" replace />,
  },
  {
    path: '/dashboard',
    element: withSuspense(DashboardPage),
  },
  {
    path: '/meetings',
    children: [
      {
        path: '',
        element: <Navigate to="all" replace />,
      },
      {
        path: 'all',
        element: withSuspense(MeetingsListPage),
      },
      {
        path: 'recent',
        element: withSuspense(MeetingsListPage), // TODO: Add filter for recent
      },
      {
        path: 'favorites',
        element: withSuspense(MeetingsListPage), // TODO: Add filter for favorites
      },
    ],
  },
  {
    path: '/recording',
    children: [
      {
        path: '',
        element: <Navigate to="new" replace />,
      },
      {
        path: 'new',
        element: withSuspense(NewRecordingPage),
      },
      {
        path: 'devices',
        element: withSuspense(NewRecordingPage), // TODO: Create separate devices page
      },
    ],
  },
  {
    path: '*',
    element: <Navigate to="/dashboard" replace />,
  },
];

export default routes;
