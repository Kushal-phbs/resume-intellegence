import { JobAnalysisResultView, STATUS_VARIANT } from "@/components/analysis/JobAnalysisResultView";
import { ErrorState } from "@/components/common/ErrorState";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ROUTES } from "@/constants/routes";
import { useJobAnalysis } from "@/hooks/useJobAnalysis";
import { formatDate } from "@/lib/utils";
import { ArrowLeft } from "lucide-react";
import { Link, useParams } from "react-router-dom";

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

      <JobAnalysisResultView data={data} />
    </div>
  );
}
