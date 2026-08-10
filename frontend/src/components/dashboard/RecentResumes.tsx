import { Link } from "react-router-dom";
import { FileText, ChevronRight, Star } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/common/EmptyState";
import { ROUTES } from "@/constants/routes";
import type { DashboardRecentResumeResponse } from "@/types/dashboard";

export function RecentResumes({ items }: { items: DashboardRecentResumeResponse[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Resumes</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState
            icon={FileText}
            title="No resumes yet"
            description="Upload your first resume to start getting AI-powered insights."
            actionLabel="Upload Resume"
            onAction={() => (window.location.href = ROUTES.resumes)}
          />
        ) : (
          <div className="space-y-2">
            {items.map((r) => (
              <Link
                key={r.id}
                to={ROUTES.resumeDetail(r.id)}
                className="flex items-center gap-3 rounded-md bg-muted/50 p-3 transition-transform hover:translate-x-0.5 hover:bg-muted"
              >
                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-muted">
                  <FileText className="h-4 w-4 text-muted-foreground" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{r.title}</p>
                  <p className="text-xs text-muted-foreground">Updated {new Date(r.updated_at).toLocaleDateString()}</p>
                </div>
                {r.is_primary && <Star className="h-3.5 w-3.5 shrink-0 text-primary" fill="currentColor" />}
                {r.latest_ats_score !== null && (
                  <Badge variant={r.latest_ats_score >= 70 ? "success" : "destructive"}>{r.latest_ats_score}</Badge>
                )}
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
