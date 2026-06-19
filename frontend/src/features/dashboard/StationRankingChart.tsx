"use client";

import { memo } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/atoms";
import { oeeTone } from "@/components/molecules";
import { useT } from "@/lib/i18n";
import { useStationRanking } from "./useDashboardData";

function oeeBarColor(v: number | null): string {
  if (v === null) return "hsl(var(--muted))";
  if (v >= 85) return "hsl(var(--oee-good))";
  if (v >= 60) return "hsl(var(--oee-mid))";
  return "hsl(var(--oee-low))";
}

function StationRankingChartInner() {
  const t = useT();
  const q = useStationRanking(10);
  const rows = (q.data ?? []).slice(0, 10);

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {t("dashboard.stationRankingChart.title")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : rows.length === 0 ? (
          <EmptyState title={t("common.noData")} className="h-72" />
        ) : (
          <ResponsiveContainer
            width="100%"
            height={Math.max(288, rows.length * 36)}
            debounce={50}
          >
            <BarChart
              layout="vertical"
              data={rows}
              margin={{ top: 8, right: 16, bottom: 8, left: 24 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                type="number"
                domain={[0, 100]}
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
              />
              <YAxis
                type="category"
                dataKey="station_name"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
                width={110}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  color: "hsl(var(--card-foreground))",
                  borderRadius: 6,
                }}
                formatter={(value: number) => [`${value.toFixed(1)}%`, "OEE"]}
              />
              <Bar dataKey="avg_oee" name="OEE %" radius={[0, 4, 4, 0]}>
                {rows.map((r) => (
                  <Cell key={r.station_name} fill={oeeBarColor(r.avg_oee)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

export const StationRankingChart = memo(StationRankingChartInner);
