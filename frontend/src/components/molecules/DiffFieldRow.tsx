"use client";

import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";
import { FieldLabel } from "@/components/atoms/FieldLabel";

export interface DiffFieldRowProps {
  field: string;
  currentValue: string;
  newValue: string;
  onChange: (v: string) => void;
  type?: "text" | "number";
  loading?: boolean;
  dirty?: boolean;
  className?: string;
}

export function DiffFieldRow({
  field,
  currentValue,
  newValue,
  onChange,
  type = "text",
  loading,
  dirty,
  className,
}: DiffFieldRowProps) {
  if (loading) {
    return (
      <div className={cn("grid grid-cols-2 gap-3 rounded-md border bg-card p-3", className)}>
        <Skeleton className="h-9 w-full" />
        <Skeleton className="h-9 w-full" />
      </div>
    );
  }
  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-3 rounded-md border bg-card p-3 md:grid-cols-[1fr_24px_1fr]",
        dirty && "border-warning/60",
        className,
      )}
    >
      <div className="space-y-1">
        <FieldLabel>{field}</FieldLabel>
        <div className="rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
          {currentValue === "" || currentValue === null || currentValue === undefined
            ? <span className="italic">—</span>
            : String(currentValue)}
        </div>
      </div>
      <div className="hidden items-center justify-center text-muted-foreground md:flex">→</div>
      <div className="space-y-1">
        <FieldLabel>{field} (yeni)</FieldLabel>
        <Input
          type={type}
          value={newValue}
          onChange={(e) => onChange(e.target.value)}
          className={cn(dirty && "border-warning focus-visible:ring-warning")}
        />
      </div>
    </div>
  );
}
