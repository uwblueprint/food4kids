import { useState } from 'react';

import type { NoteFeedItem, NoteFeedSort } from '@/api/generated/types.gen';
import { useMarkNoteRead, useNotesFeed } from '@/api/notes';
import SearchIcon from '@/assets/icons/search.svg?react';
import XIcon from '@/assets/icons/x.svg?react';
import boyPointing from '@/assets/illustrations/boy-pointing.png';
import {
  Button,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  Input,
  ModalClose,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Pagination,
  Spinner,
} from '@/common/components';
import { useDebouncedValue } from '@/common/hooks/useDebouncedValue';
import { cn } from '@/lib/utils';

import { NoteFeedEntry } from './NoteFeedEntry';

export function AllNotesModal() {
  const [sort, setSort] = useState<NoteFeedSort>('unread');
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const searchQuery = useDebouncedValue(search.trim(), 250);
  const [selected, setSelected] = useState<NoteFeedItem | null>(null);
  const { data, isPending, isError, isFetching, isPlaceholderData, refetch } =
    useNotesFeed(
      { sort, search: searchQuery || undefined, page, page_size: 20 },
      { keepPreviousData: true }
    );
  const markRead = useMarkNoteRead();
  const listBusy = isPlaceholderData || searchQuery !== search.trim();
  const currentNote = data?.items.find(
    (note) => note.note_id === selected?.note_id
  );
  // Reading a note moves it within the unread-first feed. Keep its full text
  // visible if it moves to another page; other sorts still clear deleted notes.
  if (
    selected &&
    data &&
    !listBusy &&
    !isError &&
    !currentNote &&
    sort !== 'unread'
  )
    setSelected(null);
  const selectedNote = currentNote ?? selected;
  const chooseNote = (note: NoteFeedItem) => {
    setSelected(note);
    markRead.reset();
    if (!note.is_read) markRead.mutate({ path: { note_id: note.note_id } });
  };
  const hasAddress = Boolean(
    selectedNote && !isError && selectedNote.location_address?.trim()
  );
  const email =
    !isError &&
    selectedNote?.author_role === 'driver' &&
    !selectedNote.is_system
      ? selectedNote.author_email
      : null;

  return (
    <ModalContent
      showCloseButton={false}
      className="max-h-[90dvh] w-[calc(100%-2rem)] max-w-[1296px] gap-6 overflow-y-auto rounded-4xl bg-white p-8"
    >
      <ModalHeader className="mb-2">
        <ModalTitle variant="confirmation">All Notes</ModalTitle>
      </ModalHeader>
      <ModalClose
        aria-label="Close"
        className="text-grey-500 hover:bg-grey-200 absolute top-7 right-7 flex size-8 cursor-pointer items-center justify-center rounded-full focus-visible:outline-2 focus-visible:outline-blue-300"
      >
        <XIcon className="size-5" />
      </ModalClose>
      <div className="flex flex-wrap items-center gap-5">
        <div className="bg-grey-200 relative w-full max-w-108 rounded-full">
          <SearchIcon
            aria-hidden="true"
            className="absolute top-1/2 left-5 size-5 -translate-y-1/2"
          />
          <Input
            aria-label="Search notes"
            placeholder="Search anything"
            maxLength={200}
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage(1);
              setSelected(null);
              markRead.reset();
            }}
            className="h-16 rounded-full bg-transparent pl-14 outline-none"
          />
        </div>
        <div className="flex items-center gap-3">
          <span id="notes-sort-label" className="text-grey-500 text-base">
            Sort by:
          </span>
          <Dropdown
            value={sort}
            disabled={listBusy}
            onValueChange={(value) => {
              setSort(value as NoteFeedSort);
              setPage(1);
              setSelected(null);
              markRead.reset();
            }}
          >
            <DropdownTrigger
              aria-labelledby="notes-sort-label"
              className="h-16 w-48 rounded-full bg-white"
            >
              <DropdownValue />
            </DropdownTrigger>
            <DropdownContent>
              <DropdownItem value="unread">Unread</DropdownItem>
              <DropdownItem value="recent">Newest</DropdownItem>
              <DropdownItem value="oldest">Oldest</DropdownItem>
              <DropdownItem value="driver">Driver (A–Z)</DropdownItem>
              <DropdownItem value="location">Location (A–Z)</DropdownItem>
            </DropdownContent>
          </Dropdown>
        </div>
      </div>
      <div className="tablet:h-[576px] tablet:grid-cols-[1.3fr_1fr] grid min-h-[320px] shrink-0 grid-cols-1 gap-4">
        <div
          aria-busy={isFetching}
          className="border-grey-300 tablet:h-auto h-72 min-h-0 overflow-y-auto rounded-3xl border"
        >
          {isPending ? (
            <div className="flex justify-center p-8">
              <Spinner size="sm" />
            </div>
          ) : isError ? (
            <div role="alert" className="text-grey-400 p-4">
              <p>Couldn&apos;t load notes.</p>
              <Button
                variant="textLink"
                disabled={isFetching}
                onClick={() => void refetch()}
              >
                Retry
              </Button>
            </div>
          ) : !data?.items.length ? (
            <p className="text-grey-400 p-6">
              {searchQuery
                ? 'No results. Try being less specific.'
                : 'No notes yet.'}
            </p>
          ) : (
            <ul
              className={cn(
                'divide-grey-300 divide-y',
                listBusy && 'opacity-50'
              )}
            >
              {data.items.map((note) => (
                <li key={note.note_id}>
                  <button
                    type="button"
                    disabled={listBusy}
                    aria-pressed={note.note_id === selected?.note_id}
                    onClick={() => chooseNote(note)}
                    className={cn(
                      'hover:bg-grey-200 w-full min-w-0 cursor-pointer px-8 py-6 text-left focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-blue-300',
                      note.note_id === selected?.note_id
                        ? 'bg-blue-50 hover:bg-blue-50'
                        : 'hover:bg-grey-200'
                    )}
                  >
                    <NoteFeedEntry note={note} preview />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <section
          aria-label="Selected note"
          className="border-grey-300 tablet:max-h-none tablet:min-h-0 max-h-96 min-h-80 overflow-y-auto rounded-3xl border"
        >
          {selectedNote && !isError ? (
            <NoteFeedEntry note={selectedNote} />
          ) : (
            <div className="flex h-full min-h-64 flex-col items-center justify-center gap-1 p-6 text-center">
              <img
                src={boyPointing}
                alt=""
                className="mb-3 size-52 object-contain"
              />
              <p className="text-grey-500 text-base">Nothing selected</p>
              <p className="text-grey-400 text-sm">
                Select a note to display it here
              </p>
            </div>
          )}
        </section>
      </div>
      <div
        role="status"
        aria-atomic="true"
        className={cn('text-red text-sm', !markRead.isError && 'sr-only')}
      >
        {markRead.isError && (
          <>
            <span>Couldn&apos;t mark this note as read. </span>
            <Button
              variant="textLink"
              onClick={() =>
                selectedNote &&
                markRead.mutate({ path: { note_id: selectedNote.note_id } })
              }
            >
              Retry marking as read
            </Button>
          </>
        )}
      </div>
      {!isError && data && data.total_pages > 1 && (
        <fieldset
          disabled={listBusy}
          aria-label="Notes pagination"
          className="min-w-0"
        >
          <Pagination
            page={page}
            totalPages={data.total_pages}
            onPageChange={(next) => {
              setPage(next);
              setSelected(null);
              markRead.reset();
            }}
            className="mt-0 flex-wrap gap-3"
          />
        </fieldset>
      )}
      <ModalFooter className="flex-wrap justify-end">
        {hasAddress ? (
          <Button variant="secondary" asChild>
            <a
              href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedNote!.location_address)}`}
              target="_blank"
              rel="noreferrer"
            >
              View address
            </a>
          </Button>
        ) : (
          <Button variant="secondary" disabled>
            View address
          </Button>
        )}
        {email ? (
          <Button variant="secondary" asChild>
            <a href={`mailto:${encodeURIComponent(email)}`}>Email driver</a>
          </Button>
        ) : (
          <Button variant="secondary" disabled>
            Email driver
          </Button>
        )}
        <ModalClose asChild>
          <Button>Close</Button>
        </ModalClose>
      </ModalFooter>
    </ModalContent>
  );
}
