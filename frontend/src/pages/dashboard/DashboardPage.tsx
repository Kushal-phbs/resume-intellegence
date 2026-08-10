import { FileText, Target, TrendingUp, Flame, RefreshCw, Cpu, CheckCircle2 } from "lucide-react";
import { useDashboardOverview, useRefreshDashboard } from "@/hooks/useDashboard";
import { StatCard } from "@/components/dashboard/StatCard";
import { ScoreDistributionChart } from "@/components/dashboard/ScoreDistributionChart";
import { TrendsChart } from "@/components/dashboard/TrendsChart";
import { RecentResumes } from "@/components/dashboard/RecentResumes";
import { ActivityFeed } from "@/components/dashboard/ActivityFeed";
import { QuickActions } from "@/components/dashboard/QuickActions";
import { AISuggestions } from "@/components/dashboard/AISuggestions";
import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/common/ErrorState";

function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 w-full" />
        ))}
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton className="h-64 w-full" />
        <Skeleton className="h-64 w-full" />
      </div>
    </div>
  );
}

export function DashboardPage() {
  const { data, isLoading, isError, error, refetch } = useDashboardOverview();
  const refresh = useRefreshDashboard();

  if (isLoading) return <DashboardSkeleton />;
  if (isError || !data) return <ErrorState error={error} onRetry={() => refetch()} />;

  const { user, statistics, recent_resumes, score_distribution, analytics_summary, latest_ai_suggestions, unread_notifications, quick_actions } = data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            Good to see you, {user.full_name.split(" ")[0]} 👋
          </h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Here's what's happening across your resumes.
          </p>
        </div>
        <Button variant="ghost" size="sm" onClick={() => refresh.mutate()} isLoading={refresh.isPending}>
          <RefreshCw className="h-3.5 w-3.5" />
          Refresh
        </Button>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <StatCard icon={FileText} label="Total Resumes" value={statistics.total_resumes} />
        <StatCard
          icon={Target}
          label="Average ATS Score"
          value={statistics.average_ats_score !== null ? Math.round(statistics.average_ats_score) : "—"}
          accent="text-secondary"
        />
        <StatCard
          icon={TrendingUp}
          label="Highest Score"
          value={statistics.highest_ats_score ?? "—"}
          hint={`${statistics.improvement_percentage >= 0 ? "+" : ""}${statistics.improvement_percentage.toFixed(1)}% overall`}
          accent="text-success"
        />
        <StatCard
          icon={Flame}
          label="Improvement Streak"
          value={statistics.improvement_streak}
          hint={statistics.improvement_streak > 0 ? "Keep it going!" : undefined}
          accent="text-destructive"
        />
      </div>

      {/* AI usage summary */}
      <Card>
        <CardContent className="flex flex-wrap items-center gap-6 p-5">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm text-muted-foreground">AI requests</span>
            <span className="text-sm font-semibold">{analytics_summary.total_ai_requests}</span>
          </div>
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-success" />
            <span className="text-sm text-muted-foreground">Success rate</span>
            <span className="text-sm font-semibold">{analytics_summary.success_rate.toFixed(1)}%</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Tokens used</span>
            <span className="text-sm font-semibold">{analytics_summary.total_tokens_used.toLocaleString()}</span>
          </div>
          {analytics_summary.average_processing_time_ms !== null && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-muted-foreground">Avg. processing</span>
              <span className="text-sm font-semibold">
                {(analytics_summary.average_processing_time_ms / 1000).toFixed(2)}s
              </span>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Charts */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <TrendsChart />
        <ScoreDistributionChart data={score_distribution} />
      </div>

      {/* Lower grid: recent resumes / activity / quick actions / suggestions */}
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <RecentResumes items={recent_resumes} />
        <ActivityFeed items={unread_notifications} />
        <QuickActions items={quick_actions} />
        <AISuggestions items={latest_ai_suggestions} />
      </div>
    </div>
  );
}
