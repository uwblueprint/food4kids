import type { NoteFeedItem } from '@/api/generated/types.gen';
import { cn } from '@/lib/utils';

export function NoteFeedEntry({
  note,
  preview = false,
  cardPreview = false,
}: {
  note: NoteFeedItem;
  preview?: boolean;
  cardPreview?: boolean;
}) {
  const createdAt = note.created_at ? new Date(note.created_at) : null;
  const date =
    createdAt && !Number.isNaN(createdAt.getTime())
      ? createdAt.toLocaleString('en-US', {
          month: 'short',
          day: 'numeric',
          year: 'numeric',
          hour: 'numeric',
          minute: '2-digit',
        })
      : null;

  const time =
    createdAt && !Number.isNaN(createdAt.getTime())
      ? createdAt
          .toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
          })
          .replace(/\s/g, '')
      : null;

  if (cardPreview) {
    return (
      <div className="text-grey-500 min-w-0 text-base leading-6 break-words">
        <p className="font-bold">
          {note.is_system
            ? 'System'
            : note.author_name?.trim() || 'Unknown author'}
        </p>
        <p className="text-sm leading-5">
          {note.location_name} - {note.location_group_name}
          {time && (
            <>
              {' • '}
              <time dateTime={note.created_at ?? undefined}>{time}</time>
            </>
          )}
        </p>
        <p className="whitespace-pre-wrap">{note.message}</p>
      </div>
    );
  }

  return (
    <div className="text-p2 text-grey-500 min-w-0 break-words">
      <p className="font-semibold">
        {note.is_system
          ? 'System'
          : note.author_name?.trim() || 'Unknown author'}
        {' · '}
        {note.location_name}
      </p>
      <p className="text-p3 text-grey-400">
        {note.location_group_name}
        {date && (
          <>
            {' '}
            · <time dateTime={note.created_at ?? undefined}>{date}</time>
          </>
        )}
      </p>
      {!preview && (
        <p className="text-grey-400 mt-1">{note.location_address}</p>
      )}
      <p
        className={cn(
          'mt-2 font-normal whitespace-pre-wrap',
          preview && 'line-clamp-3'
        )}
      >
        {note.message}
      </p>
      {!preview && (note.attachments?.length ?? 0) > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {note.attachments?.map((attachment) => (
            <a
              key={attachment.url}
              href={attachment.url}
              target="_blank"
              rel="noreferrer"
              className="border-grey-300 block overflow-hidden rounded-lg border focus-visible:outline-2 focus-visible:outline-blue-300"
            >
              <img
                src={attachment.url}
                alt={attachment.filename}
                className="size-24 object-cover"
                loading="lazy"
              />
            </a>
          ))}
        </div>
      )}
    </div>
  );
}
