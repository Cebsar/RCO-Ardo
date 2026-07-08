import { Activity, BarChart3, Bell, Command, Database, Download, GitBranch, Home, ListChecks, Search, ShieldCheck, TableProperties, UserRound } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AuthPanel } from "@/components/layout/AuthPanel";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";

type PageId = "dashboard" | "history" | "validation" | "downloads" | "dre" | "pipeline" | "reconciliation" | "system";

const navigation = [
  { id: "dashboard", label: "Command Center", icon: Home },
  { id: "pipeline", label: "Accounting Pipeline", icon: GitBranch },
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
  const currentPage = navigation.find((item) => item.id === activePage);

  return (
    <div className="min-h-screen bg-transparent">
      <aside className="fixed inset-y-0 left-0 z-20 hidden w-72 border-r border-border/70 bg-background/92 lg:block">
        <div className="flex h-20 items-center gap-3 border-b border-border/70 px-5">
          <div className="flex h-11 w-11 items-center justify-center rounded-md bg-primary text-primary-foreground shadow-[0_0_32px_hsl(42_78%_56%_/_0.26)]">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <p className="text-base font-semibold text-primary">ARDO</p>
            <p className="text-xs uppercase tracking-[0.16em] text-muted-foreground">Enterprise Finance</p>
          </div>
        </div>
        <div className="border-b border-border/55 px-5 py-4">
          <Badge>Live API</Badge>
          <p className="mt-2 text-xs text-muted-foreground">Conectado ao backend local de producao.</p>
        </div>
        <nav className="space-y-1 p-3">
          {navigation.map((item) => {
            const Icon = item.icon;
            return (
              <Button
                key={item.id}
                variant={activePage === item.id ? "secondary" : "ghost"}
                className={cn("h-11 w-full justify-start", activePage === item.id && "border-primary/45 font-semibold text-primary")}
                onClick={() => onNavigate(item.id)}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </Button>
            );
          })}
        </nav>
      </aside>
      <div className="lg:pl-72">
        <header className="sticky top-0 z-10 border-b border-border/70 bg-background/82 backdrop-blur-xl">
          <div className="flex min-h-20 flex-wrap items-center justify-between gap-3 px-4 py-3 lg:px-7">
            <div className="min-w-0">
              <p className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-primary">
                <Command className="h-3.5 w-3.5" />
                Executive Command Center
              </p>
              <h1 className="mt-1 text-2xl font-semibold">{currentPage?.label}</h1>
            </div>
            <div className="hidden min-w-[280px] max-w-md flex-1 items-center gap-2 lg:flex">
              <div className="relative w-full">
                <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                <Input className="pl-9" placeholder="Pesquisar operacoes, DRE, execucoes" />
              </div>
            </div>
            <div className="flex flex-wrap items-center gap-2">
              <Button variant="ghost" size="icon" title="Notificacoes">
                <Bell className="h-4 w-4" />
              </Button>
              <Badge>JWT / API</Badge>
              <div className="flex h-10 items-center gap-2 rounded-md border border-border/75 bg-secondary/55 px-3 text-sm">
                <UserRound className="h-4 w-4 text-primary" />
                <span className="hidden sm:inline">Operador</span>
              </div>
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
        <main className="space-y-6 px-4 py-6 lg:px-7">
          <AuthPanel />
          {children}
        </main>
      </div>
    </div>
  );
}
