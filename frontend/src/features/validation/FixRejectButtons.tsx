"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { useT } from "@/lib/i18n";
import { useAcceptRecord, useFixRecord, useRejectRecord } from "./useValidation";

export interface FixRejectButtonsProps {
  recordId: number;
  onAfterAction?: () => void;
}

export function FixRejectButtons({ recordId, onAfterAction }: FixRejectButtonsProps) {
  const t = useT();
  const toast = useToast();
  const fix = useFixRecord();
  const reject = useRejectRecord();
  const accept = useAcceptRecord();
  const [patchJson, setPatchJson] = useState('{"produced_qty": 12}');

  const onFix = () => {
    let patch: Record<string, unknown>;
    try {
      patch = JSON.parse(patchJson) as Record<string, unknown>;
    } catch {
      toast.push({
        tone: "warning",
        title: t("validation.fixRejectButtons.fixInvalidJson"),
        description: t("validation.fixRejectButtons.fixInvalidJsonDesc"),
      });
      return;
    }
    fix.mutate(
      { recordId, patch },
      {
        onSuccess: () => {
          toast.push({
            tone: "success",
            title: t("validation.fixRejectButtons.fixSuccess"),
            description: t("validation.fixRejectButtons.fixSuccessDesc", { id: recordId }),
          });
          onAfterAction?.();
        },
        onError: () =>
          toast.push({
            tone: "destructive",
            title: t("validation.fixRejectButtons.actionFailed"),
            description: t("validation.fixRejectButtons.fixSuccessDesc", { id: recordId }),
          }),
      },
    );
  };

  const onReject = () =>
    reject.mutate(
      { recordId },
      {
        onSuccess: () => {
          toast.push({
            tone: "success",
            title: t("validation.fixRejectButtons.rejectSuccess"),
            description: t("validation.fixRejectButtons.rejectSuccessDesc", { id: recordId }),
          });
          onAfterAction?.();
        },
        onError: () =>
          toast.push({
            tone: "destructive",
            title: t("validation.fixRejectButtons.actionFailed"),
            description: t("validation.fixRejectButtons.rejectSuccessDesc", { id: recordId }),
          }),
      },
    );

  const onAccept = () =>
    accept.mutate(
      { recordId },
      {
        onSuccess: () => {
          toast.push({
            tone: "success",
            title: t("validation.fixRejectButtons.acceptSuccess"),
            description: t("validation.fixRejectButtons.acceptSuccessDesc", { id: recordId }),
          });
          onAfterAction?.();
        },
        onError: () =>
          toast.push({
            tone: "destructive",
            title: t("validation.fixRejectButtons.actionFailed"),
            description: t("validation.fixRejectButtons.acceptSuccessDesc", { id: recordId }),
          }),
      },
    );

  const busy = fix.isPending || reject.isPending || accept.isPending;

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-xs font-medium text-muted-foreground">
          {t("validation.fixRejectButtons.patchLabel")}
        </label>
        <textarea
          value={patchJson}
          onChange={(e) => setPatchJson(e.target.value)}
          className="mt-1 h-24 w-full rounded-md border bg-background p-2 font-mono text-xs"
          spellCheck={false}
        />
        <p className="mt-1 text-xs text-muted-foreground">
          {t("validation.fixRejectButtons.example")} <code>{'{"produced_qty": 12}'}</code>
        </p>
      </div>
      <div className="flex flex-wrap gap-2">
        <Button onClick={onFix} disabled={busy} size="sm">
          {t("validation.fixRejectButtons.fix")}
        </Button>
        <Button onClick={onReject} disabled={busy} size="sm" variant="destructive">
          {t("validation.fixRejectButtons.reject")}
        </Button>
        <Button onClick={onAccept} disabled={busy} size="sm" variant="outline">
          {t("validation.fixRejectButtons.accept")}
        </Button>
      </div>
    </div>
  );
}
