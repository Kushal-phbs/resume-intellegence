import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, CartesianGrid } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { EmptyState } from "@/components/common/EmptyState";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { TrendingUp } from "lucide-react";
import { useDashboardTrends } from "@/hooks/useDashboard";
import { formatDate } from "@/lib/utils";

export function TrendsChart() {
  const { data, isLoading, isError, error, refetch } = useDashboardTrends(12);

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
              data={data.points.map((p) => ({
                label: formatDate(p.timestamp),
                score: p.average_resume_score ?? 0,
                match: p.average_job_match_score ?? 0,
              }))}
              margin={{ top: 8, right: 8, left: -20, bottom: 0 }}
            >
              <CartesianGrid stroke="hsl(var(--border))" vertical={false} />
              <XAxis dataKey="label" tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: "hsl(var(--muted-foreground))", fontSize: 11 }} axisLine={false} tickLine={false} domain={[0, 100]} />
              <Tooltip
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
