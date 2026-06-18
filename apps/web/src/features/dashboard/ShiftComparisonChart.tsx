"use client";

import { Inbox } from "lucide-react";
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
import { useShiftComparison } from "./useDashboardData";
import type { ShiftComparisonRow } from "./types";

const SHIFT_LABELS: Record<number, string> = { 1: "Sabah", 2: "Öğle", 3: "Gece" };
const SHIFT_COLORS: string[] = [
  "hsl(var(--chart-1))",
  "hsl(var(--chart-2))",
  "hsl(var(--chart-3))",
];

export function ShiftComparisonChart() {
  const q = useShiftComparison();
  const data: ShiftComparisonRow[] = q.data ?? [];

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader>
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Vardiya Karşılaştırma
        </CardTitle>
      </CardHeader>
      <CardContent>
        {q.isLoading ? (
          <Skeleton className="h-72 w-full" />
        ) : data.length === 0 ? (
          <div className="flex h-72 flex-col items-center justify-center gap-2 text-sm text-muted-foreground">
            <Inbox className="h-8 w-8 opacity-60" />
            <p>Veri yok</p>
          </div>
        ) : (
          <ResponsiveContainer width="100%" height={288}>
            <RadialBarChart
              innerRadius="20%"
              outerRadius="100%"
              data={data.map((r, i) => ({
                name: SHIFT_LABELS[r.shift] ?? `Vardiya ${r.shift}`,
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
