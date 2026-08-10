import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Link } from "react-router-dom";
import { Briefcase, Play, Info, ChevronRight } from "lucide-react";
import { useJobAnalysisHistory, useRunJobAnalysis } from "@/hooks/useJobAnalysis";
import { useResumes } from "@/hooks/useResumes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { getApiErrorMessage } from "@/api/client";
import { formatDate } from "@/lib/utils";
import { ROUTES } from "@/constants/routes";

const STATUS_VARIANT: Record<string, "default" | "success" | "destructive" | "muted"> = {
  pending: "muted",
  processing: "default",
  completed: "success",
  failed: "destructive",
};

const uuidSchema = z.string().uuid("Must be a valid UUID");
const schema = z.object({
  resume_id: uuidSchema,
  job_id: uuidSchema,
});
type FormValues = z.infer<typeof schema>;

export function JobAnalysisPage() {
  const history = useJobAnalysisHistory();
  const { data: resumes } = useResumes();
  const runJobAnalysis = useRunJobAnalysis();
  const [showForm, setShowForm] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (values: FormValues) =>
    runJobAnalysis.mutate({ resumeId: values.resume_id, jobId: values.job_id });

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Job Analysis</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Match a resume against a job description and see where it stands.
          </p>
        </div>
        <Button onClick={() => setShowForm((s) => !s)}>
          <Play className="h-4 w-4" />
          {showForm ? "Close" : "Run New Analysis"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader><CardTitle>Run Job Analysis</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-start gap-2 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
              <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>
                The backend has no endpoint to create a job description from pasted text — job analysis
                requires an existing <code className="rounded bg-muted px-1">job_id</code> (a JobDescription
                UUID already present in the database). Paste one below.
              </span>
            </div>

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <div>
                <Label htmlFor="resume_id">Resume</Label>
                {resumes && resumes.items.length > 0 ? (
                  <select
                    id="resume_id"
                    {...register("resume_id")}
                    className="flex h-10 w-full rounded-md border border-border bg-background px-3 text-sm outline-none focus-visible:border-primary"
                  >
                    <option value="">Select a resume…</option>
                    {resumes.items.map((r) => (
                      <option key={r.id} value={r.id}>{r.title}</option>
                    ))}
                  </select>
                ) : (
                  <Input id="resume_id" placeholder="Resume UUID" {...register("resume_id")} />
                )}
                {errors.resume_id && <p className="mt-1 text-xs text-destructive">{errors.resume_id.message}</p>}
              </div>

              <div>
                <Label htmlFor="job_id">Job Description ID</Label>
                <Input id="job_id" placeholder="Existing JobDescription UUID" {...register("job_id")} />
                {errors.job_id && <p className="mt-1 text-xs text-destructive">{errors.job_id.message}</p>}
              </div>

              {runJobAnalysis.isError && <ErrorMessage message={getApiErrorMessage(runJobAnalysis.error)} />}

              <Button type="submit" isLoading={runJobAnalysis.isPending}>
                <Play className="h-4 w-4" />
                Run Analysis
              </Button>
            </form>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>History</CardTitle></CardHeader>
        <CardContent>
          {history.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-16 w-full" />)}
            </div>
          ) : history.isError ? (
            <ErrorState error={history.error} onRetry={() => history.refetch()} />
          ) : history.data && history.data.length === 0 ? (
            <EmptyState
              icon={Briefcase}
              title="No job analyses yet"
              description="Run your first job match analysis to see how your resume compares."
              actionLabel="Run New Analysis"
              onAction={() => setShowForm(true)}
            />
          ) : (
            <div className="space-y-2">
              {history.data?.map((h) => (
                <Link
                  key={h.id}
                  to={ROUTES.jobAnalysisDetail(h.id)}
                  className="flex items-center gap-3 rounded-md bg-muted/50 p-3 transition-transform hover:translate-x-0.5 hover:bg-muted"
                >
                  <Badge variant={STATUS_VARIANT[h.analysis_status]}>{h.analysis_status}</Badge>
                  <span className="flex-1 text-sm text-muted-foreground">{formatDate(h.created_at)}</span>
                  {h.match_score !== null && (
                    <span className="text-sm font-semibold">{h.match_score}% match</span>
                  )}
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
