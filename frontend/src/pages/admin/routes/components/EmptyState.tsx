import boyEdgeCaseNoQuestionMark from '@/assets/illustrations/boy-edge-case-no-question-mark.png';
import boyEdgeCaseWithQuestions from '@/assets/illustrations/boy-edge-case-with-questions.png';
import girlConfused from '@/assets/illustrations/girl-confused.png';
import girlSearching from '@/assets/illustrations/girl-searching.png';
import { cn } from '@/lib/utils';

const IMAGES = {
  'girl-confused': girlConfused,
  'girl-searching': girlSearching,
  'boy-edge-case-with-questions': boyEdgeCaseWithQuestions,
  'boy-edge-case-no-question-mark': boyEdgeCaseNoQuestionMark,
};

interface EmptyStateProps {
  image?: keyof typeof IMAGES;
  title: string;
  description: string;
  /**
   * The route-generation variant: the illustration is cropped into a 106px
   * blue disc rather than standing free, and both lines drop to the table's
   * own 14/600. Used where a table shares a screen with others rather than
   * owning the page.
   *
   * This is a prop rather than a `[&_td>div]` arbitrary variant on the
   * DataTable wrapper: that selector also matched the populated cells' own
   * wrapper divs, which nearly doubled the height of every changed row.
   */
  compact?: boolean;
}

export function EmptyState({
  title,
  description,
  image = 'girl-confused',
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center text-center',
        compact ? 'gap-2 py-6' : 'gap-3 py-16'
      )}
    >
      {compact ? (
        // The source PNGs are 1000×1000 with a wide transparent margin, so
        // filling the disc means scaling past it and pulling the figure up
        // until the head sits inside — hence the offsets rather than a plain
        // object-cover.
        <div className="size-[106px] shrink-0 overflow-hidden rounded-full bg-blue-50">
          <img
            src={IMAGES[image]}
            alt=""
            className="-mt-[55px] -ml-[62px] w-[246px] max-w-none"
          />
        </div>
      ) : (
        <img src={IMAGES[image]} alt="" className="h-48 w-auto" />
      )}
      <div>
        <p
          className={cn(
            'text-grey-500',
            compact ? 'text-p2 font-semibold' : 'text-p1 font-medium'
          )}
        >
          {title}
        </p>
        <p className={cn('text-p2 text-grey-400', compact && 'font-semibold')}>
          {description}
        </p>
      </div>
    </div>
  );
}
