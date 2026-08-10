import { Link, useParams } from "react-router-dom";
import { ArrowLeft, CheckCircle2, XCircle, Lightbulb, Hash } from "lucide-react";
import { useJobAnalysis } from "@/hooks/useJobAnalysis";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { ScoreRing } from "@/components/analysis/ScoreRing";
import { InsightList } from "@/components/analysis/InsightList";
import { formatDate } from "@/lib/utils";
import { ROUTES } from "@/constants/routes";

const STATUS_VARIANT: Record<string, "default" | "success" | "destructive" | "muted"> = {
  pending: "muted",
  processing: "default",
  completed: "success",
  failed: "destructive",
};

export function JobAnalysisDetailPage() {
  const { id } = useParams<{ id: string }>();
  const { data, isLoading, isError, error, refetch } = useJobAnalysis(id);

  if (isLoading) {
    return (
      <div className="max-w-3xl space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-64 w-full" />
      </div>
    );
  }

  if (isError || !data) {
    return <ErrorState error={error} onRetry={() => refetch()} />;
  }

  return (
    <div className="max-w-3xl space-y-6">
      <Link to={ROUTES.jobAnalysis} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        Back to Job Analysis
      </Link>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Job Match Analysis</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Run on {formatDate(data.created_at)}
          </p>
        </div>
        <Badge variant={STATUS_VARIANT[data.analysis_status]}>{data.analysis_status}</Badge>
      </div>

      {data.analysis_status === "failed" ? (
        <Card>
          <CardContent className="p-6 text-center">
            <p className="text-sm font-semibold text-destructive">Analysis failed</p>
            <p className="mt-1 text-sm text-muted-foreground">{data.error_message ?? "Unknown error"}</p>
          </CardContent>
        </Card>
      ) : (
        <>
          <Card>
            <CardContent className="flex flex-wrap items-center justify-around gap-6 p-6">
              <ScoreRing value={data.match_score} label="Match Score" colorClass="stroke-primary" />
              <ScoreRing value={data.ats_match_score} label="ATS Match" colorClass="stroke-secondary" />
            </CardContent>
          </Card>

          {data.summary && (
            <Card>
              <CardHeader><CardTitle>Summary</CardTitle></CardHeader>
              <CardContent><p className="text-sm text-muted-foreground">{data.summary}</p></CardContent>
            </Card>
          )}

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader><CardTitle className="text-success">Strengths</CardTitle></CardHeader>
              <CardContent>
                <InsightList icon={CheckCircle2} items={data.strengths} tone="success" emptyLabel="None detected." />
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-destructive">Weaknesses</CardTitle></CardHeader>
              <CardContent>
                <InsightList icon={XCircle} items={data.weaknesses} tone="destructive" emptyLabel="None detected." />
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-primary">Recommendations</CardTitle></CardHeader>
              <CardContent>
                <InsightList icon={Lightbulb} items={data.recommendations} tone="primary" emptyLabel="None yet." />
              </CardContent>
            </Card>
          </div>

          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader><CardTitle>Matched Skills ({data.matched_skills.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {data.matched_skills.length === 0 ? (
                    <p className="text-sm text-muted-foreground">None found.</p>
                  ) : (
                    data.matched_skills.map((s) => <Badge key={s.id} variant="success">{s.skill_name}</Badge>)
                  )}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Missing Skills ({data.missing_skills.length})</CardTitle></CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {data.missing_skills.length === 0 ? (
                    <p className="text-sm text-muted-foreground">None — great coverage!</p>
                  ) : (
                    data.missing_skills.map((s) => <Badge key={s.id} variant="destructive">{s.skill_name}</Badge>)
                  )}
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-1.5">
                  <Hash className="h-3.5 w-3.5" />
                  Keyword Matches ({data.keyword_matches.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex flex-wrap gap-1.5">
                  {data.keyword_matches.length === 0 ? (
                    <p className="text-sm text-muted-foreground">None found.</p>
                  ) : (
                    data.keyword_matches.map((k) => <Badge key={k.id} variant="muted">{k.keyword}</Badge>)
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
