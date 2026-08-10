import { useEffect, useRef, useState } from "react";
import { Bell, CheckCheck, Trash2, ExternalLink } from "lucide-react";
import { Link } from "react-router-dom";
import { useNotifications, useMarkAllRead, useMarkRead } from "@/hooks/useNotifications";
import { notificationsApi } from "@/api/notifications";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { formatRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { NotificationPriority } from "@/types/notification";

const PRIORITY_VARIANT: Record<NotificationPriority, "default" | "success" | "destructive" | "muted"> = {
  low: "muted",
  medium: "default",
  high: "destructive",
  critical: "destructive",
};

export function NotificationPanel() {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data, isLoading, isError, error, refetch } = useNotifications({ limit: 20 });
  const markAllRead = useMarkAllRead();
  const markRead = useMarkRead();

  const unreadCount = data?.items.filter((n) => !n.is_read).length ?? 0;

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onClickOutside);
    return () => document.removeEventListener("mousedown", onClickOutside);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ""}`}
        aria-expanded={open}
        className="relative flex h-9 w-9 items-center justify-center rounded-md text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute right-1.5 top-1.5 flex h-4 w-4 items-center justify-center rounded-full bg-destructive text-[9px] font-bold text-destructive-foreground">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-full z-50 mt-2 w-80 overflow-hidden rounded-lg border border-border bg-card shadow-lg">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-border px-4 py-2.5">
            <h3 className="text-sm font-semibold">Notifications</h3>
            {unreadCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => markAllRead.mutate()}
                isLoading={markAllRead.isPending}
                className="h-7 gap-1 text-xs"
              >
                <CheckCheck className="h-3.5 w-3.5" />
                Mark all read
              </Button>
            )}
          </div>

          {/* List */}
          <div className="max-h-80 overflow-y-auto">
            {isLoading ? (
              <div className="space-y-2 p-3">
                {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
              </div>
            ) : isError ? (
              <div className="p-3">
                <ErrorState error={error} onRetry={() => refetch()} />
              </div>
            ) : !data || data.items.length === 0 ? (
              <div className="p-3">
                <EmptyState icon={Bell} title="All caught up" description="No notifications right now." />
              </div>
            ) : (
              data.items.map((n) => (
                <div
                  key={n.id}
                  className={cn(
                    "flex items-start gap-3 border-b border-border px-4 py-3 transition-colors last:border-0",
                    !n.is_read && "bg-primary/5"
                  )}
                >
                  <div className="min-w-0 flex-1">
                    <p className="text-sm font-medium">{n.title}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground">{n.message}</p>
                    <div className="mt-1.5 flex items-center gap-2">
                      <span className="text-xs text-muted-foreground">{formatRelative(n.created_at)}</span>
                      <Badge variant={PRIORITY_VARIANT[n.priority]}>{n.priority}</Badge>
                    </div>
                  </div>
                  <div className="flex shrink-0 gap-1 pt-0.5">
                    {!n.is_read && (
                      <button
                        onClick={() => markRead.mutate(n.id)}
                        className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                        aria-label="Mark as read"
                      >
                        <CheckCheck className="h-3.5 w-3.5" />
                      </button>
                    )}
                    <button
                      onClick={() => notificationsApi.remove(n.id)}
                      className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                      aria-label="Dismiss notification"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          {/* Footer */}
          {data && data.total > 20 && (
            <div className="border-t border-border px-4 py-2 text-center">
              <Link
                to="/settings"
                onClick={() => setOpen(false)}
                className="flex items-center justify-center gap-1 text-xs text-muted-foreground hover:text-foreground"
              >
                <ExternalLink className="h-3 w-3" />
                View all {data.total} notifications
              </Link>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
