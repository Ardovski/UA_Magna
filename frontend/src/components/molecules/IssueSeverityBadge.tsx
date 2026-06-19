"use client";

import { Badge, severityTone } from "@/components/ui/badge";
import { useT } from "@/lib/i18n";

export interface IssueSeverityBadgeProps {
  severity: string;
}

export function IssueSeverityBadge({ severity }: IssueSeverityBadgeProps) {
  const t = useT();
  return <Badge tone={severityTone(severity)}>{t(`severity.${severity}`)}</Badge>;
}
