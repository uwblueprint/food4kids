// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { Toggle } from '@/common/components/Toggle';

afterEach(cleanup);

function knob(): HTMLElement {
  const el = screen.getByRole('switch').querySelector('span');
  if (!el) throw new Error('toggle knob not found');
  return el as HTMLElement;
}

describe('Toggle', () => {
  it('keeps the knob Grey/100 in both states', () => {
    for (const checked of [true, false]) {
      cleanup();
      render(<Toggle checked={checked} onChange={() => {}} />);
      const classes = knob().className.split(/\s+/);
      expect(classes).toContain('bg-grey-100');
      expect(classes).not.toContain('bg-white');
      // no state-dependent fill sneaking in alongside it
      expect(classes.filter((c) => c.startsWith('bg-'))).toEqual([
        'bg-grey-100',
      ]);
    }
  });

  it('fills the track blue when on and grey when off', () => {
    render(<Toggle checked onChange={() => {}} />);
    expect(screen.getByRole('switch').className).toContain('bg-blue-300');

    cleanup();
    render(<Toggle checked={false} onChange={() => {}} />);
    expect(screen.getByRole('switch').className).toContain('bg-grey-300');
  });

  it('uses a 12px gap between the switch and its label', () => {
    const { container } = render(<Toggle checked onChange={() => {}} />);
    const root = container.firstElementChild as HTMLElement;
    const classes = root.className.split(/\s+/);
    expect(classes).toContain('gap-3');
    expect(classes).not.toContain('gap-2');
  });

  it('labels the states Yes/No and reports the right aria-checked', () => {
    render(<Toggle checked onChange={() => {}} />);
    expect(screen.getByRole('switch').getAttribute('aria-checked')).toBe(
      'true'
    );
    expect(screen.getByText('Yes')).toBeTruthy();

    cleanup();
    render(<Toggle checked={false} onChange={() => {}} />);
    expect(screen.getByRole('switch').getAttribute('aria-checked')).toBe(
      'false'
    );
    expect(screen.getByText('No')).toBeTruthy();
  });

  it('toggles to the opposite value on click, and not at all when disabled', () => {
    const onChange = vi.fn();
    render(<Toggle checked={false} onChange={onChange} />);
    fireEvent.click(screen.getByRole('switch'));
    expect(onChange).toHaveBeenCalledWith(true);

    cleanup();
    onChange.mockClear();
    render(<Toggle checked disabled onChange={onChange} />);
    fireEvent.click(screen.getByRole('switch'));
    expect(onChange).not.toHaveBeenCalled();
  });
});
