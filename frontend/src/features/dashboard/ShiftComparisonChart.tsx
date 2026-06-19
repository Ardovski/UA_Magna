"use client";

import { memo } from "react";
import {
  Legend,
  PolarAngleAxis,
  RadialBar,
  RadialBarChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/atoms";
import { useT } from "@/lib/i18n";
import { useShiftComparison } from "./useDashboardData";
import type { ShiftComparisonRow } from "./types";

const SHIFT_COLORS: string[] = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
];

function ShiftComparisonChartInner() {
  const t = useT();
  const q = useShiftComparison();
  const data: ShiftComparisonRow[] = q.data ?? [];

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {t("dashboard.shiftComparisonChart.title")}
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : data.length === 0 ? (
          <EmptyState title={t("common.noData")} className="h-72" />
        ) : (
          <ResponsiveContainer width="100%" height={288} debounce={50}>
            <RadialBarChart
              innerRadius="20%"
              outerRadius="100%"
              data={data.map((r, i) => ({
                name: t(`shift.${r.shift}`),
                shift: r.shift,
                avg_oee: r.avg_oee ?? 0,
                fill: SHIFT_COLORS[i % SHIFT_COLORS.length],
              }))}
              startAngle={90}
              endAngle={-270}
            >
              <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
              <RadialBar
                background
                dataKey="avg_oee"
                cornerRadius={6}
                stroke="none"
              />
              <Legend
                iconSize={10}
                layout="vertical"
                verticalAlign="middle"
                align="right"
                wrapperStyle={{ fontSize: 12, color: "hsl(var(--muted-foreground))" }}
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
            </RadialBarChart>
          </ResponsiveContainer>
        )}
      </CardContent>
    </Card>
  );
}

export const ShiftComparisonChart = memo(ShiftComparisonChartInner);
