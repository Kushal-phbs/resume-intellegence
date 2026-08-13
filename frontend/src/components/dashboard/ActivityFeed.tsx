import { EmptyState } from "@/components/common/EmptyState";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatRelative } from "@/lib/utils";
import type { DashboardNotificationResponse } from "@/types/dashboard";
import { Bell, Briefcase, ChevronDown, ChevronUp, Download, FileText, LogIn, Mail, Wand2 } from "lucide-react";
import { useState } from "react";

const ACTIVITY_ICON: Record<string, typeof FileText> = {
  resume_uploaded: FileText,
  resume_analyzed: FileText,
  job_analyzed: Briefcase,
  resume_tailored: Wand2,
  cover_letter_generated: Mail,
  export_generated: Download,
  login: LogIn,
};

const INITIAL_VISIBLE = 5;

/**
 * Backed by the dashboard overview's `unread_notifications` — the unified
 * GET /dashboard payload doesn't include a separate activity timeline
 * (that's DashboardResponse.recent_activity, returned only by the
 * POST /dashboard/refresh action), so this doubles as the activity feed.
 */
export function ActivityFeed({ items }: { items: DashboardNotificationResponse[] }) {
  const [expanded, setExpanded] = useState(false);
  const visible = expanded ? items : items.slice(0, INITIAL_VISIBLE);
  const hasMore = items.length > INITIAL_VISIBLE;

  return (
    <Card id="activity-feed">
      <CardHeader>
        <CardTitle>Activity Feed</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState icon={Bell} title="All caught up" description="No recent activity to show right now." />
        ) : (
          <div className="space-y-3">
            {visible.map((n) => {
              const Icon = ACTIVITY_ICON[n.activity_type] ?? Bell;
              return (
                <div key={n.id} className="flex items-start gap-3">
                  <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-muted">
                    <Icon className="h-3.5 w-3.5 text-muted-foreground" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="text-sm">{n.message}</p>
                    <p className="text-xs text-muted-foreground">{formatRelative(n.created_at)}</p>
                  </div>
                </div>
              );
            })}
            {hasMore && (
              <div className="flex justify-center pt-1">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setExpanded((e) => !e)}
                >
                  {expanded ? (
                    <>Show less <ChevronUp className="ml-1 h-4 w-4" /></>
                  ) : (
                    <>Show more <ChevronDown className="ml-1 h-4 w-4" /></>
                  )}
                </Button>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
