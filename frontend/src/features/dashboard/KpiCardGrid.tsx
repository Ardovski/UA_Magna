"use client";

import { memo } from "react";
import { AlertTriangle, Clock, Gauge, Package } from "lucide-react";
import { format, subDays } from "date-fns";
import { useQueries } from "@tanstack/react-query";
import { SummaryCard, oeeTone, type SummaryTrend, type TrendDirection } from "@/components/molecules";
import { api } from "@/lib/api";
import { useT } from "@/lib/i18n";
import { useKpis } from "./useDashboardData";

const fmtPct = (v: number | null | undefined): string =>
  v === null || v === undefined ? "—" : `${v.toFixed(1)}%`;

const fmtNumber = (v: number | null | undefined): string =>
  v === null || v === undefined ? "—" : v.toLocaleString("tr-TR");

const fmtHours = (minutes: number | null | undefined): string => {
  if (minutes === null || minutes === undefined) return "—";
  return `${(minutes / 60).toLocaleString("tr-TR", { maximumFractionDigits: 1 })} sa`;
};

function pctChange(
  current: number | null | undefined,
  previous: number | null | undefined,
): SummaryTrend | null {
  if (current === null || current === undefined) return null;
  if (previous === null || previous === undefined || previous === 0) return null;
  const change = ((current - previous) / previous) * 100;
  const direction: TrendDirection =
    Math.abs(change) < 0.1 ? "flat" : change > 0 ? "up" : "down";
  return { value: change, direction };
}

interface PeriodKpis {
  avg_oee: number | null;
  total_production: number | null;
  total_scrap: number | null;
  total_down_time_minutes: number | null;
}

function KpiCardGridInner() {
  const t = useT();
  const kpis = useKpis();
  const today = new Date();
  const todayStr = format(today, "yyyy-MM-dd");
  const last7Str = format(subDays(today, 7), "yyyy-MM-dd");
  const prev7Str = format(subDays(today, 14), "yyyy-MM-dd");
  const prev7EndStr = format(subDays(today, 7), "yyyy-MM-dd");

  // İki period'u tek useQueries ile paralel çek → ayrı hook yerine tek koordinasyon.
  const periodResults = useQueries({
    queries: [
      {
        queryKey: ["analytics", "kpis", "period", last7Str, todayStr] as const,
        queryFn: () =>
          api.get<PeriodKpis>(
            `/api/v1/analytics/kpis?start=${last7Str}&end=${todayStr}`,
          ),
        staleTime: 60_000,
      },
      {
        queryKey: ["analytics", "kpis", "period", prev7Str, prev7EndStr] as const,
        queryFn: () =>
          api.get<PeriodKpis>(
            `/api/v1/analytics/kpis?start=${prev7Str}&end=${prev7EndStr}`,
          ),
        staleTime: 60_000,
      },
    ],
  });
  const kpisCurrent = periodResults[0]?.data;
  const kpisPrevious = periodResults[1]?.data;
  const periodLoading = periodResults.some((r) => r.isLoading);

  const oeeTrend = pctChange(kpisCurrent?.avg_oee, kpisPrevious?.avg_oee);
  const productionTrend = pctChange(
    kpisCurrent?.total_production,
    kpisPrevious?.total_production,
  );
  const scrapTrend = pctChange(kpisCurrent?.total_scrap, kpisPrevious?.total_scrap);
  const downtimeTrend = pctChange(
    kpisCurrent?.total_down_time_minutes,
    kpisPrevious?.total_down_time_minutes,
  );

  const loading = kpis.isLoading || periodLoading;

  return (
    <section className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <SummaryCard
        label={t("dashboard.kpiCardGrid.avgOee")}
        value={fmtPct(kpis.data?.avg_oee)}
        icon={<Gauge className="h-4 w-4" />}
        tone={oeeTone(kpis.data?.avg_oee)}
        trend={oeeTrend}
        hint={t("dashboard.kpiCardGrid.avgOeeHint")}
        loading={loading}
      />
      <SummaryCard
        label={t("dashboard.kpiCardGrid.totalProduction")}
        value={fmtNumber(kpis.data?.total_production)}
        icon={<Package className="h-4 w-4" />}
        trend={productionTrend}
        hint={t("dashboard.kpiCardGrid.unitHint")}
        loading={loading}
      />
      <SummaryCard
        label={t("dashboard.kpiCardGrid.totalScrap")}
        value={fmtNumber(kpis.data?.total_scrap)}
        icon={<AlertTriangle className="h-4 w-4" />}
        tone="low"
        trend={scrapTrend}
        inverted
        hint={t("dashboard.kpiCardGrid.unitHint")}
        loading={loading}
      />
      <SummaryCard
        label={t("dashboard.kpiCardGrid.totalDowntime")}
        value={fmtHours(kpis.data?.total_down_time_minutes)}
        icon={<Clock className="h-4 w-4" />}
        tone="low"
        trend={downtimeTrend}
        inverted
        hint={t("dashboard.kpiCardGrid.hourHint")}
        loading={loading}
      />
    </section>
  );
}

export const KpiCardGrid = memo(KpiCardGridInner);
