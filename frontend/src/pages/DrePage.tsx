import type { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { DataTable } from "@/components/tables/DataTable";
import { ErrorState, LoadingGrid, EmptyState } from "@/components/layout/PageState";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { enterpriseApi } from "@/lib/api";
import type { DreRow } from "@/lib/types";
import { formatDecimal } from "@/lib/utils";

const columns: ColumnDef<DreRow>[] = [
  { accessorKey: "node_code", header: "Code" },
  { accessorKey: "node_name", header: "Name" },
  { accessorKey: "level", header: "Level" },
  { accessorKey: "amount", header: "Amount", cell: ({ row }) => formatDecimal(row.original.amount) },
  { accessorKey: "currency", header: "Currency" },
  { accessorKey: "parent_node_code", header: "Parent" },
];

export function DrePage() {
  const [companyInput, setCompanyInput] = useState("");
  const [periodInput, setPeriodInput] = useState("");
  const [filters, setFilters] = useState<{ company?: string; period?: string }>({});
  const dre = useQuery({
    queryKey: ["dre", filters.company, filters.period],
    queryFn: () => enterpriseApi.dre(filters.company, filters.period),
  });

  if (dre.isLoading) return <LoadingGrid />;
  if (dre.isError || !dre.data) return <ErrorState message="DRE data could not be loaded." onRetry={() => dre.refetch()} />;

  const nodes = dre.data.data.nodes;

  return (
    <div className="space-y-6">
      <Card>
        <CardContent className="grid gap-3 p-5 md:grid-cols-[1fr_1fr_auto_auto]">
          <Input placeholder="Company" value={companyInput} onChange={(event) => setCompanyInput(event.target.value)} />
          <Input placeholder="Period" value={periodInput} onChange={(event) => setPeriodInput(event.target.value)} />
          <Button onClick={() => setFilters({ company: companyInput || undefined, period: periodInput || undefined })}>
            Apply
          </Button>
          <Button variant="outline" onClick={() => { setCompanyInput(""); setPeriodInput(""); setFilters({}); }}>
            Clear
          </Button>
        </CardContent>
      </Card>
      {nodes.length === 0 ? (
        <EmptyState title="No DRE data" message="No DRE nodes were returned for the selected filters." />
      ) : (
        <div className="grid gap-6 xl:grid-cols-[minmax(0,1.35fr)_minmax(360px,0.65fr)]">
          <DataTable columns={columns} data={nodes} />
          <Card>
            <CardHeader>
              <CardTitle>DRE Amounts</CardTitle>
            </CardHeader>
            <CardContent className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={nodes.slice(0, 12).map((node) => ({ name: node.node_code, amount: Number(node.amount ?? 0) }))}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} />
                  <XAxis dataKey="name" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="amount" fill="#0369a1" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
