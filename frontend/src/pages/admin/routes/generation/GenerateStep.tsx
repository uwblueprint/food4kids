import { Card, Progress, Spinner } from '@/common/components';

const MOCK_COMPLETED = 1;
const MOCK_TOTAL = 3;

export function GenerateStep() {
  const percent = Math.round((MOCK_COMPLETED / MOCK_TOTAL) * 100);

  return (
    <Card className="flex flex-col gap-6 px-8 pt-6 pb-8">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h2 className="text-grey-500">Route Generation</h2>
        <p className="font-nunito-sans text-lg text-grey-500">
          Creating optimized delivery routes.
        </p>
      </div>

      {/* Loading content */}
      <div className="flex flex-col items-center gap-12">
        {/* Spinner + text */}
        <div className="flex flex-col items-center gap-6">
          <Spinner size="lg" />
          <div className="flex flex-col items-center gap-1 text-center">
            <p className="font-nunito-sans text-base font-bold text-grey-500">
              Generating Routes
            </p>
            <p className="font-nunito-sans text-base text-grey-500">
              This may take up to 5 minutes...
            </p>
          </div>
        </div>

        {/* Progress */}
        <div className="flex flex-col items-center gap-2">
          <Progress value={percent} className="h-2 w-80" />
          <p className="font-nunito-sans text-sm text-grey-500">
            {MOCK_COMPLETED}/{MOCK_TOTAL} route groups completed
          </p>
        </div>
      </div>
    </Card>
  );
}
