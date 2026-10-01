/** React Query defaults: retry transport errors twice, never retry 4xx (they won't change). */
import { QueryClient } from '@tanstack/react-query';

import { ApiError } from './client';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: (count, error) => {
        if (error instanceof ApiError && error.status !== null && error.status < 500) return false;
        return count < 2;
      },
    },
    mutations: { retry: false },
  },
});
