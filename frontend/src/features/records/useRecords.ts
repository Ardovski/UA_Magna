"use client";

import { useEffect, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { env } from "@/lib/env";
import { queryKeys } from "@/lib/query-keys";
import {
  filterStateToQuery,
  useRecordsFilterStore,
  type RecordsFilterState,
} from "@/stores/filters";
import type { FilterOptions, PaginatedRecords } from "./types";

/**
 * `useRecordsFilterStore` üzerindeki her değişimi (slider onCommit, text input
 * keystroke, checkbox toggle, vs.) `debounceMs` boyunca toplar ve tek bir
 * stable filter snapshot'ı döner. Hook içinde kullanıldığı için tüm
 * `useRecords` çağıranları aynı paylaşılan queryKey'e sahip olur → TanStack
 * Query dedupe ile slider sürükleme boyunca **0 istek**, bırakınca **1 istek**.
 */
function useDebouncedFilter(filter: RecordsFilterState, ms: number): RecordsFilterState {
  const [debounced, setDebounced] = useState<RecordsFilterState>(filter);
  useEffect(() => {
    const id = setTimeout(() => setDebounced(filter), ms);
    return () => clearTimeout(id);
  }, [filter, ms]);
  return debounced;
}

export function useRecords(page: number, size: number, sort?: string, debounceMs = 300) {
  const filter = useRecordsFilterStore();
  const stable = useDebouncedFilter(filter, debounceMs);
  const q = filterStateToQuery(stable);
  const sortParam = sort ? `&sort=${encodeURIComponent(sort)}` : "";
  return useQuery({
    queryKey: [...queryKeys.records.list(stable), page, size, sort ?? null] as const,
    queryFn: () =>
      api.get<PaginatedRecords>(`/api/v1/records/list?${q}${sortParam}&page=${page}&size=${size}`),
    placeholderData: (prev) => prev,
    staleTime: 30_000,
  });
}

export function useFilterOptions() {
  return useQuery({
    queryKey: ["records", "filter-options"] as const,
    queryFn: () => api.get<FilterOptions>("/api/v1/analytics/filter-options"),
    staleTime: 5 * 60_000,
  });
}

export function useExportCsv(debounceMs = 300) {
  const filter = useRecordsFilterStore();
  const stable = useDebouncedFilter(filter, debounceMs);
  return useMutation({
    mutationFn: async () => {
      const q = filterStateToQuery(stable);
      const res = await fetch(`${env.apiUrl}/api/v1/records/export?${q}`, { method: "GET" });
      if (!res.ok) throw new Error(`export failed: ${res.status}`);
      const blob = await res.blob();
      const cd = res.headers.get("Content-Disposition") ?? "";
      const m = cd.match(/filename="?([^";]+)"?/);
      const filename = m?.[1] ?? `records_${Date.now()}.csv`;
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
  });
}
