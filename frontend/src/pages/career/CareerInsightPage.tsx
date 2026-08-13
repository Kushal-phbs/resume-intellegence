import { useQuery } from "@tanstack/react-query";
import { ChevronDown, ChevronUp, FileText, FolderOpen, Mail, Target, TrendingUp, Wand2 } from "lucide-react";
import { useState } from "react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { dashboardApi } from "@/api/dashboard";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardOverview, useDashboardTrends } from "@/hooks/useDashboard";

const INITIAL_MILESTONES = 5;

function formatAxisLabel(ts: number): string {
  return new Date(ts).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

function formatTooltipLabel(ts: number): string {
  return new Date(ts).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
  });
}

function Delta({ previous, current }: { previous: number | null; current: number | null }) {
  if (previous === null || current === null || previous === undefined || current === undefined) {
    return <span className="text-xs text-muted-foreground">—</span>;
  }
  const diff = current - previous;
  if (diff > 0) {
    return (
      <span className="text-xs font-semibold text-green-500">
        ↑ +{diff}
      </span>
    );
  }
  if (diff < 0) {
    return (
      <span className="text-xs font-semibold text-red-500">
        ↓ {diff}
      </span>
    );
  }
  return <span className="text-xs font-semibold text-muted-foreground">→ 0</span>;
}

