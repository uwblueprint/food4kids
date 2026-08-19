import { MutationCache, QueryCache, QueryClient } from '@tanstack/react-query';

import { reportError } from '@/lib/telemetry';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => reportError(error, 'query'),
  }),
  mutationCache: new MutationCache({
    onError: (error) => reportError(error, 'mutation'),
  }),
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes — data stays fresh before refetching
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default queryClient;
