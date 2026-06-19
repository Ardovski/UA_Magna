"use client";

import { cn } from "@/lib/utils";

export interface KeyValueRowProps {
  label: string;
  value: React.ReactNode;
  className?: string;
  labelClassName?: string;
  valueClassName?: string;
}

export function KeyValueRow({
  label,
  value,
  className,
  labelClassName,
  valueClassName,
}: KeyValueRowProps) {
  return (
    <div className={cn("flex flex-col gap-0.5 text-sm", className)}>
      <span className={cn("text-xs font-medium text-muted-foreground", labelClassName)}>
        {label}
      </span>
      <span className={cn("text-foreground", valueClassName)}>{value}</span>
    </div>
  );
}
