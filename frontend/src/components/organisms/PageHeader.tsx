"use client";

import { cn } from "@/lib/utils";

export interface PageHeaderProps {
  subtitle?: string;
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
}

/** Sayfa başlığı — alt başlık (mono), başlık, açıklama ve sağ aksiyon slot'u. */
export function PageHeader({ subtitle, title, description, actions, className }: PageHeaderProps) {
  return (
    <header className={cn("flex flex-wrap items-end justify-between gap-3", className)}>
      <div>
        {subtitle ? (
          <p className="font-mono text-sm text-muted-foreground">MAGNA · {subtitle}</p>
        ) : null}
        <h1 className="mt-1 text-3xl font-bold tracking-tight">{title}</h1>
        {description ? (
          <div className="mt-2 text-sm text-muted-foreground">{description}</div>
        ) : null}
      </div>
      {actions ? <div className="flex items-center gap-2">{actions}</div> : null}
    </header>
  );
}
