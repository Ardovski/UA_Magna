"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type StatusDotTone = "default" | "success" | "warning" | "destructive" | "info";

const toneClass: Record<StatusDotTone, string> = {
  default: "bg-muted-foreground",
  success: "bg-success",
  warning: "bg-warning",
  destructive: "bg-destructive",
  info: "bg-info",
};

export interface StatusDotProps extends React.HTMLAttributes<HTMLSpanElement> {
  tone?: StatusDotTone;
  size?: "sm" | "md";
}

export function StatusDot({ tone = "default", size = "sm", className, ...props }: StatusDotProps) {
  const sizeClass = size === "sm" ? "h-2 w-2" : "h-2.5 w-2.5";
  return (
    <span
      aria-hidden
      className={cn("inline-block shrink-0 rounded-full", sizeClass, toneClass[tone], className)}
      {...props}
    />
  );
}
