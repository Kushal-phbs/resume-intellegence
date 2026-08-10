import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

export function InsightList({
  icon: Icon,
  items,
  tone,
  emptyLabel,
}: {
  icon: LucideIcon;
  items: string[];
  tone: "success" | "destructive" | "primary";
  emptyLabel: string;
}) {
  const toneClass = {
    success: "text-success",
    destructive: "text-destructive",
    primary: "text-primary",
  }[tone];

  if (items.length === 0) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>;
  }

  return (
    <ul className="space-y-2">
      {items.map((item, i) => (
        <li key={i} className="flex items-start gap-2 text-sm">
          <Icon className={cn("mt-0.5 h-3.5 w-3.5 shrink-0", toneClass)} />
          <span>{item}</span>
        </li>
      ))}
    </ul>
  );
}
