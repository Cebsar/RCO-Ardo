import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { Kpis } from "@/lib/types";

const statusColors = ["#d6a93a", "#e35d5b"];
const barColors = ["#d6a93a", "#7e8f78", "#b98545", "#c9c1ad"];

export function PipelineStatusChart({ kpis }: { kpis: Kpis }) {
  const data = [
    { name: "Successful", value: kpis.successful_executions },
    { name: "Failed", value: kpis.failed_executions },
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline Status</CardTitle>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="value" nameKey="name" innerRadius={58} outerRadius={92} paddingAngle={3}>
              {data.map((_, index) => (
                <Cell key={index} fill={statusColors[index]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ background: "#171a20", border: "1px solid #5f5234", color: "#f0eadc" }} />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

export function ArtifactBarChart({ values }: { values: Array<{ name: string; value: number }> }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Persisted Artifacts</CardTitle>
      </CardHeader>
      <CardContent className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={values} margin={{ top: 8, right: 8, left: 0, bottom: 16 }}>
            <CartesianGrid stroke="#3f3a2f" strokeDasharray="3 3" vertical={false} />
            <XAxis dataKey="name" tickLine={false} axisLine={false} fontSize={12} stroke="#b5aa95" />
            <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="#b5aa95" />
            <Tooltip contentStyle={{ background: "#171a20", border: "1px solid #5f5234", color: "#f0eadc" }} />
            <Bar dataKey="value" radius={[4, 4, 0, 0]}>
              {values.map((_, index) => (
                <Cell key={index} fill={barColors[index % barColors.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
