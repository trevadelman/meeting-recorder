import React, { Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, theme } from 'antd';
import { BrowserRouter, useRoutes } from 'react-router-dom';

import { AppLayout } from '@/components/common/AppLayout';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { AppProvider, useApp } from '@/contexts/AppContext';
import routes from '@/routes';
import { GlobalStyles } from '@/styles/GlobalStyles';

// Configure React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: false,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

// Configure Ant Design theme
const baseTheme = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 4,
    fontFamily: 'Inter, system-ui, -apple-system, sans-serif',
  },
  components: {
    Layout: {
      bodyBg: '#f0f2f5',
      headerBg: '#fff',
      headerHeight: 64,
      headerPadding: '0 24px',
    },
    Menu: {
      itemBg: 'transparent',
      itemSelectedBg: 'rgba(0, 0, 0, 0.06)',
      itemHoverBg: 'rgba(0, 0, 0, 0.03)',
    },
    Card: {
      boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02)',
    },
  },
};

// Routes component
function Routes() {
  const element = useRoutes(routes);
  return element;
}

// App content with context access
function AppContent() {
  const { state } = useApp();

  // Configure theme based on dark mode
  const themeConfig = {
    ...baseTheme,
    algorithm: state.ui.darkMode ? theme.darkAlgorithm : theme.defaultAlgorithm,
  };

  return (
    <ConfigProvider theme={themeConfig}>
      <GlobalStyles darkMode={state.ui.darkMode} />
      <BrowserRouter>
        <AppLayout>
          <ErrorBoundary>
            <Suspense fallback={<LoadingSpinner fullPage />}>
              <Routes />
            </Suspense>
          </ErrorBoundary>
        </AppLayout>
      </BrowserRouter>
    </ConfigProvider>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <AppProvider>
          <AppContent />
        </AppProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
}

export default App;
