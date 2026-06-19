"use client";

import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export interface SkeletonTextProps {
  lines?: number;
  className?: string;
  lastLineShort?: boolean;
}

export function SkeletonText({ lines = 3, className, lastLineShort = true }: SkeletonTextProps) {
  return (
    <div className={cn("space-y-2", className)}>
      {Array.from({ length: lines }).map((_, i) => (
        <Skeleton
          key={i}
          className={cn("h-3", i === lines - 1 && lastLineShort ? "w-2/3" : "w-full")}
        />
      ))}
    </div>
  );
}
