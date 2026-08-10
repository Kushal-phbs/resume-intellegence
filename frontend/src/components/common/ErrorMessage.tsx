import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export function ErrorMessage({
  message,
  className,
}: {
  message: string;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/10 px-3 py-2.5 text-sm text-destructive",
        className
      )}
      role="alert"
    >
      <AlertCircle className="h-4 w-4 shrink-0" />
      <span>{message}</span>
    </div>
  );
}
