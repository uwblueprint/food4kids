import { useEffect, useMemo, useRef, useState } from 'react';
import {
  Link,
  Navigate,
  useNavigate,
  useOutletContext,
} from 'react-router-dom';

import {
  describeApiFailure,
  useCancelGenerationJobs,
  useGenerationJobs,
  useStartGenerationJobs,
} from '@/api';
import type { JobRead } from '@/api/generated/types.gen';
import girlCatching from '@/assets/illustrations/girl-catching.png';
import {
  Banner,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Modal,
  ModalContent,
  ModalDescription,
  ModalFooter,
  ModalHeader,
  ModalTitle,
  Spinner,
  StatisticsCard,
} from '@/common/components';
import { parseDateOnly } from '@/common/utils';

import type { GenerationOutletContext } from './AdminRoutesGenerationLayout';
import { GenerationFooter } from './GenerationFooter';

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'] as const;
const BAR_COLORS = [
  'bg-blue-300',
  'bg-brand-pink',
  'bg-brand-orange',
  'bg-brand-green',
  'bg-brand-light-blue',
  'bg-brand-pink',
  'bg-brand-orange',
] as const;

function getWeekday(dateTime: string): (typeof WEEKDAYS)[number] {
  return parseDateOnly(dateTime).toLocaleDateString('en-US', {
    weekday: 'short',
  }) as (typeof WEEKDAYS)[number];
}

function formatDistance(distance: number): string {
  const rounded = Math.round(distance * 10) / 10;
  return `${rounded.toLocaleString()} km`;
}

interface SummaryProps {
  jobs: JobRead[];
  inputs: GenerationOutletContext['routeGenerationInputs'];
}

function GenerationSummary({ jobs, inputs }: SummaryProps) {
  const routesByDay = new Map<(typeof WEEKDAYS)[number], number>();

  jobs.forEach((job, index) => {
    const input = inputs[index];
    if (!input) return;
    const weekday = getWeekday(input.settings.route_start_time);
    routesByDay.set(
      weekday,
      (routesByDay.get(weekday) ?? 0) +
        (job.routes_created ?? input.settings.num_routes)
    );
  });

  const visibleWeekdays = WEEKDAYS.filter(
    (weekday) =>
      WEEKDAYS.indexOf(weekday) < 5 || (routesByDay.get(weekday) ?? 0) > 0
  );
  const maxDayCount = Math.max(
    1,
    ...visibleWeekdays.map((weekday) => routesByDay.get(weekday) ?? 0)
  );
  const routesCreated = jobs.reduce(
    (total, job) => total + (job.routes_created ?? 0),
    0
  );
  const totalStops = jobs.reduce(
    (total, job) => total + (job.total_stops ?? 0),
    0
  );
  const totalDistance = jobs.reduce(
    (total, job) => total + (job.total_distance_km ?? 0),
    0
  );
  const totalFamilies = jobs.reduce(
    (total, job) => total + (job.total_families ?? 0),
    0
  );

  return (
    <section className="flex flex-col gap-6">
      <div className="flex flex-col gap-1">
        <h2 className="text-grey-500">Routes Generated Successfully</h2>
        <p className="text-p1 text-grey-500">
          Your optimized delivery routes are ready!
        </p>
      </div>

      <div className="desktop:grid-cols-[minmax(0,1fr)_272px] grid gap-6">
        <Card className="min-h-112">
          <CardHeader>
            <CardTitle>Route Count by Day</CardTitle>
          </CardHeader>
          <CardContent
            className="grid flex-1 gap-5 pt-3"
            style={{
              gridTemplateColumns: `repeat(${visibleWeekdays.length}, minmax(0, 1fr))`,
            }}
          >
            {visibleWeekdays.map((weekday, index) => {
              const count = routesByDay.get(weekday) ?? 0;
              return (
                <div
                  key={weekday}
                  className="flex min-w-0 flex-col items-center justify-end"
                >
                  <div className="flex h-71 w-full items-end justify-center">
                    {count > 0 && (
                      <div
                        className={`${BAR_COLORS[index]} w-full max-w-40 rounded-t-lg`}
                        style={{
                          height: `${Math.max(18, (count / maxDayCount) * 100)}%`,
                        }}
                      />
                    )}
                  </div>
                  <p className="text-h2 mt-2 font-bold text-blue-300">
                    {count}
                  </p>
                  <p className="text-p1 text-grey-400 mt-1">{weekday}</p>
                </div>
              );
            })}
          </CardContent>
        </Card>

        <div className="grid content-start gap-4">
          <StatisticsCard
            color="green"
            label="Routes Created"
            value={routesCreated}
            character="granny"
          />
          <StatisticsCard
            color="blue"
            label="Total Stops"
            value={totalStops}
            character="boy"
          />
          <StatisticsCard
            color="pink"
            label="Total Distance"
            value={formatDistance(totalDistance)}
            character="boyPointing"
          />
          <StatisticsCard
            color="orange"
            label="Total Families"
            value={totalFamilies}
            character="girlSearching"
          />
        </div>
      </div>
    </section>
  );
}

