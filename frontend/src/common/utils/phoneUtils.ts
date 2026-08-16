/**
 * Render a stored phone number the way the designs show it.
 *
 * The API stores RFC 3966 — `tel:+1-519-576-3443` or, with an extension,
 * `tel:+1-519-576-3443;ext=1`. Figma shows `(519) 576-3443`, so every screen
 * that displays a number formats it here rather than printing the raw column.
 *
 * North American numbers get the designed form. A number with an explicit
 * non-NANP country code is still storable — `validate_phone` parses with region
 * "CA", but `phonenumbers` ignores that default whenever the input already
 * carries a country code, so `+44 20 7946 0958` validates and stores as
 * `tel:+44-20-7946-0958`. There is no design for that case; it at least must
 * not leak a raw `tel:` URI into the UI, so it renders as the plain
 * international number.
 *
 * A value matching neither shape is returned untouched rather than throwing,
 * because one screen legitimately shows unnormalized values: the import
 * Validate step keeps a row's raw spreadsheet text when the number fails
 * validation, so the admin can see what they typed and fix it. Those cells are
 * already flagged red with an "Invalid Phone Number" alert — reformatting or
 * hiding them would be worse.
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
