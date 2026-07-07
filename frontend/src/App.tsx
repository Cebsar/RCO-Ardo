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

type PageId = "dashboard" | "history" | "validation" | "downloads" | "dre" | "pipeline" | "reconciliation" | "system";

function Page({ activePage }: { activePage: PageId }) {
  if (activePage === "history") return <PipelinePage />;
  if (activePage === "validation") return <ValidationCenterPage />;
  if (activePage === "downloads") return <DownloadCenterPage />;
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
      <ToastViewport />
      <AppShell activePage={activePage} onNavigate={setActivePage}>
        <Page activePage={activePage} />
      </AppShell>
    </QueryClientProvider>
  );
}
