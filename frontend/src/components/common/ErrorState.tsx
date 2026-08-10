import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { getApiErrorMessage } from "@/api/client";

export function ErrorState({ error, onRetry }: { error: unknown; onRetry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-destructive/30 bg-destructive/5 py-14 text-center">
      <div className="flex h-14 w-14 items-center justify-center rounded-full bg-destructive/10">
        <AlertTriangle className="h-7 w-7 text-destructive" />
      </div>
      <div>
        <h3 className="text-sm font-semibold text-destructive">Something went wrong</h3>
        <p className="mt-1 max-w-sm text-sm text-muted-foreground">{getApiErrorMessage(error)}</p>
      </div>
      {onRetry && (
        <Button size="sm" variant="outline" onClick={onRetry}>
          Try again
        </Button>
      )}
    </div>
  );
}
