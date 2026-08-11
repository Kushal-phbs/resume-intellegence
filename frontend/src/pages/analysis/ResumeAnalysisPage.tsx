import { resumesApi } from "@/api/resumes";
import { InsightList } from "@/components/analysis/InsightList";
import { ScoreRing } from "@/components/analysis/ScoreRing";
import { KeywordChips, SkillChips } from "@/components/analysis/SkillKeywordChips";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { ROUTES } from "@/constants/routes";
import { useAnalysisHistory, useDeleteAnalysis, useLatestAnalysis, useRunAnalysis } from "@/hooks/useAnalysis";
import { useResume } from "@/hooks/useResumes";
import { formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  CheckCircle2,
  Download,
  FileWarning,
  History as HistoryIcon,
  Lightbulb,
  RotateCcw,
  Sparkles,
  Trash2,
  XCircle,
} from "lucide-react";
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

const STATUS_VARIANT: Record<string, "default" | "success" | "destructive" | "muted"> = {
  pending: "muted",
  processing: "default",
  completed: "success",
  failed: "destructive",
};

export function ResumeAnalysisPage() {
  const { id } = useParams<{ id: string }>();
  const resumeId = id as string;
  const { data: resume } = useResume(resumeId);
  const latest = useLatestAnalysis(resumeId);
  const history = useAnalysisHistory(resumeId);
  const runAnalysis = useRunAnalysis(resumeId);
  const deleteAnalysis = useDeleteAnalysis(resumeId);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const latestError = latest.error as {
    response?: { status?: number; data?: { detail?: string } };
  };

  // Only treat the specific backend response "Analysis not found" as the
  // empty-state case. Other 404s (for example "Resume not found") should
  // remain visible as real errors.
  const noAnalysisYet =
    latest.isError &&
    latestError?.response?.status === 404 &&
    latestError?.response?.data?.detail === "Analysis not found";

  return (
    <div className="max-w-3xl space-y-6">
      <Link
        to={ROUTES.resumeDetail(resumeId)}
        className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Resume
      </Link>

      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Resume Analysis</h1>
          <p className="mt-1 text-sm text-muted-foreground">{resume?.title ?? "Loading resume…"}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => resumesApi.download(resumeId)}>
            <Download className="h-4 w-4" />
            Original File
          </Button>
          <Button onClick={() => runAnalysis.mutate()} isLoading={runAnalysis.isPending}>
            <RotateCcw className="h-4 w-4" />
            {latest.data ? "Re-run Analysis" : "Run Analysis"}
          </Button>
        </div>
      </div>

      {runAnalysis.isError ? <ErrorState error={runAnalysis.error} /> : null}
      {deleteAnalysis.isError ? <ErrorState error={deleteAnalysis.error} /> : null}

      {latest.isLoading ? (
        <Skeleton className="h-64 w-full" />
      ) : noAnalysisYet ? (
        <EmptyState
          icon={Sparkles}
          title="No analysis yet"
          description="Run AI analysis to get an ATS score, strengths, weaknesses, and improvement suggestions for this resume."
          actionLabel="Run Analysis"
          onAction={() => runAnalysis.mutate()}
        />
      ) : latest.isError ? (
        <ErrorState error={latest.error} onRetry={() => latest.refetch()} />
      ) : latest.data?.analysis_status === "failed" ? (
        <Card>
          <CardContent className="flex flex-col items-center gap-3 p-8 text-center">
            <FileWarning className="h-8 w-8 text-destructive" />
            <p className="text-sm font-semibold text-destructive">Analysis failed</p>
            <p className="text-sm text-muted-foreground">{latest.data.error_message ?? "Unknown error"}</p>
            <Button size="sm" onClick={() => runAnalysis.mutate()} isLoading={runAnalysis.isPending}>
              Try again
            </Button>
          </CardContent>
        </Card>
      ) : latest.data ? (
        <>
          {/* Scores */}
          <Card>
            <CardContent className="flex flex-wrap items-center justify-around gap-6 p-6">
              <ScoreRing value={latest.data.resume_score} label="Resume Score" colorClass="stroke-primary" />
              <ScoreRing value={latest.data.ats_score} label="ATS Score" colorClass="stroke-secondary" />
              <Badge variant={STATUS_VARIANT[latest.data.analysis_status]}>{latest.data.analysis_status}</Badge>
            </CardContent>
          </Card>

          {/* Strengths / Weaknesses / Recommendations */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <Card>
              <CardHeader><CardTitle className="text-success">Strengths</CardTitle></CardHeader>
              <CardContent>
                <InsightList icon={CheckCircle2} items={latest.data.strengths} tone="success" emptyLabel="None detected." />
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-destructive">Weaknesses</CardTitle></CardHeader>
              <CardContent>
                <InsightList icon={XCircle} items={latest.data.weaknesses} tone="destructive" emptyLabel="None detected." />
              </CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle className="text-primary">Recommendations</CardTitle></CardHeader>
              <CardContent>
                <InsightList icon={Lightbulb} items={latest.data.recommendations} tone="primary" emptyLabel="None yet." />
              </CardContent>
            </Card>
          </div>

          {/* Skills & Keywords */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <Card>
              <CardHeader><CardTitle>Extracted Skills ({latest.data.skills.length})</CardTitle></CardHeader>
              <CardContent><SkillChips skills={latest.data.skills} /></CardContent>
            </Card>
            <Card>
              <CardHeader><CardTitle>Extracted Keywords ({latest.data.keywords.length})</CardTitle></CardHeader>
              <CardContent><KeywordChips keywords={latest.data.keywords.map((k) => k.keyword)} /></CardContent>
            </Card>
          </div>
        </>
      ) : null}

      {/* History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <HistoryIcon className="h-4 w-4" />
            Analysis History
          </CardTitle>
        </CardHeader>
        <CardContent>
          {history.isLoading ? (
            <Skeleton className="h-24 w-full" />
          ) : history.isError ? (
            <ErrorState error={history.error} onRetry={() => history.refetch()} />
          ) : !history.data || history.data.length === 0 ? (
            <p className="text-sm text-muted-foreground">No past analyses recorded.</p>
          ) : (
            <div className="space-y-2">
              {history.data.map((h) => (
                <div key={h.id} className="flex items-center gap-3 rounded-md bg-muted/50 p-3 text-sm">
                  <Badge variant={STATUS_VARIANT[h.analysis_status]}>{h.analysis_status}</Badge>
                  <span className="flex-1 text-muted-foreground">{formatDate(h.created_at)}</span>
                  {h.resume_score !== null && <span className="font-semibold">{h.resume_score}/100</span>}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 text-muted-foreground hover:text-destructive"
                    aria-label="Delete analysis record"
                    isLoading={deletingId === h.id && deleteAnalysis.isPending}
                    onClick={() => {
                      setDeletingId(h.id);
                      deleteAnalysis.mutate(h.id, { onSettled: () => setDeletingId(null) });
                    }}
                  >
                    {!(deletingId === h.id && deleteAnalysis.isPending) && <Trash2 className="h-3.5 w-3.5" />}
                  </Button>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
