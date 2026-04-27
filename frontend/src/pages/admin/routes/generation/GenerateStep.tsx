import {
  Banner,
  Button,
  Card,
  Progress,
  Spinner,
  StatCard,
} from '@/common/components';
import { Link } from 'react-router-dom';

// TODO: replace with actual values from API
const MOCK_COMPLETED = 1;
const MOCK_TOTAL = 3;
const TOTAL_FAMILIES = 515;
const AVERAGE_STOPS = 12;
const LONGEST_ROUTE = 22;

export function GenerateStep() {
  const percent = Math.round((MOCK_COMPLETED / MOCK_TOTAL) * 100);

  // TODO: replace with actual response from API
  const GENERATION_SUCCESS = true;

  if (GENERATION_SUCCESS) {
    return (
      <div className="flex flex-col gap-8">
        <Banner
          variant="success"
          subtitle="Generated on Oct 20, 2025 at 10:42 AM by Emily"
        >
          Routes generated successfully and auto-saved successfully!
        </Banner>
        <div className="flex gap-8">
          <StatCard
            color="green"
            label="Routes Created"
            value={MOCK_COMPLETED}
            character="granny"
          />
          <StatCard
            color="blue"
            label="Total Families"
            value={TOTAL_FAMILIES}
            character="boy"
          />
          <StatCard
            color="pink"
            label="Average Stops"
            value={AVERAGE_STOPS}
            character="boyPointing"
          />
          <StatCard
            color="orange"
            label="Longest Route"
            value={`${LONGEST_ROUTE} km`}
            character="girlSearching"
          />
        </div>
        <div className="flex justify-end">
          <Button asChild variant="primary">
            <Link to="/admin/routes">View Routes</Link>
          </Button>
        </div>
      </div>
    );
  }

  return (
    <>
      <Card className="flex flex-col gap-6 px-8 pt-6 pb-8">
        {/* Header */}
        <div className="flex flex-col gap-1">
          <h2 className="text-grey-500">Route Generation</h2>
          <p className="font-nunito-sans text-grey-500 text-lg">
            Creating optimized delivery routes.
          </p>
        </div>

        {/* Loading content */}
        <div className="flex flex-col items-center gap-12">
          {/* Spinner + text */}
          <div className="flex flex-col items-center gap-6">
            <Spinner size="lg" />
            <div className="flex flex-col items-center gap-1 text-center">
              <p className="font-nunito-sans text-grey-500 text-base font-bold">
                Generating Routes
              </p>
              <p className="font-nunito-sans text-grey-500 text-base">
                This may take up to 5 minutes...
              </p>
            </div>
          </div>

          {/* Progress */}
          <div className="flex flex-col items-center gap-2">
            <Progress value={percent} className="h-2 w-80" />
            <p className="font-nunito-sans text-grey-500 text-sm">
              {MOCK_COMPLETED}/{MOCK_TOTAL} route groups completed
            </p>
          </div>
        </div>
      </Card>
    </>
  );
}
