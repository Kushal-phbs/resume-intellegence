import { useState } from "react";
import { Bell, CheckCheck, Trash2, Sun, Moon, Monitor, Lock, Info } from "lucide-react";
import { useNotifications, useMarkAllRead, useMarkRead } from "@/hooks/useNotifications";
import { notificationsApi } from "@/api/notifications";
import { useQueryClient } from "@tanstack/react-query";
import { useThemeStore } from "@/store/themeStore";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { formatRelative } from "@/lib/utils";
import { cn } from "@/lib/utils";
import type { NotificationPriority } from "@/types/notification";

const PRIORITY_VARIANT: Record<NotificationPriority, "default" | "success" | "destructive" | "muted"> = {
  low: "muted", medium: "default", high: "destructive", critical: "destructive",
};

const THEMES = [
  { value: "light" as const, icon: Sun, label: "Light" },
  { value: "dark" as const, icon: Moon, label: "Dark" },
  { value: "system" as const, icon: Monitor, label: "System" },
];

export function SettingsPage() {
  const [onlyUnread, setOnlyUnread] = useState(false);
  const filters = { limit: 50, only_unread: onlyUnread || undefined };
  const { data, isLoading, isError, error, refetch } = useNotifications(filters);
  const markAllRead = useMarkAllRead();
  const markRead = useMarkRead();
  const queryClient = useQueryClient();
  const { theme, setTheme } = useThemeStore();

  const handleDelete = async (id: string) => {
    await notificationsApi.remove(id);
    queryClient.invalidateQueries({ queryKey: ["notifications"] });
  };

  const unreadCount = data?.items.filter((n) => !n.is_read).length ?? 0;

  return (
    <div className="max-w-2xl space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your preferences and account.</p>
      </div>

      {/* ── Theme ── */}
      <Card>
        <CardHeader>
          <CardTitle>Appearance</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="mb-3 text-sm text-muted-foreground">Choose how Resume Intelligence looks to you.</p>
          <div className="flex gap-2">
            {THEMES.map(({ value, icon: Icon, label }) => (
              <button
                key={value}
                onClick={() => setTheme(value)}
                className={cn(
                  "flex flex-1 flex-col items-center gap-1.5 rounded-md border py-3 text-xs font-medium transition-colors",
                  theme === value
                    ? "border-primary bg-primary/10 text-primary"
                    : "border-border text-muted-foreground hover:bg-muted"
                )}
                aria-pressed={theme === value}
                aria-label={`${label} theme`}
              >
                <Icon className="h-4 w-4" />
                {label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* ── Password (disabled — no backend endpoint) ── */}
      <Card className="opacity-60">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Lock className="h-4 w-4" />
            Password
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-start gap-2 rounded-md bg-muted/50 px-3 py-2.5 text-xs text-muted-foreground">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>
              Password change is not available — the backend does not expose a password-update
              endpoint. Contact your administrator to reset your password.
            </span>
          </div>
          <Button disabled variant="outline" className="w-full sm:w-auto">
            Change Password
          </Button>
        </CardContent>
      </Card>

      {/* ── Notifications center ── */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-3">
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              Notifications
              {unreadCount > 0 && (
                <Badge variant="destructive" className="ml-1">{unreadCount} unread</Badge>
              )}
            </CardTitle>
            <div className="flex gap-2">
              <Button
                variant={onlyUnread ? "default" : "outline"}
                size="sm"
                onClick={() => setOnlyUnread((v) => !v)}
              >
                {onlyUnread ? "Show all" : "Unread only"}
              </Button>
              {unreadCount > 0 && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => markAllRead.mutate()}
                  isLoading={markAllRead.isPending}
                >
                  <CheckCheck className="h-4 w-4" />
                  Mark all read
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-5">
              {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : isError ? (
            <div className="p-5"><ErrorState error={error} onRetry={() => refetch()} /></div>
          ) : !data || data.items.length === 0 ? (
            <div className="p-5">
              <EmptyState
                icon={Bell}
                title="No notifications"
                description={onlyUnread ? "No unread notifications." : "You're all caught up!"}
              />
            </div>
          ) : (
            data.items.map((n) => (
              <div
                key={n.id}
                className={cn(
                  "flex items-start gap-3 border-b border-border px-5 py-3.5 transition-colors last:border-0",
                  !n.is_read && "bg-primary/5"
                )}
              >
                <div className="min-w-0 flex-1">
                  <p className={cn("text-sm font-medium", !n.is_read && "text-foreground")}>{n.title}</p>
                  <p className="mt-0.5 text-sm text-muted-foreground">{n.message}</p>
                  <div className="mt-1.5 flex flex-wrap items-center gap-2">
                    <span className="text-xs text-muted-foreground">{formatRelative(n.created_at)}</span>
                    <Badge variant={PRIORITY_VARIANT[n.priority]}>{n.priority}</Badge>
                    {!n.is_read && <Badge variant="default">Unread</Badge>}
                  </div>
                </div>
                <div className="flex shrink-0 gap-1 pt-0.5">
                  {!n.is_read && (
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-7 w-7 text-muted-foreground hover:text-foreground"
                      aria-label="Mark as read"
                      onClick={() => markRead.mutate(n.id)}
                    >
                      <CheckCheck className="h-3.5 w-3.5" />
                    </Button>
                  )}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-destructive"
                    aria-label="Dismiss notification"
                    onClick={() => handleDelete(n.id)}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
}
