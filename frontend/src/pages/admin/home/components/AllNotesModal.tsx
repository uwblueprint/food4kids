import { useState } from 'react';

import type { NoteFeedSort } from '@/api/generated/types.gen';
import { useNotesFeed } from '@/api/notes';
import {
  Button,
  Dropdown,
  DropdownContent,
  DropdownItem,
  DropdownTrigger,
  DropdownValue,
  ModalClose,
  ModalContent,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Pagination,
  Spinner,
} from '@/common/components';
import { cn } from '@/lib/utils';

import { NoteFeedEntry } from './NoteFeedEntry';

export function AllNotesModal() {
  const [sort, setSort] = useState<NoteFeedSort>('recent');
  const [page, setPage] = useState(1);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const { data, isPending, isError, isFetching, refetch } = useNotesFeed({
    sort,
    page,
    page_size: 20,
  });
  const selectedNote = data?.items.find((note) => note.note_id === selectedId);

  return (
    <ModalContent className="max-h-[90dvh] w-[calc(100%-2rem)] max-w-[960px] overflow-y-auto bg-white">
      <ModalHeader>
        <ModalTitle variant="confirmation">All Notes</ModalTitle>
      </ModalHeader>
      <div className="flex items-center justify-end gap-2">
        <span id="notes-sort-label" className="text-p2 text-grey-400">
          Sort by:
        </span>
        <Dropdown
          value={sort}
          onValueChange={(value) => {
            setSort(value as NoteFeedSort);
            setPage(1);
            setSelectedId(null);
          }}
        >
          <DropdownTrigger
            aria-labelledby="notes-sort-label"
            className="w-44 bg-white"
          >
            <DropdownValue />
          </DropdownTrigger>
          <DropdownContent>
            <DropdownItem value="recent">Recent</DropdownItem>
            <DropdownItem value="oldest">Oldest</DropdownItem>
            <DropdownItem value="driver">Driver (A–Z)</DropdownItem>
            <DropdownItem value="location">Location (A–Z)</DropdownItem>
          </DropdownContent>
        </Dropdown>
      </div>
      <div className="tablet:h-[420px] tablet:grid-cols-2 grid min-h-[320px] grid-cols-1 gap-4">
        <div className="border-grey-200 min-h-0 overflow-y-auto rounded-xl border">
          {isPending ? (
            <div className="flex justify-center p-8">
              <Spinner size="sm" />
            </div>
          ) : isError ? (
            <div role="alert" className="text-p2 text-grey-400 p-4">
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
            <p className="text-p2 text-grey-400 p-4">No notes yet.</p>
          ) : (
            <ul className="divide-grey-200 divide-y">
              {data.items.map((note) => (
                <li key={note.note_id}>
                  <button
                    type="button"
                    aria-pressed={note.note_id === selectedId}
                    onClick={() => setSelectedId(note.note_id)}
                    className={cn(
                      'w-full cursor-pointer p-4 text-left hover:bg-blue-50 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-blue-300',
                      note.note_id === selectedId && 'bg-blue-50'
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
          className="border-grey-200 min-h-0 overflow-y-auto rounded-xl border p-4"
        >
          {selectedNote && !isError ? (
            <NoteFeedEntry note={selectedNote} />
          ) : (
            <div className="text-p2 text-grey-400 flex h-full min-h-32 items-center justify-center text-center">
              Select a note to display it here
            </div>
          )}
        </section>
      </div>
      {!isError && data && (
        <Pagination
          page={page}
          totalPages={data.total_pages}
          onPageChange={(nextPage) => {
            setPage(nextPage);
            setSelectedId(null);
          }}
          className="mt-0 flex-wrap gap-3"
        />
      )}
      <ModalFooter className="justify-end">
        <ModalClose asChild>
          <Button variant="primary">Close</Button>
        </ModalClose>
      </ModalFooter>
    </ModalContent>
  );
}
