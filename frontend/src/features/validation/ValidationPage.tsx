"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { useT } from "@/lib/i18n";
import { IssueDetailDrawer } from "./IssueDetailDrawer";
import { IssueList } from "./IssueList";
import { useExportReportXlsx, useRunValidation, useValidationSummary } from "./useValidation";
import type { ValidationIssue } from "./types";

export function ValidationPage() {
  const [tab, setTab] = useState("all");
  const [selected, setSelected] = useState<ValidationIssue | null>(null);
  const summary = useValidationSummary();
  const run = useRunValidation();
  const exportXlsx = useExportReportXlsx();
  const toast = useToast();
  const t = useT();

  const onExport = () => {
    toast.push({ tone: "default", title: t("validation.validationPage.exportStarted") });
    exportXlsx.mutate(undefined, {
      onSuccess: () =>
        toast.push({
          tone: "success",
          title: t("validation.validationPage.exportSuccess"),
        }),
      onError: () =>
        toast.push({ tone: "destructive", title: t("validation.validationPage.exportError") }),
    });
  };

  const onRun = () => {
    run.mutate(undefined, {
      onSuccess: (d) => {
        toast.push({
          tone: "success",
          title: t("validation.validationPage.runSuccessTitle"),
          description: t("validation.validationPage.runSuccessDescription", {
            n: d.record_count,
          }),
        });
      },
      onError: () =>
        toast.push({
          tone: "destructive",
          title: t("validation.validationPage.runErrorTitle"),
        }),
    });
  };

  return (
    <main className="container mx-auto space-y-4 py-8">
      <header className="flex items-end justify-between">
        <div>
          <p className="font-mono text-sm text-muted-foreground">MAGNA · {t("validation.validationPage.subtitle")}</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">{t("validation.validationPage.title")}</h1>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={onExport} disabled={exportXlsx.isPending}>
            {exportXlsx.isPending
              ? t("validation.validationPage.exporting")
              : t("validation.validationPage.exportXlsx")}
          </Button>
          <Button onClick={onRun} disabled={run.isPending}>
            {run.isPending ? t("validation.validationPage.running") : t("validation.validationPage.runAll")}
          </Button>
        </div>
      </header>

      <section className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <SummaryCard
          label={t("validation.validationPage.summaryTotal")}
          value={summary.data?.total_records ?? null}
          tone="default"
          loading={summary.isLoading}
        />
        <SummaryCard
          label={t("status.valid")}
          value={summary.data?.by_status?.valid ?? null}
          tone="success"
          loading={summary.isLoading}
        />
        <SummaryCard
          label={t("status.suspect")}
          value={summary.data?.by_status?.suspect ?? null}
          tone="warning"
          loading={summary.isLoading}
        />
        <SummaryCard
          label={t("status.rejected")}
          value={summary.data?.by_status?.rejected ?? null}
          tone="destructive"
          loading={summary.isLoading}
        />
      </section>

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="all">{t("common.all")}</TabsTrigger>
          <TabsTrigger value="suspect">{t("status.suspect")}</TabsTrigger>
          <TabsTrigger value="rejected">{t("status.rejected")}</TabsTrigger>
        </TabsList>
        <TabsContent value="all">
          <IssueList onSelect={setSelected} />
        </TabsContent>
        <TabsContent value="suspect">
          <IssueList recordStatus="suspect" onSelect={setSelected} />
        </TabsContent>
        <TabsContent value="rejected">
          <IssueList recordStatus="rejected" onSelect={setSelected} />
        </TabsContent>
      </Tabs>

      <IssueDetailDrawer issue={selected} onClose={() => setSelected(null)} />
    </main>
  );
}

function SummaryCard({
  label,
  value,
  tone,
  loading,
}: {
  label: string;
  value: number | null;
  tone: "default" | "success" | "warning" | "destructive";
  loading?: boolean;
}) {
  const toneText: Record<typeof tone, string> = {
    default: "text-foreground",
    success: "text-oee-good",
    warning: "text-oee-mid",
    destructive: "text-oee-low",
  };
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">{label}</CardTitle>
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-7 w-20" />
        ) : (
          <p className={`text-2xl font-semibold tabular-nums ${toneText[tone]}`}>
            {value ?? 0}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
