import { describe, expect, it } from 'vitest';

import { contactSentence } from './ErrorScreen.contact';

// Every name/phone combination is reachable and each must stay grammatical —
// the failure guarded against is a literal "contact  at  for help."
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
    // Both fields are undefined until the query resolves.
    expect(contactSentence(undefined, undefined)).toBeNull();
    expect(contactSentence(undefined, 'tel:+1-519-576-3443')).toBe(
      'If the issue persists, call (519) 576-3443 for help.'
    );
    expect(contactSentence('Emily Loro', undefined)).toBe(
      'If the issue persists, contact Emily Loro for help.'
    );
  });

  it('treats a blank or whitespace-only name as no name', () => {
    // min_length=1 rules out "", but an all-spaces name is still storable.
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
    // Storable, no design for it, but must not surface as a raw "tel:" URI.
    expect(contactSentence(null, 'tel:+44-20-7946-0958')).toBe(
      'If the issue persists, call +44 20 7946 0958 for help.'
    );
  });
});
