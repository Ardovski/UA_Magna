"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface FieldLabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

export function FieldLabel({ className, children, required, ...props }: FieldLabelProps) {
  return (
    <label
      className={cn("block text-xs font-medium text-muted-foreground", className)}
      {...props}
    >
      {children}
      {required ? <span className="ml-0.5 text-destructive">*</span> : null}
    </label>
  );
}
