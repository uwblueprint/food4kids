/**
 * Render a stored RFC 3966 number the way the designs show it: `(519) 576-3443`.
 *
 * Non-NANP numbers are storable but have no design, so they render as a plain
 * international number. Anything unrecognized is returned untouched — the
 * import Validate step shows raw spreadsheet text for numbers that failed
 * validation, already flagged red.
 */
const NANP = /^tel:\+1-(\d{3})-(\d{3})-(\d{4})(?:;ext=(\d+))?$/;
const INTERNATIONAL = /^tel:(\+\d[\d-]*)(?:;ext=(\d+))?$/;

// "Ext." capitalized, per Settings — the one frame that shows an extension.
const withExtension = (formatted: string, extension: string | undefined) =>
  extension ? `${formatted} Ext. ${extension}` : formatted;

export const formatPhone = (value: string): string => {
  const nanp = NANP.exec(value);
  if (nanp) {
    const [, area, exchange, line, extension] = nanp;
    return withExtension(`(${area}) ${exchange}-${line}`, extension);
  }

  const international = INTERNATIONAL.exec(value);
  if (international) {
    const [, number, extension] = international;
    return withExtension(number.replace(/-/g, ' '), extension);
  }

  return value;
};

export const formatPhoneInput = (value: string): string => {
  const digits = value.replace(/\D/g, '').slice(0, 10);
  if (digits.length === 0) return '';
  if (digits.length <= 3) {
    return `(${digits}`;
  }
  if (digits.length <= 6) {
    return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
  }
  return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6)}`;
};
