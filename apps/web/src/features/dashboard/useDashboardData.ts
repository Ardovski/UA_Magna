"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { queryKeys } from "@/lib/query-keys";
import type {
  KpiCards,
  OeeTrendPoint,
  ProblemShiftRow,
  QualityDistributionBucket,
  RecentRecordRow,
  ShiftComparisonRow,
  StationRankingRow,
  TopStationRow,
} from "./types";

export function useKpis() {
  return useQuery({
    queryKey: queryKeys.analytics.kpis(),
    queryFn: () => api.get<KpiCards>("/api/v1/analytics/kpis"),
  });
}

export function useKpisPeriod(start: string | null, end: string | null) {
  const q = new URLSearchParams();
  if (start) q.set("start", start);
  if (end) q.set("end", end);
  const qs = q.toString();
  return useQuery({
    queryKey: ["analytics", "kpis", "period", start, end] as const,
    queryFn: () =>
      api.get<KpiCards>(`/api/v1/analytics/kpis${qs ? `?${qs}` : ""}`),
  });
}

export function useOeeTrend(days: number = 21) {
  return useQuery({
    queryKey: [...queryKeys.analytics.oeeTrend(null), days] as const,
    queryFn: () => api.get<OeeTrendPoint[]>(`/api/v1/analytics/oee-trend?days=${days}`),
  });
}

export function useShiftComparison() {
  return useQuery({
    queryKey: queryKeys.analytics.shiftComparison(null),
    queryFn: () => api.get<ShiftComparisonRow[]>("/api/v1/analytics/shift-comparison"),
  });
}

export function useStationRanking(limit: number = 10) {
  return useQuery({
    queryKey: [...queryKeys.analytics.stationRanking(null), limit] as const,
    queryFn: () =>
      api.get<StationRankingRow[]>(`/api/v1/analytics/station-ranking?limit=${limit}`),
  });
}

export function useQualityDistribution() {
  return useQuery({
    queryKey: queryKeys.analytics.qualityDistribution(null),
    queryFn: () => api.get<QualityDistributionBucket[]>("/api/v1/analytics/quality-distribution"),
  });
}

export function useRecentRecords(batchId: number | null, limit: number = 20) {
  const q = new URLSearchParams();
  if (batchId !== null) q.set("batch_id", String(batchId));
  q.set("limit", String(limit));
  return useQuery({
    queryKey: queryKeys.analytics.recentRecords(batchId),
    queryFn: () => api.get<RecentRecordRow[]>(`/api/v1/analytics/recent-records?${q.toString()}`),
  });
}

export function useTopStations(batchId: number | null, limit: number = 10) {
  const q = new URLSearchParams();
  if (batchId !== null) q.set("batch_id", String(batchId));
  q.set("limit", String(limit));
  return useQuery({
    queryKey: queryKeys.analytics.topStations(batchId),
    queryFn: () => api.get<TopStationRow[]>(`/api/v1/analytics/top-stations?${q.toString()}`),
  });
}

export function useProblemShifts(batchId: number | null, limit: number = 20) {
  const q = new URLSearchParams();
  if (batchId !== null) q.set("batch_id", String(batchId));
  q.set("limit", String(limit));
  return useQuery({
    queryKey: queryKeys.analytics.problemShifts(batchId),
    queryFn: () => api.get<ProblemShiftRow[]>(`/api/v1/analytics/problem-shifts?${q.toString()}`),
  });
}
