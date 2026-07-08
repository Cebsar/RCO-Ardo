import { cn } from "@/lib/utils";

export function Progress({ value, className }: { value: number; className?: string }) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-2 overflow-hidden rounded-md bg-muted ring-1 ring-border/60", className)}>
      <div className="h-full bg-primary shadow-[0_0_18px_hsl(42_78%_56%_/_0.45)] transition-all duration-500" style={{ width: `${width}%` }} />
    </div>
  );
}
