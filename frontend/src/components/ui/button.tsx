import * as React from "react";
import { cn } from "@/lib/utils";

type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "default" | "secondary" | "outline" | "ghost";
  size?: "sm" | "md" | "icon";
};

export function Button({ className, variant = "default", size = "md", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-md text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
        variant === "default" && "bg-primary text-primary-foreground shadow-[0_0_24px_hsl(42_78%_56%_/_0.2)] hover:bg-primary/90",
        variant === "secondary" && "border border-primary/25 bg-accent text-accent-foreground hover:bg-accent/80",
        variant === "outline" && "border border-border/80 bg-secondary/70 text-foreground hover:border-primary/55 hover:bg-accent/45",
        variant === "ghost" && "text-muted-foreground hover:bg-muted/75 hover:text-foreground",
        size === "sm" && "h-8 px-3",
        size === "md" && "h-10 px-4",
        size === "icon" && "h-9 w-9",
        className,
      )}
      {...props}
    />
  );
}
