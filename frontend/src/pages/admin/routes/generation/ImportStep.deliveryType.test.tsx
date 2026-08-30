// @vitest-environment jsdom
import { cleanup, render, screen } from '@testing-library/react';
import {
  MemoryRouter,
  Route,
  Routes,
  useOutletContext,
} from 'react-router-dom';
import { afterEach, beforeAll, describe, expect, it, vi } from 'vitest';

import type { SystemSettingsRead } from '@/api/generated/types.gen';

import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';
import { AdminRoutesGenerationLayout } from './AdminRoutesGenerationLayout';
import { ImportStep } from './ImportStep';

const useSystemSettings = vi.fn();

vi.mock('@/api', () => ({
  useSystemSettings: () => useSystemSettings(),
  usePreviewLocationImport: () => ({
    mutateAsync: vi.fn(),
    isPending: false,
  }),
}));

/** Renders the delivery type the layout put in context, so the tests can tell
 * "applied without asking" apart from "nothing chosen yet". */
function SelectedTypeProbe() {
  const { selectedDeliveryType } = useOutletContext<GenerationOutletContext>();
  // In an attribute, not text, so the tests can assert on what the step
  // itself renders without matching the probe.
  return <div data-testid="selected" data-value={selectedDeliveryType} />;
}

type SettingsQuery = {
  data: SystemSettingsRead | undefined;
  isSuccess: boolean;
  isError: boolean;
};

const loading: SettingsQuery = {
  data: undefined,
  isSuccess: false,
  isError: false,
};

const loaded = (delivery_types: string[] | undefined): SettingsQuery => ({
  data: { delivery_types } as unknown as SystemSettingsRead,
  isSuccess: true,
  isError: false,
});

function renderImportStep(query: SettingsQuery) {
  useSystemSettings.mockReturnValue(query);
  return render(
    <MemoryRouter initialEntries={['/admin/routes/generation/import']}>
      <Routes>
        <Route
          path="/admin/routes/generation"
          element={<AdminRoutesGenerationLayout />}
        >
          <Route
            path="import"
            element={
              <>
                <ImportStep />
                <SelectedTypeProbe />
              </>
            }
          />
        </Route>
      </Routes>
    </MemoryRouter>
  );
}

const picker = () => screen.queryByText('Select Delivery Type');
const uploadSection = () =>
  screen.queryByText(/Upload an Excel file \(\.xlsx\)/);
const selected = () =>
  screen.getByTestId('selected').getAttribute('data-value');

// jsdom ships neither of these, and the stepper measures itself with both.
beforeAll(() => {
  Object.defineProperty(document, 'fonts', {
    configurable: true,
    value: { ready: Promise.resolve() },
  });
  vi.stubGlobal(
    'ResizeObserver',
    class {
      observe() {}
      unobserve() {}
      disconnect() {}
    }
  );
});

afterEach(cleanup);

describe('ImportStep delivery type selection', () => {
  it('shows the picker when several types are configured', () => {
    renderImportStep(loaded(['Family', 'School']));

    expect(picker()).not.toBeNull();
    expect(screen.getAllByRole('radio')).toHaveLength(2);
    // Nothing is chosen for the admin, so the upload waits on their pick.
    expect(selected()).toBe('');
    expect(uploadSection()).toBeNull();
  });

  it('skips the picker and applies the type when only one is configured', () => {
    renderImportStep(loaded(['Family']));

    expect(picker()).toBeNull();
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
    expect(selected()).toBe('Family');
    // Skipped, not auto-dismissed: the upload is available on first render.
    expect(uploadSection()).not.toBeNull();
    expect(screen.getByText('Family')).not.toBeNull();
  });

  it('makes no decision while settings are still loading', () => {
    renderImportStep(loading);

    expect(picker()).toBeNull();
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
    // Neither "one type" (nothing applied) nor "many" (no picker, no upload).
    expect(selected()).toBe('');
    expect(uploadSection()).toBeNull();
    expect(screen.getByRole('status')).not.toBeNull();
  });

  it('says so explicitly when no types are configured', () => {
    renderImportStep(loaded([]));

    expect(picker()).toBeNull();
    expect(screen.queryAllByRole('radio')).toHaveLength(0);
    expect(selected()).toBe('');
    expect(uploadSection()).toBeNull();
    expect(screen.queryByRole('status')).toBeNull();
    expect(screen.getByText(/No delivery types are configured/)).not.toBeNull();
  });

  it('reports a failed settings load instead of spinning forever', () => {
    renderImportStep({ data: undefined, isSuccess: false, isError: true });

    expect(screen.queryByRole('status')).toBeNull();
    expect(selected()).toBe('');
    expect(
      screen.getByText(/Could not load the configured delivery types/)
    ).not.toBeNull();
  });
});
