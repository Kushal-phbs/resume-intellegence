import { EmptyState } from "@/components/common/EmptyState";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardQuickActionResponse } from "@/types/dashboard";
import { ChevronRight, Rocket } from "lucide-react";
import { Link } from "react-router-dom";

export function QuickActions({ items }: { items: DashboardQuickActionResponse[] }) {
  const sorted = [...items].sort((a, b) => a.priority - b.priority);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Quick Actions</CardTitle>
      </CardHeader>
      <CardContent>
        {sorted.length === 0 ? (
          <EmptyState icon={Rocket} title="No suggested actions" description="You're all set for now." />
        ) : (
          <div className="space-y-2">
            {sorted.map((a) => (
              <Link
                key={a.key}
                to={a.route}
                className="flex items-center gap-3 rounded-md bg-muted/50 p-3 text-sm transition-transform hover:translate-x-0.5 hover:bg-muted"
              >
                <div className="min-w-0 flex-1">
                  <p className="font-medium">{a.title}</p>
                  <p className="truncate text-xs text-muted-foreground">{a.description}</p>
                </div>
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground" />
              </Link>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
