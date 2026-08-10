import { useState } from "react";
import { useNavigate, useParams, Link } from "react-router-dom";
import { FileText, Download, Trash2, Sparkles, Star, ArrowLeft, Info } from "lucide-react";
import { useResume, useDeleteResume } from "@/hooks/useResumes";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ErrorState } from "@/components/common/ErrorState";
import { resumesApi } from "@/api/resumes";
import { formatDate } from "@/lib/utils";
import { ROUTES } from "@/constants/routes";

export function ResumeDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: resume, isLoading, isError, error, refetch } = useResume(id);
  const deleteResume = useDeleteResume();
  const [confirmDelete, setConfirmDelete] = useState(false);

  if (isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-48" />
        <Skeleton className="h-40 w-full" />
      </div>
    );
  }

  if (isError || !resume) {
    return <ErrorState error={error} onRetry={() => refetch()} />;
  }

  const handleDelete = () => {
    deleteResume.mutate(resume.id, { onSuccess: () => navigate(ROUTES.resumes) });
  };

  return (
    <div className="max-w-2xl space-y-6">
      <Link to={ROUTES.resumes} className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="h-4 w-4" />
        Back to Resumes
      </Link>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-start gap-3">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-muted">
                <FileText className="h-5 w-5 text-muted-foreground" />
              </div>
              <div>
                <CardTitle className="text-lg">{resume.title}</CardTitle>
                <p className="mt-1 text-xs text-muted-foreground">
                  Uploaded {formatDate(resume.created_at)} · Updated {formatDate(resume.updated_at)}
                </p>
              </div>
            </div>
            {resume.is_primary && (
              <Badge variant="default">
                <Star className="h-3 w-3" fill="currentColor" /> Primary
              </Badge>
            )}
          </div>
        </CardHeader>

        <CardContent className="space-y-4">
          {/* NOTE: the backend doesn't expose extracted text content for an
              existing resume via a GET endpoint (only right after upload) —
              so "preview" here is limited to metadata + file download. */}
          <div className="flex items-start gap-2 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
            <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" />
            <span>
              Full text preview isn't available for previously uploaded resumes — the backend only
              returns extracted content at upload time. Use Download to view the original file.
            </span>
          </div>

          <div className="flex flex-wrap gap-2">
            <a href={resumesApi.downloadUrl(resume.id)} target="_blank" rel="noreferrer">
              <Button variant="outline">
                <Download className="h-4 w-4" />
                Download
              </Button>
            </a>
            <Button onClick={() => navigate(ROUTES.resumeAnalysis(resume.id))}>
              <Sparkles className="h-4 w-4" />
              View Analysis
            </Button>

            {!confirmDelete ? (
              <Button variant="ghost" className="text-destructive hover:bg-destructive/10" onClick={() => setConfirmDelete(true)}>
                <Trash2 className="h-4 w-4" />
                Delete
              </Button>
            ) : (
              <div className="flex items-center gap-2">
                <span className="text-xs text-muted-foreground">Delete this resume?</span>
                <Button variant="destructive" size="sm" onClick={handleDelete} isLoading={deleteResume.isPending}>
                  Confirm
                </Button>
                <Button variant="ghost" size="sm" onClick={() => setConfirmDelete(false)}>
                  Cancel
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
