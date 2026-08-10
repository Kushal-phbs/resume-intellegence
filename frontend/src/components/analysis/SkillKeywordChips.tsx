import { Badge } from "@/components/ui/badge";
import type { SkillResponse } from "@/types/analysis";

const CATEGORY_VARIANT: Record<string, "default" | "secondary" | "success" | "muted"> = {
  technical: "default",
  soft: "secondary",
  domain: "success",
  tool: "default",
  other: "muted",
};

export function SkillChips({ skills }: { skills: SkillResponse[] }) {
  if (skills.length === 0) return <p className="text-sm text-muted-foreground">No skills extracted yet.</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map((s) => (
        <Badge key={s.id} variant={CATEGORY_VARIANT[s.category] ?? "default"}>
          {s.skill_name}
        </Badge>
      ))}
    </div>
  );
}

export function KeywordChips({ keywords }: { keywords: string[] }) {
  if (keywords.length === 0) return <p className="text-sm text-muted-foreground">No keywords extracted yet.</p>;
  return (
    <div className="flex flex-wrap gap-1.5">
      {keywords.map((k) => (
        <Badge key={k} variant="muted">
          {k}
        </Badge>
      ))}
    </div>
  );
}
