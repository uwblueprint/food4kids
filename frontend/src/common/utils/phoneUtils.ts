/**
 * Render a stored phone number the way the designs show it.
 *
 * The API stores RFC 3966 — `tel:+1-519-576-3443` or, with an extension,
 * `tel:+1-519-576-3443;ext=1`. Figma shows `(519) 576-3443`, so every screen
 * that displays a number formats it here rather than printing the raw column.
 *
 * Only the North American form is matched, because that is the only form the
 * backend produces: `validate_phone` parses with region "CA" and rejects what
 * `phonenumbers` calls invalid.
 *
 * Anything else is returned untouched rather than throwing, because one screen
 * legitimately shows unnormalized values: the import Validate step keeps a row's
 * raw spreadsheet text when the number fails validation, so the admin can see
 * what they typed and fix it. Those cells are already flagged red with an
 * "Invalid Phone Number" alert — reformatting or hiding them would be worse.
 */
const RFC3966 = /^tel:\+1-(\d{3})-(\d{3})-(\d{4})(?:;ext=(\d+))?$/;

export const formatPhone = (value: string): string => {
  const match = RFC3966.exec(value);
  if (!match) return value;

  const [, area, exchange, line, extension] = match;
  const formatted = `(${area}) ${exchange}-${line}`;
  // "Ext." capitalized, per Settings — the one frame that shows an extension.
  return extension ? `${formatted} Ext. ${extension}` : formatted;
};
