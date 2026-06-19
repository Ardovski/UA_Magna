"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { ExportButton } from "./ExportButton";
import { FilterPanel } from "./FilterPanel";
import { RecordsTable } from "./RecordsTable";
import { useRecords } from "./useRecords";
import { queryToFilterState, useRecordsFilterStore } from "@/stores/filters";
import { useT } from "@/lib/i18n";

export function RecordsPage() {
  const t = useT();
  const [page, setPage] = useState(1);
  const [size] = useState(50);
  const filter = useRecordsFilterStore();
  const searchParams = useSearchParams();

  // URL → store hidrasyonu yalnız mount'ta bir kez. `filter`'a bağımlı olmak
  // sonsuz döngü yaratır: hydrate → store değişir → yeni referans → effect → …
  const hydratedRef = useRef(false);
  useEffect(() => {
    if (hydratedRef.current) return;
    hydratedRef.current = true;
    const sp = searchParams ?? new URLSearchParams();
    useRecordsFilterStore.getState().hydrate(queryToFilterState(sp));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // useRecords kendi içinde 300ms debounce yapar → aynı paylaşılan queryKey ile
  // RecordsPage ve RecordsTable çağrıları TanStack Query dedupe edilir.
  const records = useRecords(page, size);

  useEffect(() => {
    if (page === 1) return;
    if (records.data && page > records.data.total_pages) {
      setPage(1);
    }
  }, [records.data, page]);

  // Filter değiştiğinde → sayfa 1'e dön.
  useEffect(() => {
    setPage(1);
  }, [filter]);

  return (
    <main className="container mx-auto space-y-4 py-8">
      <header className="flex items-end justify-between">
        <div>
          <p className="font-mono text-sm text-muted-foreground">
            MAGNA · {t("records.recordsPage.breadcrumb")}
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">
            {t("records.recordsPage.title")}
          </h1>
        </div>
        <ExportButton />
      </header>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[280px_1fr]">
        <FilterPanel />
        <RecordsTable page={page} size={size} onPageChange={setPage} />
      </div>
    </main>
  );
}
