import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { DashboardPage } from "@/pages/DashboardPage";
import { DrePage } from "@/pages/DrePage";
import { PipelinePage } from "@/pages/PipelinePage";
import { ReconciliationPage } from "@/pages/ReconciliationPage";
import { SystemPage } from "@/pages/SystemPage";

type PageId = "dashboard" | "dre" | "pipeline" | "reconciliation" | "system";

function Page({ activePage }: { activePage: PageId }) {
  if (activePage === "dre") return <DrePage />;
  if (activePage === "pipeline") return <PipelinePage />;
  if (activePage === "reconciliation") return <ReconciliationPage />;
  if (activePage === "system") return <SystemPage />;
  return <DashboardPage />;
}

export default function App() {
  const [activePage, setActivePage] = useState<PageId>("dashboard");
  const queryClient = useMemo(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            retry: 1,
          },
        },
      }),
    [],
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AppShell activePage={activePage} onNavigate={setActivePage}>
        <Page activePage={activePage} />
      </AppShell>
    </QueryClientProvider>
  );
}
