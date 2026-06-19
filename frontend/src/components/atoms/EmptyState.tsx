"use client";

import * as React from "react";
import { Inbox } from "lucide-react";
import { cn } from "@/lib/utils";

export interface EmptyStateProps {
  icon?: React.ReactNode;
  title?: string;
  description?: string;
  action?: React.ReactNode;
  className?: string;
}

export function EmptyState({ icon, title, description, action, className }: EmptyStateProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center gap-2 px-4 py-8 text-center text-sm text-muted-foreground",
        className,
      )}
    >
      <div className="opacity-60">
        {icon ?? <Inbox className="h-8 w-8" />}
      </div>
      {title ? <p className="font-medium text-foreground">{title}</p> : null}
      {description ? <p className="max-w-sm text-xs">{description}</p> : null}
      {action ? <div className="mt-2">{action}</div> : null}
    </div>
  );
}
