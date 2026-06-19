"use client";

import { Languages } from "lucide-react";
import { useLocale } from "@/lib/i18n";
import { cn } from "@/lib/utils";
import type { Locale } from "@/lib/i18n";

const OPTIONS: Locale[] = ["tr", "en"];

/** Header'da TR/EN dil seçici. Seçim localStorage'a yazılır. */
export function LanguageToggle() {
  const { locale, setLocale, t } = useLocale();
  return (
    <div
      className="flex items-center gap-1 rounded-md border bg-background p-0.5"
      role="group"
      aria-label={t("lang.label")}
    >
      <Languages className="ml-1 h-3.5 w-3.5 text-muted-foreground" aria-hidden />
      {OPTIONS.map((opt) => {
        const active = locale === opt;
        return (
          <button
            key={opt}
            type="button"
            aria-pressed={active}
            onClick={() => setLocale(opt)}
            className={cn(
              "rounded px-2 py-0.5 text-xs font-medium uppercase transition-colors",
              active
                ? "bg-primary text-primary-foreground"
                : "text-muted-foreground hover:text-foreground",
            )}
          >
            {opt}
          </button>
        );
      })}
    </div>
  );
}
