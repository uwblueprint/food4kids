import * as Sentry from '@sentry/react';

// Initialize Sentry only when DSN is present (if present, will have sentry logs, else will not)
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration(),
    ],
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
