import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { getApiErrorMessage } from "@/api/client";
import { tailoringApi } from "@/api/tailoring";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorMessage } from "@/components/common/ErrorMessage";
import { ErrorState } from "@/components/common/ErrorState";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { useResumes } from "@/hooks/useResumes";
import {
  useCreateTailoring,
  useTailoringCoverLetter,
  useTailoringHistory,
  useTailoringResumeVersion,
} from "@/hooks/useTailoring";
import { formatDate } from "@/lib/utils";
import type {
  ExportFormat,
  TailoringSummaryResponse
} from "@/types/tailoring";
import {
  CheckCircle2,
  ChevronRight,
  Download, FileText,
  Info, Play,
  Plus,
  Wand2,
  X,
} from "lucide-react";

/* ─── Status badge ─── */
const STATUS_VARIANT: Record<string, "default" | "success" | "destructive" | "muted"> = {
  pending: "muted", processing: "default", completed: "success", failed: "destructive",
};

/* ─── Tailoring run form ─── */
const uuidSchema = z.string().uuid("Must be a valid UUID");
const schema = z.object({
  resume_id: uuidSchema,
  job_id: uuidSchema,
});
type FormValues = z.infer<typeof schema>;

function TailoringForm({ onSuccess }: { onSuccess: (result: TailoringSummaryResponse) => void }) {
  const { data: resumes } = useResumes();
  const createTailoring = useCreateTailoring();

  const {
    register, handleSubmit, formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema) });

  const onSubmit = (values: FormValues) =>
    createTailoring.mutate(
      { resumeId: values.resume_id, jobId: values.job_id },
      { onSuccess: (data) => onSuccess(data) }
    );

  return (
    <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
      <div className="flex items-start gap-2 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
        <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
        <span>
          The backend has no endpoint to create a job description from pasted text.
          Tailoring requires an existing <code className="rounded bg-muted px-1">job_id</code> (a
          JobDescription UUID already in the database). Paste one below.
        </span>
      </div>

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

      {createTailoring.isError && (
        <ErrorMessage message={getApiErrorMessage(createTailoring.error)} />
      )}

      <Button type="submit" isLoading={createTailoring.isPending}>
        <Play className="h-4 w-4" />
        Tailor Resume
      </Button>
    </form>
  );
}

/* ─── Helper: extract human-readable text from a recommendation object ─── */
function extractRecommendationText(rec: Record<string, unknown>): string {
  // The recommendation can be stored under various keys
  const text: unknown =
    rec.recommendation ??
    rec.text ??
    rec.value ??
    rec.message ??
    rec.description;
  if (typeof text === "string") return text;
  // Fallback: try to stringify just the first meaningful value
  const values = Object.values(rec).filter(
    (v): v is string => typeof v === "string" && v.length > 0
  );
  return values.length > 0 ? values[0] : JSON.stringify(rec);
}