export function GenerateStep() {
  const navigate = useNavigate();
  const context = useOutletContext<GenerationOutletContext>();
  const { file, routeGenerationInputs } = context;
  const [jobIds, setJobIds] = useState<string[]>([]);
  const [cancelOpen, setCancelOpen] = useState(false);
  const generationStarted = useRef(false);
  const startGeneration = useStartGenerationJobs();
  const cancelGeneration = useCancelGenerationJobs();
  const jobQueries = useGenerationJobs(jobIds);

  useEffect(() => {
    if (generationStarted.current || routeGenerationInputs.length === 0) return;
    generationStarted.current = true;
    void startGeneration
      .mutateAsync(routeGenerationInputs)
      .then(setJobIds)
      .catch(() => undefined);
  }, [routeGenerationInputs, startGeneration]);

  const jobs = useMemo(
    () =>
      jobQueries
        .map((query) => query.data)
        .filter((job): job is JobRead => job !== undefined),
    [jobQueries]
  );
  const completedCount = jobs.filter(
    (job) => job.progress === 'Completed'
  ).length;
  const failedJob = jobs.find((job) => job.progress === 'Failed');
  const cancelledJob = jobs.find((job) => job.progress === 'Cancelled');
  const pollingError = jobQueries.find((query) => query.isError)?.error;
  const allCompleted =
    jobIds.length === routeGenerationInputs.length &&
    completedCount === routeGenerationInputs.length;

  // The frames tick "Generate Routes" off on the summary; the stepper can't
  // tell that the step it is sitting on has finished, so tell it.
  const { setCurrentStepComplete } = context;
  useEffect(() => {
    setCurrentStepComplete(allCompleted);
    return () => setCurrentStepComplete(false);
  }, [allCompleted, setCurrentStepComplete]);
  const errorMessage = startGeneration.error
    ? (describeApiFailure(startGeneration.error) ??
      'Route generation could not be started. Please review your route settings and try again.')
    : pollingError
      ? (describeApiFailure(pollingError) ??
        'Route generation status could not be loaded. Please try again.')
      : failedJob
        ? (failedJob.error_message ??
          'A route group could not be generated. Please return to the previous step and try again.')
        : cancelledJob
          ? 'Route generation was cancelled. Return to the previous step to configure and try again.'
          : null;

  if (!file || routeGenerationInputs.length === 0) {
    return <Navigate to="/admin/routes/generation/import" replace />;
  }

  const handleCancel = async () => {
    try {
      await cancelGeneration.mutateAsync(
        jobIds.filter((jobId) => {
          const job = jobs.find((candidate) => candidate.job_id === jobId);
          return (
            !job ||
            (job.progress !== 'Completed' &&
              job.progress !== 'Cancelled' &&
              job.progress !== 'Failed')
          );
        })
      );
      setCancelOpen(false);
      navigate('/admin/routes/generation/configure');
    } catch {
      // The mutation error is rendered in the modal so the admin can retry.
    }
  };

  return (
    <>
      {allCompleted ? (
        <GenerationSummary jobs={jobs} inputs={routeGenerationInputs} />
      ) : (
        // The frame stacks this card top-down — header, 16, illustration, 16,
        // then the two status lines 8 apart — inside 32 across, 24 above and 40
        // below. Its copy differs from ours deliberately: that frame still
        // carries the validation wording.
        <Card className="px-8 pt-6 pb-10">
          <CardHeader className="gap-1">
            <CardTitle>Route Generation</CardTitle>
            <CardDescription>
              Creating optimized delivery routes.
            </CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col items-center gap-4 pt-4">
            {errorMessage ? (
              <Banner variant="error" className="w-full max-w-2xl">
                {errorMessage}
              </Banner>
            ) : (
              <>
                <img
                  src={girlCatching}
                  alt=""
                  aria-hidden
                  className="size-58 object-contain"
                />
                {/* The frame has no progress bar: the count line and the
                    spinner carry the progress on their own, 8 apart. */}
                <div className="flex flex-col items-center gap-2">
                  <p className="text-p2 text-grey-400">
                    {completedCount} / {routeGenerationInputs.length} route
                    groups completed
                  </p>
                  <div
                    className="text-p2 flex items-center gap-2 text-blue-300"
                    role="status"
                    aria-live="polite"
                  >
                    <Spinner size="xs" />
                    <span>Generating routes...</span>
                  </div>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      )}

      <GenerationFooter>
        {!allCompleted && (
          <Button
            variant="tertiary"
            disabled={startGeneration.isPending}
            onClick={() =>
              jobIds.length > 0
                ? setCancelOpen(true)
                : navigate('/admin/routes/generation/configure')
            }
          >
            Back to configure routes
          </Button>
        )}
        {allCompleted ? (
          <Button asChild variant="primary">
            <Link to="/admin/routes">View routes</Link>
          </Button>
        ) : (
          <Button variant="primary" disabled>
            View routes
          </Button>
        )}
      </GenerationFooter>

      <Modal open={cancelOpen} onOpenChange={setCancelOpen}>
        <ModalContent showCloseButton={false}>
          <ModalHeader>
            {/* 20/28 per the frame; ModalTitle's shared default is the 32/44 h1. */}
            <ModalTitle variant="confirmation">
              Cancel Route Generation
            </ModalTitle>
            <ModalDescription>
              If you go back to{' '}
              <span className="text-blue-300">Configure Routes</span> now, the
              current route generation will be cancelled and progress will be
              lost. Do you still want to continue?
            </ModalDescription>
          </ModalHeader>
          {cancelGeneration.isError && (
            <Banner variant="error">
              {describeApiFailure(cancelGeneration.error) ??
                'Route generation could not be cancelled. Please try again.'}
            </Banner>
          )}
          <ModalFooter className="justify-end">
            <Button
              variant="secondary"
              disabled={cancelGeneration.isPending}
              onClick={() => setCancelOpen(false)}
            >
              Keep generating
            </Button>
            <Button
              variant="primary"
              disabled={cancelGeneration.isPending}
              onClick={() => void handleCancel()}
            >
              {cancelGeneration.isPending
                ? 'Cancelling...'
                : 'Cancel route generation'}
            </Button>
          </ModalFooter>
        </ModalContent>
      </Modal>
    </>
  );
}
