"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/services/api";

export function useSessions() {
  return useQuery({
    queryKey: ["sessions"],
    queryFn: api.sessions,
  });
}

export function useCefrLevels() {
  return useQuery({
    queryKey: ["levels"],
    queryFn: api.levels,
    staleTime: Infinity,
  });
}
