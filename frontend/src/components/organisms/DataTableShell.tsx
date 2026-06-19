"use client";

import * as React from "react";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/atoms/EmptyState";
import { cn } from "@/lib/utils";

export interface DataTableShellProps {
  loading?: boolean;
  isEmpty?: boolean;
  emptyTitle?: string;
  emptyDescription?: string;
  emptyAction?: React.ReactNode;
  loadingRows?: number;
  loadingRowHeight?: number;
  children?: React.ReactNode;
  className?: string;
}

/** Tablo/metin/liste için ortak kabuk: skeleton / empty / içerik. */
export function DataTableShell({
  loading,
  isEmpty,
  emptyTitle,
  emptyDescription,
  emptyAction,
  loadingRows = 6,
  loadingRowHeight = 28,
  children,
  className,
}: DataTableShellProps) {
  return (
    <div className={cn("rounded-lg border bg-card text-card-foreground", className)}>
      {loading ? (
        <div className="space-y-1 p-2">
          {Array.from({ length: loadingRows }).map((_, i) => (
            <Skeleton
              key={i}
              className="w-full"
              style={{ height: loadingRowHeight }}
            />
          ))}
        </div>
      ) : isEmpty ? (
        <EmptyState
          title={emptyTitle}
          description={emptyDescription}
          action={emptyAction}
          className="min-h-[160px]"
        />
      ) : (
        children
      )}
    </div>
  );
}
