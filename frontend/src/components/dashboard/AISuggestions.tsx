import { Link } from "react-router-dom";
import { Sparkles, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { EmptyState } from "@/components/common/EmptyState";
import { ROUTES } from "@/constants/routes";
import type { DashboardSuggestionResponse } from "@/types/dashboard";

export function AISuggestions({ items }: { items: DashboardSuggestionResponse[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-primary" />
          AI Suggestions
        </CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <EmptyState
            icon={Sparkles}
            title="No suggestions yet"
            description="Analyze a resume to get personalized AI recommendations."
          />
        ) : (
          <div className="space-y-2">
            {items.map((s, i) => (
              <Link
                key={`${s.analysis_id}-${i}`}
                to={ROUTES.resumeAnalysis(s.resume_id)}
                className="flex items-start gap-3 rounded-md bg-muted/50 p-3 transition-transform hover:translate-x-0.5 hover:bg-muted"
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm">{s.suggestion}</p>
                  <Badge variant="secondary" className="mt-1.5">{s.source}</Badge>
                </div>
                <ChevronRight className="mt-1 h-4 w-4 shrink-0 text-muted-foreground" />
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
