import { useState } from 'react';

import { useAuthStore } from '@/api/authStore';
import { useNotesFeed } from '@/api/notes';
import ExpandIcon from '@/assets/icons/expand-content.svg?react';
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
import { cn } from '@/lib/utils';

import { AllNotesModal } from './AllNotesModal';
import { NoteFeedEntry } from './NoteFeedEntry';

export function RecentNotesCard() {
  const [open, setOpen] = useState(false);
  const userId = useAuthStore((state) => state.user?.id);
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
            <Button
              variant="ghost"
              shape="circular"
              aria-label="View all"
              className="tablet:size-8 size-8 shrink-0 bg-blue-50"
            >
              <ExpandIcon className="size-4" />
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
                <li
                  key={note.note_id}
                  className={cn('px-6 py-4', !note.is_read && 'bg-grey-200')}
                >
                  <NoteFeedEntry note={note} cardPreview />
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
      {open && <AllNotesModal key={userId} />}
    </Modal>
  );
}
