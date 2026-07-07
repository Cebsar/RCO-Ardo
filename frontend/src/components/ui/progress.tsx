import { cn } from "@/lib/utils";

export function Progress({ value, className }: { value: number; className?: string }) {
  const width = Math.max(0, Math.min(100, value));
  return (
    <div className={cn("h-2 overflow-hidden rounded-md bg-muted", className)}>
      <div className="h-full bg-primary transition-all duration-500" style={{ width: `${width}%` }} />
    </div>
  );
}
