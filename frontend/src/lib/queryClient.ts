import { QueryClient } from '@tanstack/react-query';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes — data stays fresh before refetching
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

export default queryClient;
