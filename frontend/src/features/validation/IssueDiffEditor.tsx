"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Save, ShieldCheck, ShieldX, Wand2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge, severityTone } from "@/components/ui/badge";
import { DiffFieldRow } from "@/components/molecules";
import { useToast } from "@/components/ui/toast";
import { useT } from "@/lib/i18n";
import {
  useAcceptRecord,
  useFixRecord,
  useRecordDetail,
  useRejectRecord,
} from "./useValidation";
import type { ValidationIssue } from "./types";

export interface IssueDiffEditorProps {
  issue: ValidationIssue;
  onAfterAction?: () => void;
}

/** Alan adı → input tipi. Diff editöründe alan-bazlı input render'ı. */
const FIELD_TYPE: Record<string, "text" | "number"> = {
  produced_qty: "number",
  scrap_qty: "number",
  availability: "number",
  performance: "number",
  quality: "number",
  oee: "number",
  run_time: "number",
  down_time: "number",
  planned_down: "number",
  unplanned_down: "number",
  oee_recomputed: "number",
  shift: "number",
};

function parseFieldList(raw: string | null): string[] {
  if (!raw) return [];
  return raw
    .split(/[,\s]+/)
    .map((s) => s.trim())
    .filter(Boolean);
}

function valueAsString(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (typeof v === "number") {
    return Number.isInteger(v) ? String(v) : v.toString();
  }
  return String(v);
}

function castValue(field: string, raw: string): string | number {
  if (FIELD_TYPE[field] === "number") {
    if (raw === "") return raw;
    const n = Number(raw);
    return Number.isFinite(n) ? n : raw;
  }
  return raw;
}

