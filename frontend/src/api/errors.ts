import { isAxiosError } from 'axios';

/**
 * Why a request failed, at the granularity a form needs in order to word its
 * message.
 *
 * The distinction that matters is `unauthorized`/`rejected` versus everything
 * else: only those two mean the server looked at what the user supplied and
 * refused it. A dropped connection or a 500 says nothing about the input, and
 * reporting one as "incorrect email or password" sends people off to reset a
 * password that was never wrong.
 */
type ApiFailureKind =
  /** 401 or 403, meaning the server rejected the credentials, token, or link. */
  | 'unauthorized'
  /** Another 4xx: the server understood the request and declined it. */
  | 'rejected'
  /** 5xx. The request was fine; the server broke while handling it. */
  | 'server'
  /** No response at all: offline, DNS failure, reset connection, timeout, CORS. */
  | 'unreachable'
  /** Not an HTTP failure, so a bug in our own success/error handling. */
  | 'unknown';

function classifyApiFailure(error: unknown): ApiFailureKind {
  if (!isAxiosError(error)) {
    return 'unknown';
  }

  const status = error.response?.status;

  // Axios only omits `response` when the request never got an answer, which is
  // exactly the case we must not blame on the user's input.
  if (status === undefined) {
    return 'unreachable';
  }
  if (status === 401 || status === 403) {
    return 'unauthorized';
  }
  if (status >= 500) {
    return 'server';
  }
  return 'rejected';
}

/**
 * The message to show for a failed request, or `null` when the server
 * explicitly refused what the user supplied. The caller words that case itself,
 * because only it knows what was being refused.
 *
 * Never surfaces the underlying error: backend detail belongs in the console,
 * not in front of a driver.
 */
export function describeApiFailure(error: unknown): string | null {
  const kind = classifyApiFailure(error);

  switch (kind) {
    case 'unauthorized':
    case 'rejected':
      return null;
    case 'unreachable':
      return "Can't reach the server. Check your connection and try again.";
    case 'server':
    case 'unknown':
      return 'Something went wrong on our end. Please try again in a moment.';
  }
}
