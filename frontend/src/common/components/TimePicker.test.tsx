import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { TimePicker } from './TimePicker';
import {
  type TimePickerPadding,
  timePickerPaddingClasses,
} from './TimePicker.padding';

// The closed trigger is the whole surface these tests care about, so static
// markup is enough — no DOM, no interaction. `data-slot` is how the rest of
// the component library labels its parts.
function renderTrigger(element: React.ReactElement): string {
  return renderToStaticMarkup(element);
}

const CLOCK_ICON = /data-slot="time-picker-icon"/;

describe('TimePicker padding', () => {
  it('defaults to the 12px trigger padding used in route generation', () => {
    const markup = renderTrigger(<TimePicker value="09:30" />);
    expect(markup).toContain('px-3');
    expect(markup).not.toContain('px-6');
  });

  it('renders the 12px padding when it is passed explicitly', () => {
    const markup = renderTrigger(<TimePicker value="09:30" padding={12} />);
    expect(markup).toContain('px-3');
    expect(markup).not.toContain('px-6');
  });

  it('renders the 24px trigger padding used in Settings', () => {
    const markup = renderTrigger(<TimePicker value="09:30" padding={24} />);
    expect(markup).toContain('px-6');
    expect(markup).not.toContain('px-3');
  });

  it('survives a className that sets an unrelated utility', () => {
    // The route-generation table passes a width; that must not knock the
    // padding out of the tailwind-merge result.
    const markup = renderTrigger(<TimePicker padding={24} className="w-32" />);
    expect(markup).toContain('px-6');
    expect(markup).toContain('w-32');
  });

  it('lets a className padding win, since cn() merges last-wins', () => {
    const markup = renderTrigger(<TimePicker className="px-6" />);
    expect(markup).toContain('px-6');
    expect(markup).not.toContain('px-3');
  });

  it('keeps the padding on a disabled trigger', () => {
    const markup = renderTrigger(<TimePicker disabled padding={24} />);
    expect(markup).toContain('px-6');
    expect(markup).toContain('disabled');
  });
});

describe('TimePicker icon', () => {
  // Isabelle's resolution in #f4k-design: a clock everywhere, including the
  // route-generation table where every other field carries a dropdown arrow.
  it.each([undefined, 12, 24] as const)(
    'renders the clock icon at padding=%s',
    (padding) => {
      const markup = renderTrigger(
        <TimePicker value="09:30" padding={padding} />
      );
      expect(markup).toMatch(CLOCK_ICON);
      expect(markup).not.toContain('chevron');
    }
  );

  it('renders the clock icon on a disabled trigger', () => {
    expect(renderTrigger(<TimePicker disabled />)).toMatch(CLOCK_ICON);
  });
});

describe('TimePicker display', () => {
  it.each([
    ['00:00', '12:00 AM'],
    ['08:00', '8:00 AM'],
    ['09:30', '9:30 AM'],
    ['12:00', '12:00 PM'],
    ['13:05', '1:05 PM'],
    ['23:55', '11:55 PM'],
  ])('shows %s as %s', (value, expected) => {
    expect(renderTrigger(<TimePicker value={value} />)).toContain(expected);
  });

  it('falls back to 8:00 AM when uncontrolled with no value', () => {
    expect(renderTrigger(<TimePicker />)).toContain('8:00 AM');
  });
});

/**
 * The panel renders through a Radix portal, which needs a `document` and so
 * renders nothing under `renderToStaticMarkup`. Its padding is therefore tested
 * on the function that decides it — the same one the component calls.
 */
describe('timePickerPaddingClasses', () => {
  /** Tailwind's spacing scale is 4px per step. */
  function pxOf(className: string): number {
    const step = Number(className.replace('px-', ''));
    expect(Number.isFinite(step)).toBe(true);
    return step * 4;
  }

  it('pairs the 12px trigger with a panel that adds nothing', () => {
    expect(timePickerPaddingClasses(12)).toEqual({
      trigger: 'px-3',
      panel: 'px-0',
    });
  });

  it('pairs the 24px trigger with a panel that adds the remainder', () => {
    expect(timePickerPaddingClasses(24)).toEqual({
      trigger: 'px-6',
      panel: 'px-3',
    });
  });

  it.each([12, 24] as const)(
    'lands an option on the trigger text x for padding=%i',
    (padding: TimePickerPadding) => {
      const { trigger, panel } = timePickerPaddingClasses(padding);
      // The option pill's own px-3 completes the inset, so panel + 12 has to
      // land exactly on the trigger's padding. That is the whole alignment
      // contract: move one side without the other and it breaks here.
      expect(pxOf(panel) + 12).toBe(pxOf(trigger));
      expect(pxOf(trigger)).toBe(padding);
    }
  );

  it('refuses a padding with no Tailwind class rather than dropping it', () => {
    expect(() => timePickerPaddingClasses(20 as TimePickerPadding)).toThrow(
      /No Tailwind padding class/
    );
  });
});

describe('TimePicker trigger padding', () => {
  it.each([12, 24] as const)(
    'renders %i as the class the padding module chose',
    (padding: TimePickerPadding) => {
      const { trigger } = timePickerPaddingClasses(padding);
      expect(renderTrigger(<TimePicker padding={padding} />)).toContain(
        trigger
      );
    }
  );
});
