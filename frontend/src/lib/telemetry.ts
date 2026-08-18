import * as Sentry from '@sentry/react';
import { isAxiosError } from 'axios';

/**
 * The one sanctioned way to report a failure. Never hand an error object to a
 * logger: an AxiosError drags the whole request along with it. Wired globally
 * in queryClient.ts, so hooks rarely call this directly.
 *
 * Every failure is logged to Sentry, so the log stream shows what users are
 * hitting. Only unexpected ones — 5xx, network silence, non-HTTP bugs — also
 * become issues; a 4xx is the server refusing user input, which the form
 * already words for them.
 */

/** The complete set of fields allowed to leave the device. */
interface FailureFacts {
  /** Where the failure surfaced, e.g. 'query', 'mutation'. */
  context: string;
  status?: number;
  /** Axios transport code when there is no HTTP status, e.g. ERR_NETWORK. */
  code?: string;
  method?: string;
  /** Request path with query and fragment removed — parameters can carry PII. */
  path?: string;
  /** Only set when the request got no answer: a dead zone or a dead server. */
  online?: boolean;
}

export function reportError(error: unknown, context: string): void {
  const url = isAxiosError(error) ? (error.config?.url ?? '') : '';
  const status = isAxiosError(error) ? error.response?.status : undefined;
  const facts: FailureFacts = isAxiosError(error)
    ? {
        context,
        status,
        code: error.code,
        method: error.config?.method?.toUpperCase(),
        path: url.split(/[?#]/)[0] || undefined,
        // Drivers work on cellular. Without this, a tunnel and an outage
        // produce identical records.
        online:
          status === undefined && typeof navigator !== 'undefined'
            ? navigator.onLine
            : undefined,
      }
    : { context };

  if (import.meta.env.DEV) {
    // eslint-disable-next-line no-console
    console.warn('Request failed:', facts);
  }

  if (!Sentry.isInitialized()) {
    return;
  }

  // Attributes must be primitives; drop the fields this failure didn't have.
  const attributes = Object.fromEntries(
    Object.entries(facts).filter(([, value]) => value !== undefined)
  );

  // No status means no answer at all (or a non-HTTP bug) — ours to notice,
  // like a 5xx. Capturing the error is safe: axiosClient strips the body and
  // token from every rejection first.
  const unexpected = facts.status === undefined || facts.status >= 500;
  if (unexpected) {
    Sentry.logger.error('Request failed', attributes);
    Sentry.captureException(error, { extra: { ...facts } });
  } else {
    Sentry.logger.warn('Request failed', attributes);
  }
}
