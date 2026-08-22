import { useMutation, useQueries } from '@tanstack/react-query';

import {
  getJobOptions,
  getJobQueryKey,
} from './generated/@tanstack/react-query.gen';
import { cancelJob, generateJob } from './generated/sdk.gen';
import type { RouteGenerationGroupInput } from './generated/types.gen';

const TERMINAL_JOB_STATES = new Set(['Cancelled', 'Completed', 'Failed']);

export function useStartGenerationJobs() {
  return useMutation({
    mutationFn: async (inputs: RouteGenerationGroupInput[]) => {
      const results = await Promise.allSettled(
        inputs.map(async (body) => {
          const { data } = await generateJob({ body, throwOnError: true });
          return data.job_id;
        })
      );
      const jobIds = results.flatMap((result) =>
        result.status === 'fulfilled' ? [result.value] : []
      );
      const failed = results.find((result) => result.status === 'rejected');

      if (failed) {
        await Promise.allSettled(
          jobIds.map((jobId) =>
            cancelJob({ path: { job_id: jobId }, throwOnError: true })
          )
        );
        throw failed.reason;
      }

      return jobIds;
    },
  });
}

export function useGenerationJobs(jobIds: string[]) {
  return useQueries({
    queries: jobIds.map((jobId) => ({
      ...getJobOptions({ path: { job_id: jobId } }),
      refetchInterval: (query: { state: { data?: { progress?: string } } }) =>
        query.state.data?.progress &&
        TERMINAL_JOB_STATES.has(query.state.data.progress)
          ? false
          : 1500,
    })),
  });
}

export function useCancelGenerationJobs() {
  return useMutation({
    mutationFn: async (jobIds: string[]) =>
      Promise.all(
        jobIds.map(async (jobId) => {
          const { data } = await cancelJob({
            path: { job_id: jobId },
            throwOnError: true,
          });
          return data;
        })
      ),
    onSuccess: (_jobs, jobIds, _context, { client }) =>
      Promise.all(
        jobIds.map((jobId) =>
          client.invalidateQueries({
            queryKey: getJobQueryKey({ path: { job_id: jobId } }),
          })
        )
      ),
  });
}
