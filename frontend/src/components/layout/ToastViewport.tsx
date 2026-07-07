import { CheckCircle2, Info, XCircle } from "lucide-react";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

type Toast = {
  id: string;
  title: string;
  message: string;
  type: "success" | "error" | "info";
};

export function notify(toast: Omit<Toast, "id">) {
  window.dispatchEvent(new CustomEvent("enterprise-toast", { detail: { ...toast, id: crypto.randomUUID() } }));
}

export function ToastViewport() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  useEffect(() => {
    function handleToast(event: Event) {
      const toast = (event as CustomEvent<Toast>).detail;
      setToasts((current) => [toast, ...current].slice(0, 4));
      window.setTimeout(() => {
        setToasts((current) => current.filter((item) => item.id !== toast.id));
      }, 5200);
    }

    window.addEventListener("enterprise-toast", handleToast);
    return () => window.removeEventListener("enterprise-toast", handleToast);
  }, []);

  return (
    <div className="fixed right-4 top-4 z-50 grid w-[min(360px,calc(100vw-2rem))] gap-2">
      {toasts.map((toast) => {
        const Icon = toast.type === "success" ? CheckCircle2 : toast.type === "error" ? XCircle : Info;
        return (
          <div
            key={toast.id}
            className={cn(
              "rounded-lg border bg-card p-3 shadow-lg",
              toast.type === "success" && "border-emerald-200",
              toast.type === "error" && "border-destructive/40",
            )}
          >
            <div className="flex gap-3">
              <Icon className={cn("mt-0.5 h-4 w-4", toast.type === "error" ? "text-destructive" : "text-primary")} />
              <div>
                <p className="text-sm font-semibold">{toast.title}</p>
                <p className="mt-1 text-sm text-muted-foreground">{toast.message}</p>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
