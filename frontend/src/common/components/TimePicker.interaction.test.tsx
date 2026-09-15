// @vitest-environment happy-dom
import { act, cleanup, fireEvent, render } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it } from 'vitest';

import { TimePicker } from './TimePicker';

afterEach(cleanup);

/**
 * The panel is portalled out of the trigger, so it is found on the document.
 * Read through `data-state` rather than presence, because a real browser keeps
 * a dismissed panel mounted for its exit animation; with no animation to wait
 * on, happy-dom drops the node instead, which is equally closed.
 */
function panelState(): 'open' | 'closed' {
  const panel = document.querySelector('[data-slot="time-picker-panel"]');
  if (!panel) return 'closed';
  return panel.getAttribute('data-state') === 'open' ? 'open' : 'closed';
}

/** Controlled, as every real caller uses it, so a commit reaches the field. */
function Harness({ onChange }: { onChange?: (value: string) => void }) {
  const [value, setValue] = useState('09:30');
  return (
    <TimePicker
      value={value}
      onChange={(next) => {
        setValue(next);
        onChange?.(next);
      }}
    />
  );
}

function renderPicker(onChange?: (value: string) => void) {
  const { container } = render(<Harness onChange={onChange} />);
  const trigger = container.querySelector(
    '[data-slot="time-picker-trigger"]'
  ) as HTMLDivElement;
  return {
    trigger,
    input: trigger.querySelector('input') as HTMLInputElement,
    clock: trigger.querySelector('button') as HTMLButtonElement,
  };
}

/** Lets Radix's deferred document listeners register, and effects settle. */
async function settle() {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, 0));
  });
}

function pointerDown(target: Element) {
  target.dispatchEvent(
    new PointerEvent('pointerdown', {
      bubbles: true,
      cancelable: true,
      pointerId: 1,
      button: 0,
      isPrimary: true,
      pointerType: 'mouse',
    })
  );
}

describe('TimePicker opening from the field', () => {
  it('opens the panel when the field takes focus', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    expect(panelState()).toBe('open');
  });

  /**
   * The real regression. In a browser the focusin that opens the panel is still
   * propagating when Radix's freshly-mounted layer starts listening for it, so
   * the panel dismissed itself the instant it appeared — the flash Colin saw.
   * happy-dom cannot reproduce that timing, so the focusin is replayed here
   * with the panel open, which is the same event reaching the same listener.
   */
  it('stays open when focus lands in the field', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    await settle();

    await act(async () => {
      input.dispatchEvent(new FocusEvent('focusin', { bubbles: true }));
    });

    expect(panelState()).toBe('open');
  });

  it('stays open when the field is clicked again while open', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    await settle();

    await act(async () => pointerDown(input));

    expect(panelState()).toBe('open');
  });

  it('stays open while typing into the field', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    await settle();

    await act(async () => fireEvent.change(input, { target: { value: '10' } }));
    await act(async () => {
      input.dispatchEvent(new FocusEvent('focusin', { bubbles: true }));
    });

    expect(panelState()).toBe('open');
    expect(input.value).toBe('10');
  });

  it('still closes on a pointer interaction genuinely outside', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    await settle();

    await act(async () => pointerDown(document.body));

    expect(panelState()).toBe('closed');
  });

  it('still closes on focus moving genuinely outside, committing the draft', async () => {
    const outside = document.createElement('input');
    document.body.appendChild(outside);
    try {
      const { input } = renderPicker();
      await act(async () => input.focus());
      await settle();
      await act(async () =>
        fireEvent.change(input, { target: { value: '1' } })
      );

      await act(async () => outside.focus());
      await settle();

      expect(panelState()).toBe('closed');
      // A bare "1" reads as the afternoon of the delivery day.
      expect(input.value).toBe('1:00 PM');
    } finally {
      outside.remove();
    }
  });

  it('still opens and closes from the clock button', async () => {
    const { clock } = renderPicker();
    await act(async () => fireEvent.click(clock));
    expect(panelState()).toBe('open');
    await settle();

    await act(async () => {
      pointerDown(clock);
      fireEvent.click(clock);
    });
    expect(panelState()).toBe('closed');
  });

  it('reverts the draft and closes on Escape', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    await settle();
    await act(async () => fireEvent.change(input, { target: { value: '10' } }));

    await act(async () => fireEvent.keyDown(input, { key: 'Escape' }));

    expect(panelState()).toBe('closed');
    expect(input.value).toBe('9:30 AM');
  });

  it('commits the draft and closes on Enter', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    await settle();
    await act(async () => fireEvent.change(input, { target: { value: '10' } }));

    await act(async () => fireEvent.keyDown(input, { key: 'Enter' }));

    expect(panelState()).toBe('closed');
    expect(input.value).toBe('10:00 AM');
  });

  it('commits the option a mousedown lands on', async () => {
    const { input } = renderPicker();
    await act(async () => input.focus());
    await settle();

    const option = [
      ...document.querySelectorAll(
        '[data-slot="time-picker-panel"] [role="option"]'
      ),
    ].find((o) => o.textContent === '11:00 AM') as HTMLButtonElement;
    await act(async () => fireEvent.mouseDown(option));

    expect(panelState()).toBe('closed');
    expect(input.value).toBe('11:00 AM');
  });
});
