import { Loader2, Sparkles } from "lucide-react";

export function GlobalLoader() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center gap-4 bg-background">
      <div className="flex items-center gap-2 text-lg font-bold text-foreground">
        <Sparkles className="h-5 w-5 text-primary" />
        Resume Intelligence
      </div>
      <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
    </div>
  );
}
