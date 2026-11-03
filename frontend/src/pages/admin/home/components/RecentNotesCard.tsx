import { useState } from 'react';

import { useNotesFeed } from '@/api/notes';
import {
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Modal,
  ModalTrigger,
  Spinner,
} from '@/common/components';

import { AllNotesModal } from './AllNotesModal';
import { NoteFeedEntry } from './NoteFeedEntry';

export function RecentNotesCard() {
  const [open, setOpen] = useState(false);
  const { data, isPending, isError, isFetching, refetch } = useNotesFeed({
    sort: 'recent',
    page: 1,
    page_size: 5,
  });

  return (
    <Modal open={open} onOpenChange={setOpen}>
      <Card className="shadow-admin-bento min-h-0 rounded-4xl">
        <CardHeader className="mb-4 flex-row items-center justify-between gap-2">
          <CardTitle>Recent Notes</CardTitle>
          <ModalTrigger asChild>
            <Button variant="textLink" className="shrink-0">
              View all
            </Button>
          </ModalTrigger>
        </CardHeader>
        <CardContent className="min-h-0 overflow-y-auto">
          {isPending ? (
            <div className="flex justify-center py-8">
              <Spinner size="sm" />
            </div>
          ) : isError ? (
            <div role="alert" className="text-p2 text-grey-400">
              <p>Couldn&apos;t load recent notes.</p>
              <Button
                variant="textLink"
                disabled={isFetching}
                onClick={() => void refetch()}
              >
                Retry
              </Button>
            </div>
          ) : !data?.items.length ? (
            <p className="text-p2 text-grey-400 py-6 text-center">
              No notes yet.
            </p>
          ) : (
            <ul className="divide-grey-200 divide-y">
              {data.items.map((note) => (
                <li key={note.note_id} className="py-3 first:pt-0">
                  <NoteFeedEntry note={note} preview />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
      {open && <AllNotesModal />}
    </Modal>
  );
}