/* ─── Result panel shown after a successful tailoring ─── */
function TailoringResult({
  result, onClose,
}: {
  result: TailoringSummaryResponse;
  onClose: () => void;
}) {
  const { session, resume_version, cover_letter } = result;

  const FORMATS: ExportFormat[] = ["md", "docx", "pdf"];

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <CheckCircle2 className="h-5 w-5 text-success" />
          <span className="font-semibold">Tailoring complete</span>
          <Badge variant="success">{session.status}</Badge>
        </div>
        <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close result">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {/* Resume version */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-4 w-4" /> Tailored Resume
            <Badge variant="default" className="ml-auto">ATS {resume_version.ats_score}</Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          {resume_version.professional_summary && (
            <div>
              <p className="mb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Professional Summary</p>
              <p className="text-sm">{resume_version.professional_summary}</p>
            </div>
          )}

          {resume_version.recommendations_json.length > 0 && (
            <div>
              <p className="mb-1.5 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                AI Recommendations ({resume_version.recommendations_json.length})
              </p>
              <ul className="space-y-1.5">
                {resume_version.recommendations_json.map((rec, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <CheckCircle2 className="mt-0.5 h-3.5 w-3.5 shrink-0 text-primary" />
                    <span>{extractRecommendationText(rec)}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Export */}
          <div>
            <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Export Resume</p>
            <div className="flex flex-wrap gap-2">
              {FORMATS.map((fmt) => (
                <Button
                  key={fmt}
                  variant="outline"
                  size="sm"
                  onClick={() => tailoringApi.exportResume(resume_version.id, fmt)}
                >
                  <Download className="h-3.5 w-3.5" />
                  .{fmt.toUpperCase()}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cover letter */}
      {cover_letter && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Cover Letter — {cover_letter.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="text-sm">{cover_letter.greeting}</p>
            <p className="text-sm">{cover_letter.introduction}</p>
            <p className="text-sm">{cover_letter.body}</p>
            <p className="text-sm">{cover_letter.closing}</p>

            <div>
              <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Export Cover Letter</p>
              <div className="flex flex-wrap gap-2">
                {FORMATS.map((fmt) => (
                  <Button
                    key={fmt}
                    variant="outline"
                    size="sm"
                    onClick={() => tailoringApi.exportCoverLetter(cover_letter.id as string, fmt)}
                  >
                    <Download className="h-3.5 w-3.5" />
                    .{fmt.toUpperCase()}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/* ─── Tailoring session detail panel (for history items) ─── */
function SessionDetail({ sessionId, onClose }: { sessionId: string; onClose: () => void }) {
  const rv = useTailoringResumeVersion(sessionId);
  const cl = useTailoringCoverLetter(sessionId);
  const FORMATS: ExportFormat[] = ["md", "docx", "pdf"];

  if (rv.isLoading || cl.isLoading) return <Skeleton className="h-48 w-full" />;
  if (rv.isError) return <ErrorState error={rv.error} onRetry={() => rv.refetch()} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <span className="font-semibold text-sm">Session results</span>
        <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
          <X className="h-4 w-4" />
        </Button>
      </div>

      {rv.data && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <FileText className="h-4 w-4" /> Tailored Resume
              <Badge variant="default" className="ml-auto">ATS {rv.data.ats_score}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {rv.data.professional_summary && (
              <p className="text-sm">{rv.data.professional_summary}</p>
            )}
            <div className="flex flex-wrap gap-2">
              {FORMATS.map((fmt) => (
                <Button key={fmt} variant="outline" size="sm" onClick={() => tailoringApi.exportResume(rv.data!.id, fmt)}>
                  <Download className="h-3.5 w-3.5" />.{fmt.toUpperCase()}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {cl.data && (
        <Card>
          <CardHeader><CardTitle className="text-sm">Cover Letter — {cl.data.title}</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            <p className="text-sm">{cl.data.introduction}</p>
            <div className="flex flex-wrap gap-2">
              {FORMATS.map((fmt) => (
                <Button key={fmt} variant="outline" size="sm" onClick={() => tailoringApi.exportCoverLetter(cl.data!.id as string, fmt)}>
                  <Download className="h-3.5 w-3.5" />.{fmt.toUpperCase()}
                </Button>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

/* ─── Page ─── */
export function TailoringPage() {
  const history = useTailoringHistory();
  const [showForm, setShowForm] = useState(false);
  const [freshResult, setFreshResult] = useState<TailoringSummaryResponse | null>(null);
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

  return (
    <div className="max-w-3xl space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Resume Tailoring</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            AI-powered tailoring of your resume against a specific job description.
          </p>
        </div>
        <Button onClick={() => { setShowForm((s) => !s); setFreshResult(null); }}>
          {showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {showForm ? "Close" : "New Tailoring"}
        </Button>
      </div>

      {showForm && !freshResult && (
        <Card>
          <CardHeader><CardTitle>Tailor a Resume</CardTitle></CardHeader>
          <CardContent>
            <TailoringForm onSuccess={(r) => { setFreshResult(r); setShowForm(false); }} />
          </CardContent>
        </Card>
      )}

      {freshResult && (
        <Card>
          <CardContent className="p-5">
            <TailoringResult result={freshResult} onClose={() => setFreshResult(null)} />
          </CardContent>
        </Card>
      )}

      {selectedSessionId && !freshResult && (
        <Card>
          <CardContent className="p-5">
            <SessionDetail sessionId={selectedSessionId} onClose={() => setSelectedSessionId(null)} />
          </CardContent>
        </Card>
      )}

      {/* History */}
      <Card>
        <CardHeader><CardTitle>History</CardTitle></CardHeader>
        <CardContent>
          {history.isLoading ? (
            <div className="space-y-2">
              {Array.from({ length: 3 }).map((_, i) => <Skeleton key={i} className="h-14 w-full" />)}
            </div>
          ) : history.isError ? (
            <ErrorState error={history.error} onRetry={() => history.refetch()} />
          ) : !history.data || history.data.length === 0 ? (
            <EmptyState
              icon={Wand2}
              title="No tailoring sessions yet"
              description="Create your first tailored resume to see it here."
              actionLabel="Start Tailoring"
              onAction={() => setShowForm(true)}
            />
          ) : (
            <div className="space-y-2">
              {history.data.map((s) => (
                <button
                  key={s.id}
                  onClick={() => {
                    setSelectedSessionId(selectedSessionId === s.id ? null : s.id);
                    setFreshResult(null);
                  }}
                  className="flex w-full items-center gap-3 rounded-md bg-muted/50 p-3 text-left transition-colors hover:bg-muted"
                >
                  <Badge variant={STATUS_VARIANT[s.status]}>{s.status}</Badge>
                  <span className="flex-1 text-sm text-muted-foreground">{formatDate(s.created_at)}</span>
                  <span className="text-xs text-muted-foreground font-mono truncate max-w-[120px]">{s.job_description_id.slice(0, 8)}…</span>
                  <ChevronRight className={`h-4 w-4 text-muted-foreground transition-transform ${selectedSessionId === s.id ? "rotate-90" : ""}`} />
                </button>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
