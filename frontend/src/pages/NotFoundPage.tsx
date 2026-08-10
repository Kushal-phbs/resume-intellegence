import { Link } from "react-router-dom";
import { FileQuestion } from "lucide-react";
import { ROUTES } from "@/constants/routes";

export function NotFoundPage() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-4 text-center">
      <div className="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
        <FileQuestion className="h-8 w-8 text-muted-foreground" />
      </div>
      <div>
        <h1 className="text-2xl font-bold">Page not found</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          The page you're looking for doesn't exist or was moved.
        </p>
      </div>
      <Link
        to={ROUTES.dashboard}
        className="inline-flex items-center gap-2 rounded-md bg-muted px-4 py-2 text-sm font-semibold text-foreground transition-colors hover:bg-muted/70"
      >
        Go to Dashboard
      </Link>
    </div>
  );
}
