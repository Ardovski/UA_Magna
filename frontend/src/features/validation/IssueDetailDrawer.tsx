"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { useT } from "@/lib/i18n";
import { useRecordEdits } from "./useValidation";
import { IssueDiffEditor } from "./IssueDiffEditor";
import type { ValidationIssue } from "./types";

export interface IssueDetailDrawerProps {
  issue: ValidationIssue | null;
  onClose: () => void;
}

export function IssueDetailDrawer({ issue, onClose }: IssueDetailDrawerProps) {
  const t = useT();
  const edits = useRecordEdits(issue?.record_id ?? 0);
  if (issue === null) return null;
  return (
    // Okunabilirlik: koyu + blur arka plan paneli net ayırır. İçeride etiketler
    // muted, değerler `text-foreground` → düşük kontrast/"belirsiz" görünüm giderildi.
    <div
      className="fixed inset-0 z-40 flex justify-end bg-black/60 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      onClick={onClose}
    >
      <div
        className="flex h-full w-full max-w-2xl flex-col overflow-hidden border-l bg-card text-card-foreground shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between border-b px-4 py-3">
          <div>
            <p className="font-mono text-xs text-muted-foreground">MAGNA</p>
            <h2 className="text-base font-semibold">
              Issue #{issue.id} · Record #{issue.record_id}
            </h2>
          </div>
          <Button variant="ghost" size="sm" onClick={onClose}>
            {t("common.close")}
          </Button>
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto p-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {t("validation.issueDetailDrawer.messageTitle")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-card-foreground">{issue.message}</p>
            </CardContent>
          </Card>

          <IssueDiffEditor issue={issue} onAfterAction={onClose} />

          <Card>
            <CardHeader>
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {t("validation.issueDetailDrawer.auditTrailTitle")}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {edits.isLoading ? (
                <Skeleton className="h-12 w-full" />
              ) : (edits.data ?? []).length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {t("validation.issueDetailDrawer.noEdits")}
                </p>
              ) : (
                <div className="space-y-2">
                  {(edits.data ?? []).map((e) => (
                    <div key={e.id} className="rounded border bg-background p-2 text-xs">
                      <div className="flex justify-between font-medium">
                        <span>{e.reason ?? e.field}</span>
                        <span className="text-muted-foreground">{e.edited_at}</span>
                      </div>
                      <div className="text-muted-foreground">{e.edited_by}</div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
