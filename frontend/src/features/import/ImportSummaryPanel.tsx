"use client";

import { AlertTriangle, CheckCircle2, FileWarning } from "lucide-react";
import { Badge, severityTone } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";
import type { ImportSummary } from "./types";

function Stat({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: number | string;
  tone?: "default" | "success" | "warning" | "destructive";
}) {
  const toneClass = {
    default: "text-foreground",
    success: "text-success",
    warning: "text-warning",
    destructive: "text-destructive",
  }[tone];
  return (
    <div className="rounded-lg border bg-card p-3">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn("mt-1 text-2xl font-bold tabular-nums", toneClass)}>{value}</p>
    </div>
  );
}

export function ImportSummaryPanel({ summary }: { summary: ImportSummary }) {
  const t = useT();
  const v = summary.validation;
  const rejectedTotal = summary.parse_failed_count + summary.duplicate_row_skipped;

  return (
    <Card data-testid="import-summary">
      <CardHeader className="flex flex-row items-start justify-between gap-2 space-y-0">
        <div>
          <CardTitle className="text-base">{t("import.importSummaryPanel.title")}</CardTitle>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {summary.filename} · {summary.elapsed_ms} ms
          </p>
        </div>
        <Badge tone={summary.status === "duplicate" ? "warning" : "success"}>
          {summary.status === "duplicate"
            ? t("import.importSummaryPanel.duplicateFileBadge")
            : t("import.importSummaryPanel.completedBadge")}
        </Badge>
      </CardHeader>

      <CardContent className="space-y-5">
        {summary.duplicate_file && (
          <div
            role="alert"
            data-testid="import-summary-duplicate-file"
            className="flex items-start gap-2 rounded-md border border-warning/40 bg-warning/10 p-3 text-sm"
          >
            <FileWarning className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <span>
              {t("import.importSummaryPanel.duplicateFileNoticePrefix")}{" "}
              <code>file_hash</code>).{" "}
              {t("import.importSummaryPanel.duplicateFileNoticeSuffix")}
            </span>
          </div>
        )}

        {/* Duplicate satır uyarısı: dosya farklı ama içerik aynı olan satırlar atlandı. */}
        {summary.duplicate_row_skipped > 0 && (
          <div
            role="status"
            data-testid="import-summary-duplicate-rows"
            className="flex items-start gap-2 rounded-md border border-warning/30 bg-warning/5 p-3 text-sm"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <span>
              <strong className="text-warning">
                {t("import.importSummaryPanel.duplicateRowsNoticeTitle")}
              </strong>{" "}
              {t("import.importSummaryPanel.duplicateRowsNoticeDesc", {
                n: summary.duplicate_row_skipped,
              })}
            </span>
          </div>
        )}

        {/* Hiç yeni satır eklenmedi → operatöre net bilgi. */}
        {summary.total_rows > 0 && summary.imported_rows === 0 && (
          <div
            role="alert"
            data-testid="import-summary-no-new"
            className="flex items-start gap-2 rounded-md border border-destructive/40 bg-destructive/10 p-3 text-sm"
          >
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
            <span className="text-destructive">
              {t("import.importSummaryPanel.noNewRecordsTitle")}
            </span>
          </div>
        )}

        {/* İçe aktarma sayıları */}
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Stat label={t("import.importSummaryPanel.totalRows")} value={summary.total_rows} />
          <Stat
            label={t("import.importSummaryPanel.importedRows")}
            value={summary.imported_rows}
            tone="success"
          />
          <Stat
            label={t("import.importSummaryPanel.skippedDuplicateRows")}
            value={summary.duplicate_row_skipped}
            tone={summary.duplicate_row_skipped > 0 ? "warning" : "default"}
          />
          <Stat
            label={t("import.importSummaryPanel.parseErrors")}
            value={summary.parse_failed_count}
            tone={summary.parse_failed_count > 0 ? "destructive" : "default"}
          />
        </div>

        {/* Validasyon (kalite) dökümü */}
        {v ? (
          <div className="space-y-3">
            <p className="text-sm font-medium">{t("import.importSummaryPanel.dataQualityHeading")}</p>
            <div className="grid grid-cols-3 gap-3">
              <Stat label={t("status.valid")} value={v.valid} tone="success" />
              <Stat label={t("status.suspect")} value={v.suspect} tone="warning" />
              <Stat label={t("status.rejected")} value={v.rejected} tone="destructive" />
            </div>

            {v.total_issues > 0 ? (
              <>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {t("import.importSummaryPanel.severityLabel")}
                  </span>
                  {Object.entries(v.by_severity).map(([sev, count]) => (
                    <Badge key={sev} tone={severityTone(sev)}>
                      {t(`severity.${sev}`)}: {count}
                    </Badge>
                  ))}
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-xs text-muted-foreground">
                    {t("import.importSummaryPanel.categoryLabel")}
                  </span>
                  {Object.entries(v.by_category).map(([cat, count]) => (
                    <Badge key={cat} tone="outline">
                      {t(`import.importSummaryPanel.category.${cat}`)}: {count}
                    </Badge>
                  ))}
                </div>
              </>
            ) : (
              <p className="flex items-center gap-1.5 text-sm text-success">
                <CheckCircle2 className="h-4 w-4" /> {t("import.importSummaryPanel.noQualityIssues")}
              </p>
            )}
          </div>
        ) : (
          summary.imported_rows === 0 && (
            <p className="text-sm text-muted-foreground">
              {t("import.importSummaryPanel.noNewRecordsValidation")}
            </p>
          )
        )}

        {/* Reddedilen/parse hatası örnekleri + sebep */}
        {summary.failed_rows_sample.length > 0 && (
          <div className="space-y-2">
            <p className="flex items-center gap-1.5 text-sm font-medium">
              <AlertTriangle className="h-4 w-4 text-destructive" />
              {t("import.importSummaryPanel.rejectedRowSamplesHeading")}
            </p>
            <div className="overflow-hidden rounded-lg border">
              <table className="w-full text-left text-xs">
                <thead className="bg-muted/50 text-muted-foreground">
                  <tr>
                    <th className="px-3 py-2 font-medium">
                      {t("import.importSummaryPanel.reasonColumn")}
                    </th>
                    <th className="px-3 py-2 font-medium">
                      {t("import.importSummaryPanel.rowSummaryColumn")}
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {summary.failed_rows_sample.map((f, i) => (
                    <tr key={i} className="border-t align-top">
                      <td className="px-3 py-2 text-destructive">
                        {f.reason ?? t("import.importSummaryPanel.parseErrorFallback")}
                      </td>
                      <td className="px-3 py-2 font-mono text-muted-foreground">
                        {f.row
                          ? Object.entries(f.row)
                              .slice(0, 4)
                              .map(([k, val]) => `${k}=${val}`)
                              .join(" · ")
                          : t("common.none")}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Reddedilen toplamı not */}
        {rejectedTotal > 0 && (
          <p className="text-xs text-muted-foreground">
            {t("import.importSummaryPanel.rejectedTotalNote", {
              total: rejectedTotal,
              parseFailed: summary.parse_failed_count,
              duplicate: summary.duplicate_row_skipped,
            })}
          </p>
        )}
      </CardContent>
    </Card>
  );
}
