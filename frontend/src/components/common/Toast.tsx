import { useEffect, useState } from "react";
import { CheckCircle2, AlertTriangle, X, Info } from "lucide-react";
import { cn } from "@/lib/utils";
import { toastListeners } from "@/lib/toastBus";

export type ToastType = "success" | "error" | "info";

export interface ToastMessage {
  id: string;
  message: string;
  type: ToastType;
}

const ICONS = { success: CheckCircle2, error: AlertTriangle, info: Info };
const COLORS = {
  success: "border-success/30 bg-success/10 text-success",
  error:   "border-destructive/30 bg-destructive/10 text-destructive",
  info:    "border-border bg-muted text-foreground",
};

function ToastItem({ t, onDismiss }: { t: ToastMessage; onDismiss: () => void }) {
  const Icon = ICONS[t.type];

  useEffect(() => {
    const timer = setTimeout(onDismiss, 3500);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "flex items-center gap-2.5 rounded-lg border px-4 py-2.5 text-sm font-medium shadow-lg animate-in",
        COLORS[t.type]
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="flex-1">{t.message}</span>
      <button onClick={onDismiss} aria-label="Dismiss notification" className="ml-1 opacity-60 hover:opacity-100">
        <X className="h-3.5 w-3.5" />
      </button>
    </div>
  );
}

export function ToastContainer() {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const handler = (t: ToastMessage) => setToasts((prev) => [...prev, t]);
    toastListeners.push(handler);
    return () => {
      const idx = toastListeners.indexOf(handler);
      if (idx > -1) toastListeners.splice(idx, 1);
    };
  }, []);

  const dismiss = (id: string) => setToasts((prev) => prev.filter((t) => t.id !== id));

  if (toasts.length === 0) return null;
  return (
    <div className="fixed bottom-6 left-1/2 z-[100] flex -translate-x-1/2 flex-col gap-2">
      {toasts.map((t) => (
        <ToastItem key={t.id} t={t} onDismiss={() => dismiss(t.id)} />
      ))}
    </div>
  );
}
