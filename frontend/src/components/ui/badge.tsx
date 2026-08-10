import * as React from "react";
import { cn } from "@/lib/utils";

const variants = {
  default: "bg-primary/15 text-primary",
  success: "bg-success/15 text-success",
  destructive: "bg-destructive/15 text-destructive",
  secondary: "bg-secondary/15 text-secondary",
  muted: "bg-muted text-muted-foreground",
};

export function Badge({
  className,
  variant = "default",
  ...props
}: React.HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof variants }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2.5 py-0.5 text-[11px] font-semibold uppercase tracking-wide",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
