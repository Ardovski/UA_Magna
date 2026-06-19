"use client";

import { memo } from "react";
import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/atoms";
import { useT } from "@/lib/i18n";
import { useOeeTrend } from "./useDashboardData";

function OeeTrendChartInner() {
  const t = useT();
  const q = useOeeTrend(21);
  const data = q.data ?? [];

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {t("dashboard.oeeTrendChart.title")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : data.length === 0 ? (
          <EmptyState title={t("common.noData")} className="h-72" />
        ) : (
          <ResponsiveContainer width="100%" height={288} debounce={50}>
            <AreaChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
              <defs>
                <linearGradient id="oeeGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="hsl(var(--chart-1))" stopOpacity={0.45} />
                  <stop offset="100%" stopColor="hsl(var(--chart-1))" stopOpacity={0.02} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis
                dataKey="prod_date"
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
              />
              <YAxis
                domain={[0, 100]}
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                tickLine={false}
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  color: "hsl(var(--card-foreground))",
                  borderRadius: 6,
                }}
              />
              <Area
                type="monotone"
                dataKey="avg_oee"
                name="OEE %"
                stroke="hsl(var(--chart-1))"
                strokeWidth={2}
                fill="url(#oeeGradient)"
              />
            </AreaChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

export const OeeTrendChart = memo(OeeTrendChartInner);
