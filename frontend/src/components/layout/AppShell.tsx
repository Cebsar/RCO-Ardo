import { Activity, BarChart3, Database, Download, GitBranch, Home, ListChecks, ShieldCheck, TableProperties } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AuthPanel } from "@/components/layout/AuthPanel";
import { cn } from "@/lib/utils";

type PageId = "dashboard" | "history" | "validation" | "downloads" | "dre" | "pipeline" | "reconciliation" | "system";

const navigation = [
  { id: "dashboard", label: "Home", icon: Home },
  { id: "history", label: "Execution History", icon: TableProperties },
  { id: "validation", label: "Validation Center", icon: ListChecks },
  { id: "downloads", label: "Download Center", icon: Download },
  { id: "dre", label: "DRE", icon: BarChart3 },
  { id: "reconciliation", label: "Reconciliation", icon: Database },
  { id: "system", label: "System", icon: ShieldCheck },
] satisfies Array<{ id: PageId; label: string; icon: typeof Home }>;

export function AppShell({
  activePage,
  onNavigate,
  children,
}: {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  children: React.ReactNode;
}) {
  return (
    <div className="min-h-screen bg-background">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-64 border-r bg-card lg:block">
        <div className="flex h-16 items-center gap-3 border-b px-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <p className="text-sm font-semibold">ARDO Enterprise</p>
            <p className="text-xs text-muted-foreground">Financial Operations</p>
          </div>
        </div>
        <nav className="space-y-1 p-3">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.id}
                variant={activePage === item.id ? "secondary" : "ghost"}
                className={cn("w-full justify-start", activePage === item.id && "font-semibold")}
                onClick={() => onNavigate(item.id)}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Button>
            );
          })}
        </nav>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b bg-background/95 backdrop-blur">
          <div className="flex min-h-16 flex-wrap items-center justify-between gap-3 px-4 py-3 lg:px-6">
            <div>
              <p className="text-sm text-muted-foreground">Enterprise Dashboard</p>
              <h1 className="text-xl font-semibold">{navigation.find((item) => item.id === activePage)?.label}</h1>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Badge className="border-emerald-200 bg-emerald-50 text-emerald-700">REST API only</Badge>
              <Badge className="border-sky-200 bg-sky-50 text-sky-700">Production UI</Badge>
            </div>
            <nav className="grid w-full grid-cols-3 gap-2 lg:hidden">
              {navigation.map((item) => (
                <Button
                  key={item.id}
                  size="sm"
                  variant={activePage === item.id ? "secondary" : "outline"}
                  onClick={() => onNavigate(item.id)}
                >
                  {item.label}
                </Button>
              ))}
            </nav>
          </div>
        </header>
        <main className="space-y-6 px-4 py-6 lg:px-6">
          <AuthPanel />
          {children}
        </main>
      </div>
    </div>
  );
}
