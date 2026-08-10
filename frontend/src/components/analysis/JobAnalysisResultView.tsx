import { CheckCircle2, Hash, Lightbulb, XCircle } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScoreRing } from "@/components/analysis/ScoreRing";
import { InsightList } from "@/components/analysis/InsightList";
import type { JobAnalysisResponse } from "@/types/jobAnalysis";

const STATUS_VARIANT: Record<string, "default" | "success" | "destructive" | "muted"> = {
  pending: "muted",
  processing: "default",
  completed: "success",
  failed: "destructive",
};

export function JobAnalysisResultView({ data }: { data: JobAnalysisResponse }) {
  if (data.analysis_status === "failed") {
    return (
      <Card>
        <CardContent className="p-6 text-center">
          <p className="text-sm font-semibold text-destructive">Analysis failed</p>
          <p className="mt-1 text-sm text-muted-foreground">{data.error_message ?? "Unknown error"}</p>
        </CardContent>
      </Card>
    );
  }

  return (
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
  );
}

export { STATUS_VARIANT };