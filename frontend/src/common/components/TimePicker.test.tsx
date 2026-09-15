import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';

import { TimePicker } from './TimePicker';
import {
  centeredScrollTop,
  formatDisplayTime,
  parseTypedTime,
  timeOptions,
} from './TimePicker.options';
import {
  type TimePickerPadding,
  timePickerPaddingClass,
} from './TimePicker.padding';

// The closed trigger is the whole surface these render tests care about, so
// static markup is enough — no DOM, no interaction. The panel goes through a
// Radix portal, which needs a `document` and so renders nothing here; the
// panel's behaviour is covered on the pure modules that decide it.
function renderTrigger(element: React.ReactElement): string {
  return renderToStaticMarkup(element);
}

const CLOCK_ICON = /data-slot="time-picker-icon"/;

describe('TimePicker padding', () => {
  it('defaults to the 12px padding used in route generation', () => {
    const markup = renderTrigger(<TimePicker value="09:30" />);
    expect(markup).toContain('px-3');
    expect(markup).not.toContain('px-6');
  });

  it('renders the 24px padding used in Settings', () => {
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

describe('timePickerPaddingClass', () => {
  it('maps each supported padding to its Tailwind class', () => {
    expect(timePickerPaddingClass(12)).toBe('px-3');
    expect(timePickerPaddingClass(24)).toBe('px-6');
  });

  it.each([12, 24] as const)(
    'gives the trigger and the options one class at padding=%i',
    (padding: TimePickerPadding) => {
      // The alignment contract: options take the same inset as the trigger, so
      // an option's text lands on the trigger's text. One class means the two
      // cannot drift apart.
      const className = timePickerPaddingClass(padding);
      expect(renderTrigger(<TimePicker padding={padding} />)).toContain(
        className
      );
    }
  );

  it('refuses a padding with no Tailwind class rather than dropping it', () => {
    expect(() => timePickerPaddingClass(20 as TimePickerPadding)).toThrow(
      /No Tailwind padding class/
    );
  });
});

describe('TimePicker icon', () => {
  // Isabelle's resolution in #f4k-design, and what the newer route-generation
  // frames now show: a clock everywhere, never the dropdown arrow.
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

describe('formatDisplayTime', () => {
  it.each([
    ['00:00', '12:00 AM'],
    ['00:30', '12:30 AM'],
    ['08:00', '8:00 AM'],
    ['08:45', '8:45 AM'],
    ['09:30', '9:30 AM'],
    ['11:59', '11:59 AM'],
    ['12:00', '12:00 PM'],
    ['12:30', '12:30 PM'],
    ['13:05', '1:05 PM'],
    ['23:30', '11:30 PM'],
    ['23:59', '11:59 PM'],
  ])('renders %s as %s', (value, expected) => {
    expect(formatDisplayTime(value)).toBe(expected);
  });

  it.each(['9:30', '24:00', '12:60', '', 'noon', '09:5', '0930'])(
    'refuses %o rather than rendering something wrong',
    (value) => {
      expect(() => formatDisplayTime(value)).toThrow(/Expected a 24-hour/);
    }
  );

  it('shows the value in the trigger', () => {
    expect(renderTrigger(<TimePicker value="13:05" />)).toContain('1:05 PM');
  });

  it('falls back to 8:00 AM when uncontrolled with no value', () => {
    expect(renderTrigger(<TimePicker />)).toContain('8:00 AM');
  });
});

describe('timeOptions', () => {
  it('covers the whole day on a half-hour step', () => {
    const options = timeOptions();
    expect(options).toHaveLength(48);
    expect(options[0]).toBe('00:00');
    expect(options[1]).toBe('00:30');
    expect(options.at(-1)).toBe('23:30');
  });

  it('steps by exactly 30 minutes throughout', () => {
    const minutes = timeOptions().map((o) => {
      const [h, m] = o.split(':').map(Number);
      return h * 60 + m;
    });
    const steps = new Set(minutes.slice(1).map((m, i) => m - minutes[i]));
    expect([...steps]).toEqual([30]);
  });

  it('adds nothing when the value already falls on the step', () => {
    expect(timeOptions('09:30')).toEqual(timeOptions());
    expect(timeOptions('00:00')).toHaveLength(48);
  });

  it.each([
    ['08:45', 18],
    ['10:05', 21],
    ['09:45', 20],
  ])(
    'keeps a staggered route-generation time like %s selectable',
    (value, index) => {
      // Route start times are staggered per route, so a stored value off the
      // half-hour step still has to appear as the selection.
      const options = timeOptions(value);
      expect(options).toHaveLength(49);
      expect(options).toContain(value);
      expect(options[index]).toBe(value);
    }
  );

  it('keeps an off-step value before midnight in order', () => {
    const options = timeOptions('23:45');
    expect(options.at(-1)).toBe('23:45');
    expect(options.at(-2)).toBe('23:30');
  });

  it('keeps an off-step value after midnight in order', () => {
    const options = timeOptions('00:05');
    expect(options[0]).toBe('00:00');
    expect(options[1]).toBe('00:05');
    expect(options[2]).toBe('00:30');
  });

  it('stays chronological with the extra value inserted', () => {
    const options = timeOptions('16:20');
    expect([...options].sort()).toEqual(options);
    expect(new Set(options).size).toBe(options.length);
  });

  it('refuses a malformed value rather than offering a broken list', () => {
    expect(() => timeOptions('8:45')).toThrow(/Expected a 24-hour/);
  });
});

describe('centeredScrollTop', () => {
  // A 48-option list of 42px rows in a 128px viewport, which is the real shape.
  const list = {
    optionHeight: 42,
    viewportHeight: 128,
    contentHeight: 48 * 42,
  };

  it('centres an option from the middle of the list', () => {
    // 20th option: 840 - (128 - 42) / 2 = 797
    expect(centeredScrollTop({ ...list, optionTop: 20 * 42 })).toBe(797);
  });

  it('stays at the top for the first option, with nothing to scroll past', () => {
    expect(centeredScrollTop({ ...list, optionTop: 0 })).toBe(0);
  });

  it('stays at the top for any option that cannot be centred yet', () => {
    // Option 1 would want -1, which would leave the list blank above.
    expect(centeredScrollTop({ ...list, optionTop: 42 })).toBe(0);
  });

  it('stops at the bottom for the last option', () => {
    const furthest = list.contentHeight - list.viewportHeight;
    expect(centeredScrollTop({ ...list, optionTop: 47 * 42 })).toBe(furthest);
  });

  it('stops at the bottom for any option near the end', () => {
    const furthest = list.contentHeight - list.viewportHeight;
    expect(centeredScrollTop({ ...list, optionTop: 46 * 42 })).toBe(furthest);
  });

  it('does not scroll when everything already fits', () => {
    expect(
      centeredScrollTop({
        optionTop: 84,
        optionHeight: 42,
        viewportHeight: 400,
        contentHeight: 126,
      })
    ).toBe(0);
  });

  it('never returns a negative or past-the-end offset across the list', () => {
    const furthest = list.contentHeight - list.viewportHeight;
    for (let i = 0; i < 48; i++) {
      const top = centeredScrollTop({ ...list, optionTop: i * 42 });
      expect(top).toBeGreaterThanOrEqual(0);
      expect(top).toBeLessThanOrEqual(furthest);
    }
  });
});

describe('parseTypedTime', () => {
  it.each([
    // The shapes a user actually types for nine in the morning.
    ['9', '09:00'],
    ['09', '09:00'],
    ['9:00', '09:00'],
    ['09:00', '09:00'],
    ['9am', '09:00'],
    ['9 am', '09:00'],
    ['9AM', '09:00'],
    ['9 AM', '09:00'],
    ['9a', '09:00'],
    ['9 a.m.', '09:00'],
    ['9:00 AM', '09:00'],
    ['  9:00 am  ', '09:00'],
  ])('reads %o as %s', (raw, expected) => {
    expect(parseTypedTime(raw)).toBe(expected);
  });

  it.each([
    ['9pm', '21:00'],
    ['9 PM', '21:00'],
    ['9 p.m.', '21:00'],
    ['12am', '00:00'],
    ['12:30 am', '00:30'],
    ['12pm', '12:00'],
    ['12:30 pm', '12:30'],
    ['1pm', '13:00'],
    ['11:59 pm', '23:59'],
  ])('applies the meridiem in %o to give %s', (raw, expected) => {
    expect(parseTypedTime(raw)).toBe(expected);
  });

  it.each([
    // The morning half of the delivery day.
    ['8', '08:00'],
    ['9', '09:00'],
    ['10', '10:00'],
    ['11', '11:00'],
    ['12', '12:00'],
    // The afternoon half: 1 through 7 can only sensibly mean PM here.
    ['1', '13:00'],
    ['2', '14:00'],
    ['5', '17:00'],
    ['7', '19:00'],
  ])(
    'places the bare hour %o in the delivery day, giving %s',
    (raw, expected) => {
      expect(parseTypedTime(raw)).toBe(expected);
    }
  );

  it.each([
    ['1:30', '13:30'],
    ['7:45', '19:45'],
    ['9:45', '09:45'],
    ['12:15', '12:15'],
  ])(
    'applies the delivery day to the hour of %o, giving %s',
    (raw, expected) => {
      // The minutes never move the hour into the other half.
      expect(parseTypedTime(raw)).toBe(expected);
    }
  );

  it.each([
    ['0', '00:00'],
    ['00:00', '00:00'],
    ['0:30', '00:30'],
    ['13', '13:00'],
    ['13:05', '13:05'],
    ['20', '20:00'],
    ['23:59', '23:59'],
  ])('leaves the already-unambiguous %o alone, giving %s', (raw, expected) => {
    // 13-23 say which half they mean, and midnight has only one reading, even
    // though it falls outside the delivery day.
    expect(parseTypedTime(raw)).toBe(expected);
  });

  it.each([
    ['1am', '01:00'],
    ['7 am', '07:00'],
    ['2 a.m.', '02:00'],
    ['12am', '00:00'],
    ['8pm', '20:00'],
    ['11 pm', '23:00'],
  ])(
    'lets the explicit meridiem in %o beat the delivery day, giving %s',
    (raw, expected) => {
      expect(parseTypedTime(raw)).toBe(expected);
    }
  );

  it.each([
    ['9:7', '09:07'],
    ['9:07', '09:07'],
    ['10:5', '10:05'],
  ])('reads a one-digit minute in %o as %s', (raw, expected) => {
    // "9:7" can only mean seven minutes past — "9:70" is not a time — so
    // reading it is forgiving rather than a silent coercion.
    expect(parseTypedTime(raw)).toBe(expected);
  });

  it.each([
    ['08:45', '08:45'],
    ['10:05', '10:05'],
    ['9:45 am', '09:45'],
  ])('accepts the staggered route time %o', (raw, expected) => {
    // Typed times are not restricted to the half-hour step the list offers.
    expect(parseTypedTime(raw)).toBe(expected);
  });

  it.each([
    '',
    '   ',
    'banana',
    'noon',
    '25:00',
    '24:00',
    '24',
    '12:60',
    '9:99',
    '13pm',
    '0pm',
    '0am',
    '13 a.m.',
    '9:',
    ':30',
    '-1:00',
    '9:00 xm',
    '9::00',
    '900',
    '9.00',
    '9 10',
    'am',
  ])('refuses %o', (raw) => {
    expect(parseTypedTime(raw)).toBeNull();
  });

  it('round-trips every option through its own display form', () => {
    // Whatever the list shows has to be re-typeable exactly as shown.
    for (const option of timeOptions()) {
      expect(parseTypedTime(formatDisplayTime(option))).toBe(option);
    }
  });

  it('feeds a typed off-step time straight into the list, in order', () => {
    const typed = parseTypedTime('10:05');
    expect(typed).toBe('10:05');
    const options = timeOptions(typed as string);
    expect(options[20]).toBe('10:00');
    expect(options[21]).toBe('10:05');
    expect(options[22]).toBe('10:30');
  });
});

describe('TimePicker typed trigger', () => {
  it('shows the value in an editable field rather than static text', () => {
    const markup = renderTrigger(<TimePicker value="13:05" />);
    expect(markup).toContain('data-slot="time-picker-input"');
    expect(markup).toContain('value="1:05 PM"');
  });

  it('disables the field and the clock button together', () => {
    const markup = renderTrigger(<TimePicker disabled />);
    // The attribute, not the `disabled:` variants in the class names.
    expect(markup.match(/disabled=""/g)).toHaveLength(2);
  });

  it('is not marked invalid before anything has been typed', () => {
    expect(renderTrigger(<TimePicker value="09:30" />)).not.toContain(
      'aria-invalid'
    );
  });
});
