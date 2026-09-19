import { useQuery } from "@tanstack/react-query";

import { api } from "../lib/api";

export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => api("/health", { auth: false }),
    refetchInterval: 60_000,
    retry: false,
    staleTime: 30_000,
  });
}