function StatCard({
  title,
  current,
  previous,
  icon: Icon,
}: {
  title: string;
  current: number | null;
  previous?: number | null;
  icon: typeof TrendingUp;
}) {
  return (
    <Card>
      <CardContent className="pt-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Icon className="h-4 w-4" />
            <span>{title}</span>
          </div>
          {previous !== undefined && <Delta previous={previous} current={current} />}
        </div>
        <p className="mt-2 text-2xl font-bold">
          {current === null || current === undefined ? "—" : current}
        </p>
        {previous !== undefined && previous !== null && (
          <p className="mt-1 text-xs text-muted-foreground">
            Previous: {previous}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

const MILESTONE_LABELS: Record<string, { label: string; icon: typeof FileText }> = {
  resume_uploaded: { label: "Resume uploaded", icon: FileText },
  resume_analyzed: { label: "Resume analyzed", icon: Target },
  job_analyzed: { label: "Job analysis completed", icon: FolderOpen },
  resume_tailored: { label: "Resume tailored", icon: Wand2 },
  cover_letter_generated: { label: "Cover letter generated", icon: Mail },
  export_generated: { label: "Export generated", icon: FileText },
  login: { label: "Signed in", icon: TrendingUp },
};

export function CareerInsightPage() {
  const overview = useDashboardOverview();
  const trends = useDashboardTrends(12);
  const statistics = useQuery({
    queryKey: ["dashboard", "statistics"],
    queryFn: dashboardApi.statistics,
  });
  const [expanded, setExpanded] = useState(false);

  const latestAts = overview.data?.statistics.average_ats_score ?? null;
  const resumeCount = overview.data?.statistics.total_resumes ?? null;
  const tailoringCount = statistics.data?.total_tailoring_sessions ?? null;
  const avgMatch = statistics.data?.average_job_match_score ?? null;
  const improvementPct = overview.data?.statistics.improvement_percentage ?? null;
  const highestAts = overview.data?.statistics.highest_ats_score ?? null;

  const trendPoints = trends.data?.points ?? [];
  const chartData = trendPoints.map((p) => ({
    timestamp: new Date(p.timestamp).getTime(),
    score: p.average_resume_score ?? 0,
    match: p.average_job_match_score ?? 0,
  }));

  // Previous values
  const firstTrend = trendPoints.length > 0 ? trendPoints[0] : null;
  const lastTrend = trendPoints.length > 0 ? trendPoints[trendPoints.length - 1] : null;

  const atsCurrentForDelta = trends.isSuccess && trendPoints.length >= 2 ? lastTrend?.average_resume_score ?? null : null;
  const atsPreviousForDelta = trends.isSuccess && trendPoints.length >= 2 ? firstTrend?.average_resume_score ?? null : null;

  const matchCurrentForDelta = trends.isSuccess && trendPoints.length >= 2 ? lastTrend?.average_job_match_score ?? null : null;
  const matchPreviousForDelta = trends.isSuccess && trendPoints.length >= 2 ? firstTrend?.average_job_match_score ?? null : null;

  const activity = overview.data?.unread_notifications ?? [];
  const meaningful = activity.filter((n) => {
    const key = n.activity_type as string;
    return MILESTONE_LABELS[key] !== undefined;
  });
  const visibleMilestones = expanded ? meaningful : meaningful.slice(0, INITIAL_MILESTONES);
  const hasMoreMilestones = meaningful.length > INITIAL_MILESTONES;
  const hasAnyData = resumeCount !== null || latestAts !== null || chartData.length > 0;

  return (
    <div className="space-y-4 p-4 sm:p-6">
      <div className="flex items-center gap-2">
        <TrendingUp className="h-5 w-5 text-primary" />
        <h1 className="text-xl font-bold text-foreground">Career Insight</h1>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="ATS Score" current={latestAts} previous={atsPreviousForDelta} icon={TrendingUp} />
        <StatCard title="Match Score" current={avgMatch} previous={matchPreviousForDelta} icon={Target} />
        <StatCard title="Resumes" current={resumeCount} icon={FileText} />
        <StatCard title="Tailoring Sessions" current={tailoringCount} icon={Wand2} />
      </div>

      {/* Secondary improvement badges */}
      <div className="flex flex-wrap gap-2">
        {improvementPct !== null && improvementPct !== 0 && (
          <Badge variant="secondary" className="gap-1">
            <TrendingUp className="h-3.5 w-3.5" />
            {improvementPct > 0 ? "+" : ""}
            {improvementPct}% overall improvement
          </Badge>
        )}
        {highestAts !== null && (
          <Badge variant="secondary" className="gap-1">
            Highest ATS: {highestAts}
          </Badge>
        )}
      </div>

      {/* Improvement Trend */}
      <Card>
        <CardHeader>
          <CardTitle>Progression</CardTitle>
        </CardHeader>
        <CardContent>
          {trends.isLoading ? (
            <Skeleton className="h-[200px] w-full" />
          ) : trends.isError ? (
            <ErrorState error={trends.error} onRetry={() => trends.refetch()} />
          ) : chartData.length === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="No trend data yet"
              description="Trends build up automatically as you analyze resumes and jobs over time."
            />
          ) : (
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={chartData} margin={{ top: 8, right: 8, left: -20, bottom: 0 }}>
                <CartesianGrid stroke="hsl(var(--border))" vertical={false} />
                <XAxis
                  dataKey="timestamp"
                  scale="time"
                  domain={["auto", "auto"]}
                  tickFormatter={(v) => formatAxisLabel(v as number)}
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                />
                <YAxis
                  tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                  axisLine={false}
                  tickLine={false}
                  domain={[0, 100]}
                />
                <Tooltip
                  labelFormatter={(v) => formatTooltipLabel(v as number)}
                  contentStyle={{
                    background: "hsl(var(--card))",
                    border: "1px solid hsl(var(--border))",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Line type="monotone" dataKey="score" stroke="hsl(var(--primary))" strokeWidth={2} dot={{ r: 3 }} name="Resume score" />
                <Line type="monotone" dataKey="match" stroke="hsl(var(--secondary))" strokeWidth={1.5} strokeDasharray="4 4" dot={false} name="Job match" />
              </LineChart>
            </ResponsiveContainer>
          )}
        </CardContent>
      </Card>

      {/* Career Milestones */}
      <Card>
        <CardHeader>
          <CardTitle>Career Milestones</CardTitle>
        </CardHeader>
        <CardContent>
          {overview.isLoading ? (
            <Skeleton className="h-[120px] w-full" />
          ) : meaningful.length === 0 ? (
            <EmptyState
              icon={TrendingUp}
              title="No milestones yet"
              description="Upload and analyze a resume to start tracking your progress."
            />
          ) : (
            <>
              <div className="space-y-3">
                {visibleMilestones.map((n) => {
                  const meta = MILESTONE_LABELS[n.activity_type] ?? MILESTONE_LABELS.login;
                  const Icon = meta.icon;
                  return (
                    <div key={n.id} className="flex items-start gap-3">
                      <div className="mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-primary/10">
                        <Icon className="h-3.5 w-3.5 text-primary" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <p className="text-sm">{meta.label}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(n.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric", hour: "numeric" })}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
              {hasMoreMilestones && (
                <div className="flex justify-center pt-3">
                  <button
                    type="button"
                    className="inline-flex items-center gap-1 rounded-md px-2 py-1 text-xs text-muted-foreground hover:bg-muted hover:text-foreground"
                    onClick={() => setExpanded((e) => !e)}
                  >
                    {expanded ? (
                      <>Show less <ChevronUp className="h-3.5 w-3.5" /></>
                    ) : (
                      <>Show more <ChevronDown className="h-3.5 w-3.5" /></>
                    )}
                  </button>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>

      {/* Empty state when no data at all */}
      {!overview.isLoading && !hasAnyData && meaningful.length === 0 && (
        <Card>
          <CardContent className="pt-6">
            <EmptyState
              icon={TrendingUp}
              title="Start your career journey"
              description="Upload a resume to begin receiving AI-powered insights, scores, and suggestions."
            />
          </CardContent>
        </Card>
      )}
    </div>
  );
}