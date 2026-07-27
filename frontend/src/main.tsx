import './index.css';

import * as Sentry from '@sentry/react';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';

import App from './App.tsx';
import { AuthProvider } from './contexts/AuthProvider.tsx';
import queryClient from './lib/queryClient.ts';

// Initialize Sentry only when DSN is present (if present, will have sentry logs, else will not)
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
      // Automatically capture console.log, console.warn, and console.error calls as Sentry logs
      Sentry.consoleLoggingIntegration({ levels: ['log', 'warn', 'error'] }),
    ],
    // Enable logs
    enableLogs: true,

    tracesSampleRate: 0.2,
    tracePropagationTargets: ['localhost', /^https:\/\/.*\.run\.app/],

    // Session replay
    // Capture 5% of normal user sessions
    replaysSessionSampleRate: 0.05,
    // Capture 100% of sessions when errors happen
    replaysOnErrorSampleRate: 1.0,
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          <App />
        </AuthProvider>
      </BrowserRouter>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>
);
