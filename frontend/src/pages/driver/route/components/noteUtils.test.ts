import { describe, expect, it } from 'vitest';

import type { NoteRead } from '@/api/generated/types.gen';

import { noteAuthorLabel } from './noteUtils';

function makeNote(overrides: Partial<NoteRead> = {}): NoteRead {
  return {
    note_id: 'note-1',
    note_chain_id: 'chain-1',
    message: 'Hello',
    user_id: 'user-other',
    is_system: false,
    author_name: 'Casey Driver',
    ...overrides,
  };
}

describe('noteAuthorLabel', () => {
  it('returns System for system notes', () => {
    expect(
      noteAuthorLabel(
        makeNote({ is_system: true, user_id: null, author_name: null }),
        'me',
        'Me User'
      )
    ).toBe('System');
  });

  it('returns You for own notes', () => {
    expect(
      noteAuthorLabel(
        makeNote({ user_id: 'me', author_name: 'Me User' }),
        'me',
        'Me User'
      )
    ).toBe('You');
  });

  it('returns author_name for other authors (seeded mixed notes)', () => {
    expect(
      noteAuthorLabel(
        makeNote({ user_id: 'driver-1', author_name: 'Casey Driver' }),
        'me',
        'Me User'
      )
    ).toBe('Casey Driver');
  });

  it('falls back to Unknown when author_name is missing', () => {
    expect(
      noteAuthorLabel(
        makeNote({ user_id: 'driver-1', author_name: null }),
        'me',
        'Me User'
      )
    ).toBe('Unknown');
  });
});
