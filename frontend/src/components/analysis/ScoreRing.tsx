import { cn } from "@/lib/utils";

export function ScoreRing({
  value,
  label,
  size = 104,
  colorClass = "stroke-primary",
}: {
  value: number | null;
  label: string;
  size?: number;
  colorClass?: string;
}) {
  const v = value ?? 0;
  const radius = 15.9;
  return (
    <div className="relative mx-auto" style={{ width: size, height: size }}>
      <svg viewBox="0 0 36 36" className="h-full w-full -rotate-90">
        <circle cx="18" cy="18" r={radius} fill="none" strokeWidth="3" className="stroke-muted" />
        {value !== null && (
          <circle
            cx="18"
            cy="18"
            r={radius}
            fill="none"
            strokeWidth="3"
            strokeLinecap="round"
            strokeDasharray={`${v} 100`}
            className={cn(colorClass, "transition-all duration-700 ease-out")}
          />
        )}
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-xl font-bold">{value !== null ? value : "—"}</span>
        <span className="text-[10px] text-muted-foreground">{label}</span>
      </div>
    </div>
  );
}
