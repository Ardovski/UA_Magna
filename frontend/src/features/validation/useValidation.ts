"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { env } from "@/lib/env";
import { queryKeys } from "@/lib/query-keys";
import type { IssueFilter, RecordDetail, RecordEdit, ValidationIssue, ValidationSummary } from "./types";

export function useIssues(filter: IssueFilter) {
  const p = new URLSearchParams();
  if (filter.category) p.set("category", filter.category);
  if (filter.severity) p.set("severity", filter.severity);
  if (filter.rule_id) p.set("rule_id", filter.rule_id);
  if (filter.record_status) p.set("record_status", filter.record_status);
  const q = p.toString();
  return useQuery({
    queryKey: [...queryKeys.validation.issues(filter), q] as const,
    queryFn: () => api.get<ValidationIssue[]>(`/api/v1/validation/issues${q ? `?${q}` : ""}`),
  });
}

export function useValidationSummary() {
  return useQuery({
    queryKey: queryKeys.validation.summary,
    queryFn: () => api.get<ValidationSummary>("/api/v1/validation/summary"),
  });
}

export function useRecordDetail(recordId: number) {
  return useQuery({
    queryKey: queryKeys.records.detail(recordId),
    queryFn: () => api.get<RecordDetail>(`/api/v1/records/${recordId}`),
    enabled: recordId > 0,
    staleTime: 30_000,
  });
}

export function useRecordEdits(recordId: number) {
  return useQuery({
    queryKey: [...queryKeys.records.detail(recordId), "edits"] as const,
    queryFn: () => api.get<RecordEdit[]>(`/api/v1/validation/records/${recordId}/edits`),
    enabled: recordId > 0,
  });
}

export interface FixPayload {
  patch: Record<string, unknown>;
}

export function useFixRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, patch }: { recordId: number; patch: Record<string, unknown> }) =>
      api.post<{ record_id: number; status: string }>(
        `/api/v1/validation/records/${recordId}/fix`,
        patch,
      ),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.validation.issues({}) });
      qc.invalidateQueries({ queryKey: queryKeys.validation.summary });
      qc.invalidateQueries({ queryKey: queryKeys.records.detail(vars.recordId) });
      qc.invalidateQueries({ queryKey: queryKeys.records.list({}) });
    },
  });
}

export function useRejectRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, reason }: { recordId: number; reason?: string }) =>
      api.post<{ record_id: number; status: string }>(
        `/api/v1/validation/records/${recordId}/reject`,
        { reason: reason ?? null },
      ),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.validation.issues({}) });
      qc.invalidateQueries({ queryKey: queryKeys.validation.summary });
      qc.invalidateQueries({ queryKey: queryKeys.records.detail(vars.recordId) });
      qc.invalidateQueries({ queryKey: queryKeys.records.list({}) });
    },
  });
}

export function useAcceptRecord() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ recordId, reason }: { recordId: number; reason?: string }) =>
      api.post<{ record_id: number; status: string }>(
        `/api/v1/validation/records/${recordId}/accept`,
        { reason: reason ?? null },
      ),
    onSuccess: (_data, vars) => {
      qc.invalidateQueries({ queryKey: queryKeys.validation.issues({}) });
      qc.invalidateQueries({ queryKey: queryKeys.validation.summary });
      qc.invalidateQueries({ queryKey: queryKeys.records.detail(vars.recordId) });
      qc.invalidateQueries({ queryKey: queryKeys.records.list({}) });
    },
  });
}

/** İndirilebilir Excel validation raporu (.xlsx) — blob indirme. */
export function useExportReportXlsx() {
  return useMutation({
    mutationFn: async () => {
      const res = await fetch(`${env.apiUrl}/api/v1/validation/report.xlsx`, { method: "GET" });
      if (!res.ok) throw new Error(`export failed: ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "validation_report.xlsx";
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    },
  });
}

export function useRunValidation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.post<{ record_count: number }>("/api/v1/validation/run"),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: queryKeys.validation.summary });
      qc.invalidateQueries({ queryKey: queryKeys.validation.issues({}) });
      qc.invalidateQueries({ queryKey: queryKeys.records.list({}) });
    },
  });
}
