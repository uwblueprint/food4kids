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
      <Card className="shadow-admin-bento min-h-0 overflow-hidden rounded-4xl p-0">
        <CardHeader className="min-h-[60px] shrink-0 flex-row items-center justify-between gap-2 px-6 py-4">
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
            <div role="alert" className="text-p2 text-grey-400 px-6 py-4">
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
            <ul className="pb-6">
              {data.items.map((note) => (
                <li key={note.note_id} className="px-6 py-3 first:pt-2">
                  <NoteFeedEntry note={note} cardPreview />
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
