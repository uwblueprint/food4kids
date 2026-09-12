import { useNotes } from '@/api/notes';

interface StopNotesCellProps {
  /** The stop's note chain; null when the location has no notes. */
  noteChainId?: string | null;
}

/**
 * Shows a stop's latest driver note (truncated) in the Stops table, fetched
 * from the stop's note chain. Renders "—" when the stop has no chain or the
 * chain is empty.
 */
export function StopNotesCell({ noteChainId }: StopNotesCellProps) {
  const { data: notes, isLoading } = useNotes(noteChainId);

  if (!noteChainId) return <span className="text-grey-500">—</span>;
  if (isLoading) return <span className="text-grey-500">…</span>;

  // Newest note wins; ignore any without a message.
  const latest = (notes ?? [])
    .filter((n) => n.message?.trim())
    .sort(
      (a, b) =>
        new Date(b.created_at ?? 0).getTime() -
        new Date(a.created_at ?? 0).getTime()
    )[0];

  if (!latest) return <span className="text-grey-500">—</span>;

  return (
    <span className="line-clamp-1 max-w-[16rem]" title={latest.message}>
      {latest.message}
    </span>
  );
}
