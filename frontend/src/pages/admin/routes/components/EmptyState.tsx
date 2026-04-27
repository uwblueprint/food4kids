import girlConfused from '@/assets/illustrations/girl-confused.png';
import boyEdgeCaseWithQuestions from '@/assets/illustrations/boy-edge-case-with-questions.png';
import boyEdgeCaseNoQuestionMark from '@/assets/illustrations/boy-edge-case-no-question-mark.png';

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
}

export function EmptyState({
  title,
  description,
  image = 'girl-confused',
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-16 text-center">
      <img src={IMAGES[image]} alt="" className="h-48 w-auto" />
      <div>
        <p className="text-p1 text-grey-500 font-medium">{title}</p>
        <p className="text-p2 text-grey-400">{description}</p>
      </div>
    </div>
  );
}
