import type { NoteFeedItem } from '@/api/generated/types.gen';

export function NoteFeedEntry({
  note,
  preview = false,
}: {
  note: NoteFeedItem;
  preview?: boolean;
}) {
  const date = note.created_at
    ? new Date(note.created_at).toLocaleString('en-US', {
        month: 'short',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
      })
    : null;

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
        className={`mt-2 whitespace-pre-wrap ${preview ? 'line-clamp-3' : ''}`}
      >
        {note.message}
      </p>
      {!preview && (note.attachments?.length ?? 0) > 0 && (
        <div className="mt-3 flex flex-wrap gap-2">
          {note.attachments?.map((attachment) => (
            <a
              key={attachment.filename}
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
