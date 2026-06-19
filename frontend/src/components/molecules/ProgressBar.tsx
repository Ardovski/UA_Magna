"use client";

import { cn } from "@/lib/utils";

export interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercent?: boolean;
  tone?: "primary" | "success" | "warning" | "destructive";
  className?: string;
}

const toneClass: Record<NonNullable<ProgressBarProps["tone"]>, string> = {
  primary: "bg-primary",
  success: "bg-success",
  warning: "bg-warning",
  destructive: "bg-destructive",
};

export function ProgressBar({
  value,
  max = 100,
  label,
  showPercent = true,
  tone = "primary",
  className,
}: ProgressBarProps) {
  const pct = Math.max(0, Math.min(100, (value / max) * 100));
  return (
    <div className={cn("w-full", className)}>
      {(label || showPercent) ? (
        <div className="mb-1 flex items-center justify-between text-xs text-muted-foreground">
          {label ? <span>{label}</span> : <span />}
          {showPercent ? <span className="tabular-nums">{pct.toFixed(0)}%</span> : null}
        </div>
      ) : null}
      <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
        <div
          className={cn("h-full transition-all", toneClass[tone])}
          style={{ width: `${pct}%` }}
          role="progressbar"
          aria-valuenow={pct}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
    </div>
  );
}
