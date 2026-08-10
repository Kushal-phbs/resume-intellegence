import { useMemo, useState } from "react";
import { FileText, Search, Plus, X, ChevronLeft, ChevronRight } from "lucide-react";
import { useResumes, useDeleteResume } from "@/hooks/useResumes";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { UploadResumeForm } from "@/components/resume/UploadResumeForm";
import { ResumeListItem } from "@/components/resume/ResumeListItem";

const PAGE_SIZE = 8;

export function ResumesPage() {
  const { data, isLoading, isError, error, refetch } = useResumes();
  const deleteResume = useDeleteResume();
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [showUpload, setShowUpload] = useState(false);
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);

  const filtered = useMemo(() => {
    if (!data) return [];
    const q = query.trim().toLowerCase();
    if (!q) return data.items;
    return data.items.filter((r) => r.title.toLowerCase().includes(q));
  }, [data, query]);

  // NOTE: GET /resumes has no limit/offset query params — the backend
  // returns the full list in one call, so pagination here is a purely
  // client-side slice over the already-fetched array, not server-paginated.
  const totalPages = Math.max(1, Math.ceil(filtered.length / PAGE_SIZE));
  const paged = filtered.slice((page - 1) * PAGE_SIZE, page * PAGE_SIZE);

  const handleDelete = (id: string) => {
    setPendingDeleteId(id);
    deleteResume.mutate(id, { onSettled: () => setPendingDeleteId(null) });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Resume Library</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            {data ? `${data.total} resume${data.total === 1 ? "" : "s"}` : "Manage all your resumes"}
          </p>
        </div>
        <Button onClick={() => setShowUpload((s) => !s)}>
          {showUpload ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}
          {showUpload ? "Close" : "Upload Resume"}
        </Button>
      </div>

      {showUpload && (
        <Card>
          <CardContent className="p-5">
            <UploadResumeForm onSuccess={() => setShowUpload(false)} />
          </CardContent>
        </Card>
      )}

      {isLoading ? (
        <div className="space-y-2">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-16 w-full" />
          ))}
        </div>
      ) : isError ? (
        <ErrorState error={error} onRetry={() => refetch()} />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          icon={FileText}
          title="No resumes yet"
          description="Upload your first resume to start getting AI-powered insights and job matches."
          actionLabel="Upload Resume"
          onAction={() => setShowUpload(true)}
        />
      ) : (
        <Card>
          <CardContent className="space-y-4 p-5">
            {/* Search */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={query}
                onChange={(e) => { setQuery(e.target.value); setPage(1); }}
                placeholder="Search resumes by title…"
                className="pl-9"
              />
            </div>

            {filtered.length === 0 ? (
              <EmptyState icon={Search} title="No matches" description="Try a different search term." />
            ) : (
              <>
                <div className="space-y-2">
                  {paged.map((r) => (
                    <ResumeListItem
                      key={r.id}
                      resume={r}
                      onDelete={handleDelete}
                      isDeleting={pendingDeleteId === r.id && deleteResume.isPending}
                    />
                  ))}
                </div>

                {totalPages > 1 && (
                  <div className="flex items-center justify-between pt-2">
                    <p className="text-xs text-muted-foreground">
                      Page {page} of {totalPages}
                    </p>
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={page === 1}
                        onClick={() => setPage((p) => Math.max(1, p - 1))}
                        aria-label="Previous page"
                      >
                        <ChevronLeft className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        disabled={page === totalPages}
                        onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                        aria-label="Next page"
                      >
                        <ChevronRight className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
