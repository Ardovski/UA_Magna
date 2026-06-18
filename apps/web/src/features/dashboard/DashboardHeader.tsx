"use client";

import { Activity } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useKpis } from "./useDashboardData";

export function DashboardHeader() {
  const kpis = useKpis();
  const recordCount = kpis.data?.record_count ?? 0;
  const valid = kpis.data?.valid_count ?? 0;
  const suspect = kpis.data?.suspect_count ?? 0;
  const rejected = kpis.data?.rejected_count ?? 0;

  return (
    <header className="space-y-2">
      <div className="flex items-center gap-2 text-muted-foreground">
        <Activity className="h-4 w-4" />
        <p className="font-mono text-xs">MAGNA · Dashboard</p>
      </div>
      <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
        <h1 className="text-3xl font-semibold tracking-tight">Üretim Performansı</h1>
        <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
          {kpis.isLoading ? (
            <Skeleton className="h-4 w-40" />
          ) : (
            <>
              <span>
                <strong className="font-mono text-foreground">{recordCount.toLocaleString("tr-TR")}</strong>{" "}
                kayıt
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-oee-good" />
                <strong className="font-mono text-oee-good">{valid}</strong> geçerli
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-oee-mid" />
                <strong className="font-mono text-oee-mid">{suspect}</strong> şüpheli
              </span>
              <span className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-oee-low" />
                <strong className="font-mono text-oee-low">{rejected}</strong> reddedildi
              </span>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
