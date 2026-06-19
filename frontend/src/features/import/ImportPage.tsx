"use client";

import { useEffect, useRef, useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { useToast } from "@/components/ui/toast";
import { useT } from "@/lib/i18n";
import { BatchSelector } from "./BatchSelector";
import { ImportDropzone } from "./ImportDropzone";
import { ImportPreviewPanel } from "./ImportPreviewPanel";
import { ImportProgress } from "./ImportProgress";
import { ImportSummaryPanel } from "./ImportSummaryPanel";
import { mergeSummaries } from "./mergeSummaries";
import type { ImportPreview, ImportSummary } from "./types";
import { useActivateBatch, useActiveBatch, useImportCsv, useImportPreview } from "./useBatch";

type Phase = "idle" | "previewing" | "preview" | "importing" | "done";

export function ImportPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();
  const active = useActiveBatch();
  const activate = useActivateBatch();
  const toast = useToast();
  const t = useT();
  const hydratedRef = useRef(false);

  const previewMut = useImportPreview();
  const importMut = useImportCsv();

  const [phase, setPhase] = useState<Phase>("idle");
  const [files, setFiles] = useState<File[]>([]);
  const [preview, setPreview] = useState<ImportPreview | null>(null);
  const [progress, setProgress] = useState(0);
  const [current, setCurrent] = useState<string>("");
  const [summary, setSummary] = useState<ImportSummary | null>(null);

  // Aktif batch'i URL'den hidrat et (sayfa açılışında)
  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    const urlId = searchParams?.get("batch_id");
    if (!urlId) return;
    const numId = Number(urlId);
    if (!Number.isFinite(numId)) return;
    if (active.data && active.data.id === numId) return;
    activate.mutate(numId);
  }, [active.data, searchParams, activate]);

  // Aktif batch'i URL ile senkron tut
  useEffect(() => {
    const urlId = searchParams?.get("batch_id") ?? null;
    const activeId = active.data?.id != null ? String(active.data.id) : null;
    if (urlId === activeId) return;
    const url = activeId ? `${pathname}?batch_id=${activeId}` : pathname;
    router.replace(url, { scroll: false });
  }, [active.data, pathname, router, searchParams]);

  function reset() {
    setPhase("idle");
    setFiles([]);
    setPreview(null);
    setSummary(null);
    setProgress(0);
    setCurrent("");
  }

  async function handleFiles(selected: File[]) {
    const csvs = selected.filter((f) => f.name.toLowerCase().endsWith(".csv"));
    if (!csvs.length) {
      toast.push({ tone: "warning", title: t("import.importPage.onlyCsvSupported") });
      return;
    }
    setFiles(csvs);
    setPhase("previewing");
    toast.push({ tone: "default", title: t("import.toast.previewing") });
    try {
      const pv = await previewMut.mutateAsync(csvs[0]);
      setPreview(pv);
      setPhase("preview");

      // 0 kolon veya 0 satır → operatöre açık uyarı (panelde de banner var, toast
      // ile birlikte "kaçırma riski" sıfıra iner).
      if (pv.detected_columns.length === 0) {
        toast.push({
          tone: "destructive",
          title: t("import.toast.previewNoColumnsTitle"),
          description: t("import.toast.previewNoColumnsDesc"),
        });
      } else if (pv.total_rows === 0) {
        toast.push({
          tone: "warning",
          title: t("import.toast.previewNoRowsTitle"),
          description: t("import.toast.previewNoRowsDesc"),
        });
      } else {
        toast.push({
          tone: "success",
          title:
            csvs.length > 1
              ? t("import.toast.previewReadyMulti", {
                  files: csvs.length,
                  rows: pv.total_rows,
                })
              : t("import.toast.previewReady", {
                  rows: pv.total_rows,
                  cols: pv.detected_columns.length,
                }),
        });
      }
    } catch {
      toast.push({ tone: "destructive", title: t("import.importPage.previewFailed") });
      reset();
    }
  }

  async function confirmImport() {
    if (!files.length) return;
    setPhase("importing");
    toast.push({ tone: "default", title: t("import.toast.importing") });
    const results: ImportSummary[] = [];
    try {
      for (const file of files) {
        setCurrent(file.name);
        setProgress(0);
        const s = await importMut.mutateAsync({ file, onProgress: setProgress });
        setProgress(100);
        results.push(s);
      }
    } catch {
      toast.push({ tone: "destructive", title: t("import.importPage.importFailed") });
      reset();
      return;
    }
    const combined = results.length === 1 ? results[0] : mergeSummaries(results);
    // Son içe aktarılan batch'i aktif yap (dashboard/sync onu görsün)
    const lastId = results[results.length - 1]?.batch_id;
    if (lastId != null) await activate.mutateAsync(lastId);
    setSummary(combined);
    setPhase("done");

    // 1) Duplicate dosya: aynı file_hash DB'de zaten var → operatöre net uyarı.
    if (combined.duplicate_file) {
      toast.push({
        tone: "warning",
        title: t("import.toast.duplicateFileTitle"),
        description: t("import.toast.duplicateFileDesc", {
          skipped: combined.duplicate_row_skipped,
          imported: combined.imported_rows,
        }),
      });
    }
    // 2) Duplicate satırlar (farklı dosya ama aynı satır içeriği) → info.
    else if (combined.duplicate_row_skipped > 0) {
      toast.push({
        tone: "default",
        title: t("import.toast.duplicateRowsTitle"),
        description: t("import.toast.duplicateRowsDesc", {
          skipped: combined.duplicate_row_skipped,
        }),
      });
    }
    // 3) Hiç satır eklenmedi (duplicate veya boş) → warning.
    if (combined.imported_rows === 0 && combined.total_rows > 0) {
      toast.push({
        tone: "warning",
        title: t("import.toast.noNewRowsTitle"),
        description: t("import.toast.noNewRowsDesc", {
          total: combined.total_rows,
          skipped: combined.duplicate_row_skipped,
        }),
      });
    } else if (!combined.duplicate_file) {
      toast.push({
        tone: "success",
        title: t("import.toast.importSuccess"),
        description: t("import.toast.importSuccessDesc", {
          imported: combined.imported_rows,
          rejected: combined.parse_failed_count + (combined.duplicate_row_skipped ?? 0),
        }),
      });
    }
  }

  return (
    <main className="container mx-auto space-y-4 py-8">
      <header className="flex flex-col items-start gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="font-mono text-sm text-muted-foreground">MAGNA · Import</p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">{t("import.importPage.title")}</h1>
        </div>
        <BatchSelector />
      </header>

      {phase === "idle" && <ImportDropzone onFiles={handleFiles} />}

      {phase === "previewing" && (
        <ImportProgress value={0} filename={files[0]?.name} />
      )}

      {phase === "preview" && preview && (
        <div className="space-y-3">
          {files.length > 1 && (
            <p className="rounded-md border bg-muted/40 px-3 py-2 text-sm">
              <strong>{t("import.importPage.multiFileCount", { n: files.length })}</strong>{" "}
              {t("import.importPage.multiFileNoteBefore")}
              (<span className="font-mono">{files[0].name}</span>)
              {t("import.importPage.multiFileNoteAfter")}
            </p>
          )}
          <ImportPreviewPanel
            preview={preview}
            onConfirm={confirmImport}
            onCancel={reset}
          />
        </div>
      )}

      {phase === "importing" && <ImportProgress value={progress} filename={current} />}

      {phase === "done" && summary && (
        <div className="space-y-3">
          <ImportSummaryPanel summary={summary} />
          <Button variant="outline" size="sm" onClick={reset}>
            {t("import.importPage.newImport")}
          </Button>
        </div>
      )}
    </main>
  );
}
