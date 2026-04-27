import { Card, Spinner } from '@/common/components';

export function GenerateStep() {
  return (
    <Card className="flex flex-col gap-6 p-6">
      {/* Header */}
      <div className="flex flex-col gap-1">
        <h2 className="text-grey-500">Route Generation</h2>
        <p className="text-p1 text-grey-400">
          Creating optimized delivery routes.
        </p>
      </div>

      {/* Loading content */}
      <div className="flex flex-col items-center gap-6 py-10">
        <Spinner size="lg" />

        <div className="flex flex-col items-center gap-1 text-center">
          <p className="font-nunito text-h2 text-grey-500 font-bold">
            Generating Routes
          </p>
          <p className="text-p1 text-grey-400">
            This may take up to 5 minutes…
          </p>
        </div>

        {/* TODO: replace with ProgressBar component */}
        <div>TODO: replace with ProgressBar component</div>
      </div>
    </Card>
  );
}
