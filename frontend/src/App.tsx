import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { ToastViewport } from "@/components/layout/ToastViewport";
import { DashboardPage } from "@/pages/DashboardPage";
import { DownloadCenterPage } from "@/pages/DownloadCenterPage";
import { DrePage } from "@/pages/DrePage";
import { PipelinePage } from "@/pages/PipelinePage";
import { ReconciliationPage } from "@/pages/ReconciliationPage";
import { SystemPage } from "@/pages/SystemPage";
import { ValidationCenterPage } from "@/pages/ValidationCenterPage";
import { FinancialFilterBar } from "@/components/financial/FinancialFilterBar";
import { FinancialFiltersProvider } from "@/lib/financialFilters";

type PageId = "dashboard" | "history" | "validation" | "downloads" | "dre" | "pipeline" | "reconciliation" | "system";

function Page({ activePage }: { activePage: PageId }) {
  let content: React.ReactNode;
  if (activePage === "history") content = <PipelinePage />;
  else if (activePage === "validation") content = <ValidationCenterPage />;
  else if (activePage === "downloads") content = <DownloadCenterPage />;
  else if (activePage === "dre") content = <DrePage />;
  else if (activePage === "pipeline") content = <PipelinePage />;
  else if (activePage === "reconciliation") content = <ReconciliationPage />;
  else if (activePage === "system") content = <SystemPage />;
  else content = <DashboardPage />;
  const financial = ["dashboard", "dre", "reconciliation", "validation", "downloads"].includes(activePage);
  return <>{financial ? <FinancialFilterBar /> : null}{content}</>;
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
      <FinancialFiltersProvider>
        <ToastViewport />
        <AppShell activePage={activePage} onNavigate={setActivePage}>
          <Page activePage={activePage} />
        </AppShell>
      </FinancialFiltersProvider>
    </QueryClientProvider>
  );
}
