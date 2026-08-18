import * as Sentry from '@sentry/react';
import { AxiosError, AxiosHeaders, type AxiosResponse } from 'axios';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { reportError } from '@/lib/telemetry';

vi.mock('@sentry/react', () => ({
  isInitialized: vi.fn(() => true),
  captureException: vi.fn(),
  logger: { warn: vi.fn(), error: vi.fn() },
}));

/**
 * Facts are picked fields only, with no query strings. Every failure is
 * logged; only breakage and silence also become issues — never a 4xx the UI
 * already words for the user.
 */

function httpError(status: number, url = '/location-groups'): AxiosError {
  const config = { url, method: 'post', headers: new AxiosHeaders() };
  const response = {
    data: { detail: 'nope' },
    status,
    statusText: 'Error',
    headers: {},
    config,
  } as AxiosResponse;
  return new AxiosError(
    `Request failed with status code ${status}`,
    AxiosError.ERR_BAD_REQUEST,
    config as never,
    null,
    response
  );
}

function networkError(): AxiosError {
  const config = { url: '/routes', method: 'get', headers: new AxiosHeaders() };
  return new AxiosError(
    'Network Error',
    AxiosError.ERR_NETWORK,
    config as never
  );
}

beforeEach(() => {
  vi.clearAllMocks();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

describe('reportError', () => {
  it('captures a 500', () => {
    reportError(httpError(500), 'query');
    expect(Sentry.captureException).toHaveBeenCalledTimes(1);
  });

  it('captures network silence', () => {
    reportError(networkError(), 'query');
    expect(Sentry.captureException).toHaveBeenCalledTimes(1);
  });

  it('captures non-HTTP bugs', () => {
    reportError(new TypeError('x is not a function'), 'query');
    expect(Sentry.captureException).toHaveBeenCalledTimes(1);
  });

  it.each([400, 401, 403, 404, 409, 422])(
    'logs a %i as a warning without raising an issue',
    (status) => {
      reportError(httpError(status), 'mutation');
      expect(Sentry.captureException).not.toHaveBeenCalled();
      expect(Sentry.logger.warn).toHaveBeenCalledWith(
        'Request failed',
        expect.objectContaining({ status, context: 'mutation' })
      );
    }
  );

  it('logs unexpected failures at error level, with the facts attached', () => {
    reportError(httpError(503), 'query');
    expect(Sentry.logger.error).toHaveBeenCalledWith('Request failed', {
      context: 'query',
      status: 503,
      code: AxiosError.ERR_BAD_REQUEST,
      method: 'POST',
      path: '/location-groups',
    });
  });

  it('strips query strings from the path', () => {
    reportError(httpError(500, '/drivers?email=dana@example.com'), 'query');
    const [, attributes] = vi.mocked(Sentry.logger.error).mock.calls[0];
    expect(attributes).toMatchObject({ path: '/drivers' });
  });

  it('reports the transport code when there was no response', () => {
    reportError(networkError(), 'query');
    const [, attributes] = vi.mocked(Sentry.logger.error).mock.calls[0];
    expect(attributes).toMatchObject({ code: 'ERR_NETWORK' });
    expect(attributes).not.toHaveProperty('status');
  });

  it('records connectivity when the request got no answer', () => {
    vi.stubGlobal('navigator', { onLine: false });
    reportError(networkError(), 'query');
    const [, attributes] = vi.mocked(Sentry.logger.error).mock.calls[0];
    expect(attributes).toMatchObject({ online: false });
  });

  it('leaves connectivity off a failure the server answered', () => {
    vi.stubGlobal('navigator', { onLine: true });
    reportError(httpError(404), 'query');
    const [, attributes] = vi.mocked(Sentry.logger.warn).mock.calls[0];
    expect(attributes).not.toHaveProperty('online');
  });

  it('carries only the context for a non-HTTP error', () => {
    reportError(new Error('boom'), 'mutation');
    expect(Sentry.logger.error).toHaveBeenCalledWith('Request failed', {
      context: 'mutation',
    });
  });

  it('stays quiet when Sentry is not initialized', () => {
    vi.mocked(Sentry.isInitialized).mockReturnValue(false);
    reportError(httpError(500), 'query');
    expect(Sentry.captureException).not.toHaveBeenCalled();
    expect(Sentry.logger.error).not.toHaveBeenCalled();
  });
});