export function IssueDiffEditor({ issue, onAfterAction }: IssueDiffEditorProps) {
  const t = useT();
  const toast = useToast();
  const record = useRecordDetail(issue.record_id);
  const fix = useFixRecord();
  const reject = useRejectRecord();
  const accept = useAcceptRecord();

  const fields = useMemo(() => parseFieldList(issue.fields), [issue.fields]);

  // record'dan gelen alan değerlerinin "orijinal" halleri (sol kolon).
  const initialDraft = useMemo<Record<string, string>>(() => {
    if (!record.data) return {};
    const out: Record<string, string> = {};
    const rec = record.data as unknown as Record<string, unknown>;
    for (const f of fields) {
      out[f] = valueAsString(rec[f]);
    }
    return out;
  }, [record.data, fields]);

  // Operatörün değiştirdiği taslak. `initialDraft` değişirse (record yüklendiğinde
  // veya issue.fields değiştiğinde) taslağı orijinale sıfırla — JSON karşılaştırması
  // ile gereksiz re-render'ı önle.
  const [draft, setDraft] = useState<Record<string, string>>(initialDraft);
  const lastInitialRef = useRef<string>("");
  useEffect(() => {
    const serialized = JSON.stringify(initialDraft);
    if (serialized !== lastInitialRef.current) {
      lastInitialRef.current = serialized;
      setDraft(initialDraft);
    }
  }, [initialDraft]);

  const dirtyFields = useMemo(() => {
    const d: string[] = [];
    for (const f of fields) {
      if ((draft[f] ?? "") !== (initialDraft[f] ?? "")) d.push(f);
    }
    return d;
  }, [draft, initialDraft, fields]);

  const busy = fix.isPending || reject.isPending || accept.isPending;

  const onFix = () => {
    if (dirtyFields.length === 0) {
      toast.push({
        tone: "warning",
        title: t("validation.diffEditor.noChangesTitle"),
        description: t("validation.diffEditor.noChangesDesc"),
      });
      return;
    }
    const patch: Record<string, unknown> = {};
    for (const f of dirtyFields) patch[f] = castValue(f, draft[f] ?? "");
    fix.mutate(
      { recordId: issue.record_id, patch },
      {
        onSuccess: () => {
          toast.push({
            tone: "success",
            title: t("validation.diffEditor.fixSuccess"),
            description: t("validation.diffEditor.fixSuccessDesc", {
              id: issue.record_id,
              n: dirtyFields.length,
            }),
          });
          onAfterAction?.();
        },
        onError: () =>
          toast.push({
            tone: "destructive",
            title: t("validation.diffEditor.actionFailed"),
            description: t("validation.fixRejectButtons.actionFailed"),
          }),
      },
    );
  };

  const onReject = () => {
    reject.mutate(
      { recordId: issue.record_id },
      {
        onSuccess: () => {
          toast.push({
            tone: "success",
            title: t("validation.fixRejectButtons.rejectSuccess"),
            description: t("validation.fixRejectButtons.rejectSuccessDesc", {
              id: issue.record_id,
            }),
          });
          onAfterAction?.();
        },
        onError: () =>
          toast.push({
            tone: "destructive",
            title: t("validation.diffEditor.actionFailed"),
          }),
      },
    );
  };

  const onAccept = () => {
    accept.mutate(
      { recordId: issue.record_id },
      {
        onSuccess: () => {
          toast.push({
            tone: "success",
            title: t("validation.fixRejectButtons.acceptSuccess"),
            description: t("validation.fixRejectButtons.acceptSuccessDesc", {
              id: issue.record_id,
            }),
          });
          onAfterAction?.();
        },
        onError: () =>
          toast.push({
            tone: "destructive",
            title: t("validation.diffEditor.actionFailed"),
          }),
      },
    );
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex flex-wrap items-center gap-2 text-sm">
          <Badge tone={severityTone(issue.severity)}>{t(`severity.${issue.severity}`)}</Badge>
          <span className="font-mono text-xs">{issue.rule_id}</span>
          <Badge tone="outline">{issue.category}</Badge>
          <span className="ml-auto text-xs font-normal text-muted-foreground">
            {t("validation.diffEditor.dirtyCount", {
              n: dirtyFields.length,
              total: fields.length,
            })}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        {record.isLoading ? (
          <div className="space-y-2">
            {Array.from({ length: Math.max(fields.length, 1) }).map((_, i) => (
              <div key={i} className="grid grid-cols-2 gap-3 rounded-md border bg-card p-3">
                <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
                <div className="h-9 w-full animate-pulse rounded-md bg-muted" />
              </div>
            ))}
          </div>
        ) : fields.length === 0 ? (
          <p className="rounded-md border bg-muted/30 p-3 text-xs text-muted-foreground">
            {t("validation.diffEditor.noFields")}
          </p>
        ) : (
          <div className="space-y-2">
            {fields.map((f) => (
              <DiffFieldRow
                key={f}
                field={f}
                currentValue={initialDraft[f] ?? ""}
                newValue={draft[f] ?? ""}
                onChange={(v) => setDraft((prev) => ({ ...prev, [f]: v }))}
                type={FIELD_TYPE[f] ?? "text"}
                dirty={dirtyFields.includes(f)}
              />
            ))}
          </div>
        )}

        <div className="flex flex-wrap gap-2 border-t pt-3">
          <Button
            size="sm"
            onClick={onFix}
            disabled={busy || dirtyFields.length === 0}
          >
            <Save className="mr-1.5 h-3.5 w-3.5" />
            {t("validation.diffEditor.fix")} ({dirtyFields.length})
          </Button>
          <Button size="sm" variant="destructive" onClick={onReject} disabled={busy}>
            <ShieldX className="mr-1.5 h-3.5 w-3.5" />
            {t("validation.fixRejectButtons.reject")}
          </Button>
          <Button size="sm" variant="outline" onClick={onAccept} disabled={busy}>
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5" />
            {t("validation.fixRejectButtons.accept")}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setDraft(initialDraft)}
            disabled={busy || dirtyFields.length === 0}
            className="ml-auto"
          >
            <Wand2 className="mr-1.5 h-3.5 w-3.5" />
            {t("validation.diffEditor.reset")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
