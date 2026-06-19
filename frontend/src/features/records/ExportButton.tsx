"use client";

import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { useT } from "@/lib/i18n";
import { useExportCsv } from "./useRecords";

export function ExportButton() {
  const exp = useExportCsv();
  const toast = useToast();
  const t = useT();
  return (
    <Button
      variant="outline"
      size="sm"
      disabled={exp.isPending}
      onClick={() => {
        toast.push({ tone: "default", title: t("records.toast.exportStarted") });
        exp.mutate(undefined, {
          onSuccess: () =>
            toast.push({
              tone: "success",
              title: t("records.toast.exportSuccess"),
            }),
          onError: () =>
            toast.push({
              tone: "destructive",
              title: t("records.toast.exportFailed"),
            }),
        });
      }}
    >
      {exp.isPending
        ? t("records.exportButton.downloading")
        : t("records.exportButton.download")}
    </Button>
  );
}
