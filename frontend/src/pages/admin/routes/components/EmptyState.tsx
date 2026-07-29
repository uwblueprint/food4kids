import boyEdgeCaseNoQuestionMark from '@/assets/illustrations/boy-edge-case-no-question-mark.png';
import boyEdgeCaseWithQuestions from '@/assets/illustrations/boy-edge-case-with-questions.png';
import girlConfused from '@/assets/illustrations/girl-confused.png';
import { cn } from '@/lib/utils';

const IMAGES = {
  'girl-confused': girlConfused,
  'boy-edge-case-with-questions': boyEdgeCaseWithQuestions,
  'boy-edge-case-no-question-mark': boyEdgeCaseNoQuestionMark,
};

interface EmptyStateProps {
  image?:
    | 'girl-confused'
    | 'boy-edge-case-with-questions'
    | 'boy-edge-case-no-question-mark';
  title: string;
  description: string;
  /**
   * Tighter illustration and padding, for a table that shares a screen with
   * others (the route-generation steps) rather than owning the page.
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
        compact ? 'gap-1 py-8' : 'gap-3 py-16'
      )}
    >
      <img
        src={IMAGES[image]}
        alt=""
        className={cn('w-auto', compact ? 'h-28' : 'h-48')}
      />
      <div>
        <p className="text-p1 text-grey-500 font-medium">{title}</p>
        <p className="text-p2 text-grey-400">{description}</p>
      </div>
    </div>
  );
}
