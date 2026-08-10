import { Link } from "react-router-dom";
import { FileText, Star, ChevronRight, Download, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatDate } from "@/lib/utils";
import { resumesApi } from "@/api/resumes";
import { ROUTES } from "@/constants/routes";
import type { ResumeResponse } from "@/types/resume";

export function ResumeListItem({
  resume,
  onDelete,
  isDeleting,
}: {
  resume: ResumeResponse;
  onDelete: (id: string) => void;
  isDeleting: boolean;
}) {
  return (
    <div className="flex items-center gap-3 rounded-md bg-muted/50 p-3 transition-colors hover:bg-muted">
      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-md bg-muted">
        <FileText className="h-4 w-4 text-muted-foreground" />
      </div>

      <Link to={ROUTES.resumeDetail(resume.id)} className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{resume.title}</p>
        <p className="text-xs text-muted-foreground">
          Updated {formatDate(resume.updated_at)}
        </p>
      </Link>

      {resume.is_primary && <Star className="h-3.5 w-3.5 shrink-0 text-primary" fill="currentColor" />}

      <a
        href={resumesApi.downloadUrl(resume.id)}
        target="_blank"
        rel="noreferrer"
        aria-label="Download resume"
        className="flex h-8 w-8 items-center justify-center rounded-md text-muted-foreground hover:bg-muted hover:text-foreground"
      >
        <Download className="h-4 w-4" />
      </a>

      <Button
        variant="ghost"
        size="icon"
        aria-label="Delete resume"
        onClick={() => onDelete(resume.id)}
        isLoading={isDeleting}
        className="h-8 w-8 text-muted-foreground hover:text-destructive"
      >
        {!isDeleting && <Trash2 className="h-4 w-4" />}
      </Button>

      <Link to={ROUTES.resumeDetail(resume.id)}>
        <ChevronRight className="h-4 w-4 text-muted-foreground" />
      </Link>
    </div>
  );
}
