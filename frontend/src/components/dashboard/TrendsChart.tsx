import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboardTrends } from "@/hooks/useDashboard";
import { TrendingUp } from "lucide-react";
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

function formatAxisLabel(ts: number, spanHours: number, spanDays: number): string {
  const d = new Date(ts);
  if (spanHours <= 48) {
    return d.toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
  }
  if (spanDays <= 14) {
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
  if (spanDays <= 90) {
    return d.toLocaleDateString("en-US", { month: "short", day: "numeric" });
  }
  return d.toLocaleDateString("en-US", { month: "short" });
}

function formatTooltipLabel(ts: number): string {
  return new Date(ts).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export function TrendsChart() {
  const { data, isLoading, isError, error, refetch } = useDashboardTrends(12);

  const chartData = data?.points.map((p) => ({
    timestamp: new Date(p.timestamp).getTime(),
    score: p.average_resume_score ?? 0,
    match: p.average_job_match_score ?? 0,
  }));

  let spanHours = 0;
  let spanDays = 0;
  let tickCount: number | undefined;

  if (chartData && chartData.length >= 2) {
    const timestamps = chartData.map((p) => p.timestamp);
    const minTs = Math.min(...timestamps);
    const maxTs = Math.max(...timestamps);
    spanHours = (maxTs - minTs) / (1000 * 60 * 60);
    spanDays = spanHours / 24;
  }

  if (spanDays > 14) {
    tickCount = 6;
  } else if (spanDays > 90) {
    tickCount = 6;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>ATS Score Trend</CardTitle>
      </CardHeader>
      <CardContent>
        {isLoading ? (
          <Skeleton className="h-[200px] w-full" />
        ) : isError ? (
          <ErrorState error={error} onRetry={() => refetch()} />
        ) : !data || data.points.length === 0 ? (
          <EmptyState
            icon={TrendingUp}
            title="No trend data yet"
            description="Trends build up automatically as you upload and analyze resumes over time."
          />
        ) : (
          <ResponsiveContainer width="100%" height={200}>
            <LineChart
              data={chartData}
              margin={{ top: 8, right: 8, left: -20, bottom: 0 }}
            >
              <CartesianGrid stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="timestamp"
                scale="time"
                domain={["auto", "auto"]}
                tickFormatter={(v) => formatAxisLabel(v as number, spanHours, spanDays)}
                tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }}
                axisLine={false}
                tickLine={false}
                tickCount={tickCount}
              />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} />
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
  );
}