import { describe, expect, it } from 'vitest';

import { formatPhone } from './phoneUtils';

describe('formatPhone', () => {
  it('renders a stored number the way the designs show it', () => {
    expect(formatPhone('tel:+1-519-576-3443')).toBe('(519) 576-3443');
  });

  it('keeps the extension', () => {
    expect(formatPhone('tel:+1-519-576-3443;ext=1')).toBe(
      '(519) 576-3443 ext. 1'
    );
  });

  it('keeps a multi-digit extension', () => {
    expect(formatPhone('tel:+1-519-576-3443;ext=224')).toBe(
      '(519) 576-3443 ext. 224'
    );
  });

  it.each([
    'tel:+1-416-221-8456',
    'tel:+1-289-234-1245',
    'tel:+1-519-349-5094',
  ])('formats %s', (value) => {
    expect(formatPhone(value)).toMatch(/^\(\d{3}\) \d{3}-\d{4}$/);
  });

  // The import Validate step shows a row's raw spreadsheet text when the
  // number failed validation, so the admin can see what to fix. Those values
  // must survive untouched rather than being mangled or hidden.
  it.each([
    'a',
    '',
    '519-576-3443',
    '(519) 576-3443',
    '+15195763443',
    'tel:+44-20-8366-1177',
    'tel:+1-519-576-3443;ext=',
    'tel:+1-5195-76-3443',
  ])('passes through unrecognized value %s', (value) => {
    expect(formatPhone(value)).toBe(value);
  });

  it('is stable when applied twice to a formatted value', () => {
    const once = formatPhone('tel:+1-519-576-3443');
    expect(formatPhone(once)).toBe(once);
  });
});
