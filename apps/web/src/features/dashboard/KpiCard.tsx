"use client";

import { ArrowDown, ArrowUp, Minus } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type Tone = "good" | "mid" | "low" | "neutral";

export function oeeTone(v: number | null | undefined): Tone {
  if (v === null || v === undefined) return "neutral";
  if (v >= 85) return "good";
  if (v >= 60) return "mid";
  return "low";
}

export type TrendDirection = "up" | "down" | "flat";

export interface KpiTrend {
  value: number;
  direction: TrendDirection;
}

export interface KpiCardProps {
  label: string;
  value: string;
  icon: React.ReactNode;
  trend?: KpiTrend | null;
  tone?: Tone;
  inverted?: boolean;
  hint?: string;
  loading?: boolean;
}

function trendColor(tone: Tone, inverted: boolean, dir: TrendDirection): string {
  if (dir === "flat") return "text-muted-foreground";
  const isUp = dir === "up";
  if (inverted) return isUp ? "text-oee-low" : "text-oee-good";
  if (tone === "low") return isUp ? "text-oee-good" : "text-oee-low";
  return isUp ? "text-oee-good" : "text-oee-low";
}

function trendArrow(dir: TrendDirection): React.ReactNode {
  if (dir === "up") return <ArrowUp className="h-3 w-3" />;
  if (dir === "down") return <ArrowDown className="h-3 w-3" />;
  return <Minus className="h-3 w-3" />;
}

export function KpiCard({
  label,
  value,
  icon,
  trend,
  tone,
  inverted,
  hint,
  loading,
}: KpiCardProps) {
  const t: Tone = tone ?? "neutral";
  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <span className="text-muted-foreground">{icon}</span>
          {label}
        </CardTitle>
        {trend ? (
          <span
            className={cn(
              "inline-flex items-center gap-0.5 rounded-md px-1.5 py-0.5 text-xs font-medium tabular-nums",
              trendColor(t, Boolean(inverted), trend.direction),
            )}
          >
            {trendArrow(trend.direction)}
            {Math.abs(trend.value).toFixed(1)}%
          </span>
        ) : null}
      </CardHeader>
      <CardContent>
        {loading ? (
          <Skeleton className="h-8 w-24" />
        ) : (
          <p
            className={cn(
              "text-3xl font-semibold tabular-nums tracking-tight",
              t === "good" && "text-oee-good",
              t === "mid" && "text-oee-mid",
              t === "low" && "text-oee-low",
              t === "neutral" && "text-foreground",
            )}
          >
            {value}
          </p>
        )}
        {hint ? <p className="mt-1 text-xs text-muted-foreground">{hint}</p> : null}
      </CardContent>
    </Card>
  );
}
