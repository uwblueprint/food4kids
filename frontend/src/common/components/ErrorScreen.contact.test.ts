import { describe, expect, it } from 'vitest';

import { contactSentence } from './ErrorScreen.contact';

/**
 * The catch-all error page's contact line, built from `system_settings`.
 *
 * Both fields are independently nullable, and the page renders before the
 * (unauthenticated) contact request resolves, so every combination of
 * name/phone × set/unset/undefined is reachable in practice. The sentence has
 * to stay grammatical in all of them — the failure this guards against is the
 * literal "contact  at  for help." a naive template would produce.
 */
describe('contactSentence', () => {
  it('names the contact and their number when both are configured', () => {
    expect(contactSentence('Emily Loro', 'tel:+1-519-576-3443')).toBe(
      'If the issue persists, contact Emily Loro at (519) 576-3443 for help.'
    );
  });

  it('keeps the extension, which is why phones are stored RFC 3966', () => {
    expect(contactSentence('Emily Loro', 'tel:+1-519-576-3443;ext=1')).toBe(
      'If the issue persists, contact Emily Loro at (519) 576-3443 Ext. 1 for help.'
    );
  });

  it('names the contact alone when no number is configured', () => {
    expect(contactSentence('Emily Loro', null)).toBe(
      'If the issue persists, contact Emily Loro for help.'
    );
  });

  it('switches to "call" when there is a number but no name', () => {
    expect(contactSentence(null, 'tel:+1-519-576-3443')).toBe(
      'If the issue persists, call (519) 576-3443 for help.'
    );
  });

  it('drops the sentence entirely when neither is configured', () => {
    expect(contactSentence(null, null)).toBeNull();
  });

  it('treats the pre-fetch undefined state as unconfigured', () => {
    // The page renders immediately; the query resolves after. Until it does,
    // both fields are undefined and the page must not promise a number.
    expect(contactSentence(undefined, undefined)).toBeNull();
    expect(contactSentence(undefined, 'tel:+1-519-576-3443')).toBe(
      'If the issue persists, call (519) 576-3443 for help.'
    );
    expect(contactSentence('Emily Loro', undefined)).toBe(
      'If the issue persists, contact Emily Loro for help.'
    );
  });

  it('treats a blank or whitespace-only name as no name', () => {
    // The API's min_length=1 makes "" unreachable through a PATCH, but a name
    // that is all spaces is not, and "contact     at ..." reads as a bug.
    expect(contactSentence('', 'tel:+1-519-576-3443')).toBe(
      'If the issue persists, call (519) 576-3443 for help.'
    );
    expect(contactSentence('   ', 'tel:+1-519-576-3443')).toBe(
      'If the issue persists, call (519) 576-3443 for help.'
    );
    expect(contactSentence('   ', null)).toBeNull();
  });

  it('trims a padded name rather than embedding the padding', () => {
    expect(contactSentence('  Emily Loro  ', null)).toBe(
      'If the issue persists, contact Emily Loro for help.'
    );
  });

  it('never leaks a raw tel: URI into the sentence', () => {
    // A non-NANP number is storable (validate_phone honours an explicit country
    // code), and there is no design for it — but the reader must not be shown
    // "tel:+44-20-7946-0958". formatPhone renders it as a plain international
    // number; this pins that the error copy goes through it.
    expect(contactSentence(null, 'tel:+44-20-7946-0958')).toBe(
      'If the issue persists, call +44 20 7946 0958 for help.'
    );
  });
});
