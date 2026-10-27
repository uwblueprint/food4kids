// @vitest-environment happy-dom
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  cleanup,
  fireEvent,
  render,
  screen,
  waitFor,
} from '@testing-library/react';
import { AxiosError } from 'axios';
import { afterEach, describe, expect, it } from 'vitest';

import { useAuthStore } from '@/api/authStore';
import type { BillingCostsResponse } from '@/api/generated';
import axiosClient from '@/lib/axiosClient';

import { RouteGenerationCostCard } from './RouteGenerationCostCard';

const originalAdapter = axiosClient.defaults.adapter;
const clients: QueryClient[] = [];
afterEach(() => {
  cleanup();
  clients.forEach((client) => client.clear());
  clients.length = 0;
  axiosClient.defaults.adapter = originalAdapter;
  useAuthStore.setState({ accessToken: null });
});

function renderCard() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  clients.push(client);
  return render(
    <QueryClientProvider client={client}>
      <RouteGenerationCostCard />
    </QueryClientProvider>
  );
}

const costs: BillingCostsResponse = {
  project_id: 'food4kids',
  invoice_month: '2026-10',
  currency: 'CAD',
  month_to_date_cost: 5,
  year_to_date_cost: 123.45,
  gross_cost: 6,
  credits: -1,
  budget_amount: null,
  budget_currency: null,
  budget_display_name: null,
  budget_scope: null,
  data_as_of: '2026-10-25T15:00:00Z',
};

function respond(data: BillingCostsResponse) {
  axiosClient.defaults.adapter = async (config) => ({
    data,
    status: 200,
    statusText: 'OK',
    headers: {},
    config,
  });
}

describe('Route generation cost integration', () => {
  it('requests the billing endpoint and displays yearly rather than monthly spend', async () => {
    let url: string | undefined;
    let authorization: unknown;
    useAuthStore.setState({ accessToken: 'test-admin-token' });
    axiosClient.defaults.adapter = async (config) => {
      url = config.url;
      authorization = config.headers.get('Authorization');
      return {
        data: costs,
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();

    expect(await screen.findByText(/CAD\s+123\.45/)).toBeDefined();
    expect(url).toMatch(/\/api\/billing\/costs$/);
    expect(authorization).toBe('Bearer test-admin-token');
    expect(
      screen.getByText(
        `as of ${new Date().toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
        })}`
      )
    ).toBeDefined();
    expect(screen.queryByText(/CAD\s+5\.00/)).toBeNull();
  });

  it('renders zero without crashing when the export has no currency or usage', async () => {
    respond({ ...costs, currency: '', year_to_date_cost: 0, data_as_of: null });
    renderCard();
    expect(await screen.findByText('0.00')).toBeDefined();
  });

  it('shows loading until the request resolves', async () => {
    let release!: () => void;
    const pending = new Promise<void>((resolve) => {
      release = resolve;
    });
    axiosClient.defaults.adapter = async (config) => {
      await pending;
      return {
        data: costs,
        status: 200,
        statusText: 'OK',
        headers: {},
        config,
      };
    };
    renderCard();
    expect(screen.getByRole('status', { name: 'Loading' })).toBeDefined();
    release();
    expect(await screen.findByText(/CAD\s+123\.45/)).toBeDefined();
  });

  it('shows an unavailable state on failure and retries the real query', async () => {
    axiosClient.defaults.adapter = async () => {
      throw new AxiosError('Unavailable');
    };
    renderCard();
    expect(await screen.findByText('Cost unavailable.')).toBeDefined();
    expect(screen.queryByText('0.00')).toBeNull();

    respond(costs);
    fireEvent.click(screen.getByRole('button', { name: 'Retry' }));
    await waitFor(() =>
      expect(screen.queryByText('Cost unavailable.')).toBeNull()
    );
    expect(await screen.findByText(/CAD\s+123\.45/)).toBeDefined();
  });
});
