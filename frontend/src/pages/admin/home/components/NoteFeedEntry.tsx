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
  const parsed = note.created_at ? new Date(note.created_at) : null;
  const createdAt = parsed && !Number.isNaN(parsed.getTime()) ? parsed : null;
  const time = createdAt
    ?.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' })
    .replace(/\s/g, '');
  const day = createdAt?.getDate() ?? 0;
  const suffix =
    day % 100 >= 11 && day % 100 <= 13
      ? 'th'
      : (({ 1: 'st', 2: 'nd', 3: 'rd' } as Record<number, string>)[day % 10] ??
        'th');
  const fullDate = createdAt
    ? `${createdAt.toLocaleDateString('en-US', { month: 'long' })} ${day}${suffix}, ${time}`
    : null;
  const author = note.is_system
    ? 'System'
    : note.author_name?.trim() || 'Unknown author';

  if (preview || cardPreview) {
    return (
      <div className="text-grey-500 min-w-0 text-base leading-6 break-words">
        <p
          className={cn(
            'flex items-center gap-2',
            !note.is_read && 'font-bold'
          )}
        >
          {author}
          {!note.is_read && (
            <span
              role="img"
              aria-label="Unread note"
              className="inline-block size-2 shrink-0 rounded-full bg-blue-300"
            />
          )}
        </p>
        <p
          className={cn('text-sm leading-5', !note.is_read && 'font-semibold')}
        >
          {note.location_name} - {note.location_group_name}
          {time && (
            <>
              {' '}
              · <time dateTime={note.created_at ?? undefined}>{time}</time>
            </>
          )}
        </p>
        <p className={cn(preview ? 'truncate' : 'whitespace-pre-wrap')}>
          {note.message}
        </p>
      </div>
    );
  }

  return (
    <article className="shadow-admin-bento text-grey-500 rounded-3xl bg-white p-8 text-base leading-6">
      <p className="break-words whitespace-pre-wrap">{note.message}</p>
      {createdAt && (
        <p className="text-grey-400 mt-2 text-sm">
          <time dateTime={note.created_at ?? undefined}>{fullDate}</time>
        </p>
      )}
      {(note.attachments?.length ?? 0) > 0 && (
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
    </article>
  );
}
