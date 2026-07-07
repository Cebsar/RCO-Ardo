import { Play, UploadCloud } from "lucide-react";
import { useRef, useState } from "react";
import { notify } from "@/components/layout/ToastViewport";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { enterpriseApi } from "@/lib/api";
import {
  sha256File,
  validateWorkbook,
  type OperationalStage,
} from "@/lib/operational";

const stages: OperationalStage[] = [
  "Upload workbook",
  "Validation",
  "Processing",
  "Persistence",
  "Reconciliation",
  "Dashboard refresh",
];
function executionTimestamp() {
  return Array.from(new Date().toISOString())
    .filter((character) => character >= "0" && character <= "9")
    .join("")
    .slice(0, 14);
}

export function PipelineRunner({ onComplete }: { onComplete: () => Promise<void> | void }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [running, setRunning] = useState(false);
  const [stage, setStage] = useState<OperationalStage>("Upload workbook");
  const [progress, setProgress] = useState(0);
  const [friendlyError, setFriendlyError] = useState("");

  async function runPipeline() {
    if (!file) {
      setFriendlyError("Select an accounting workbook before running the pipeline.");
      notify({ type: "error", title: "Workbook required", message: "Choose an Excel workbook to start the daily flow." });
      return;
    }

    setRunning(true);
    setFriendlyError("");
    const executionId = `op-${executionTimestamp()}`;

    try {
      const issues = validateWorkbook(file, executionId);
      const blockingIssue = issues.some((issue) => issue.type === "error");
      await sha256File(file);
      setStage("Validation");
      setProgress(20);
      if (blockingIssue) {
        throw new Error("Validation stopped the run. Review the Validation Center before processing again.");
      }

      setStage("Processing");
      setProgress(40);
      await enterpriseApi.runPipeline(file);
      setStage("Persistence");
      setProgress(70);
      setStage("Reconciliation");
      setProgress(85);
      setStage("Dashboard refresh");
      setProgress(100);
      await onComplete();
      notify({
        type: "success",
        title: "Pipeline completed",
        message: "Dashboard data was refreshed after the operational run.",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Pipeline execution could not be completed.";
      setFriendlyError(message);
      notify({ type: "error", title: "Pipeline failed", message });
    } finally {
      setRunning(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Pipeline Execution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <input
            ref={inputRef}
            type="file"
            accept=".xlsx,.xlsm,.xls"
            className="hidden"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <Button variant="outline" onClick={() => inputRef.current?.click()} disabled={running}>
            <UploadCloud className="h-4 w-4" />
            Upload workbook
          </Button>
          <div className="min-w-0 flex-1 text-sm text-muted-foreground">
            {file ? <span className="block truncate">{file.name}</span> : "No workbook selected"}
          </div>
          <Button onClick={runPipeline} disabled={running}>
            <Play className="h-4 w-4" />
            Run Accounting Pipeline
          </Button>
        </div>
        <div className="space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium">{stage}</span>
            <span className="text-muted-foreground">{progress}%</span>
          </div>
          <Progress value={progress} />
        </div>
        <div className="grid gap-2 text-xs text-muted-foreground sm:grid-cols-3 lg:grid-cols-6">
          {stages.map((item) => (
            <span key={item} className={item === stage ? "font-semibold text-foreground" : undefined}>
              {item}
            </span>
          ))}
        </div>
        {friendlyError ? <p className="text-sm text-destructive">{friendlyError}</p> : null}
      </CardContent>
    </Card>
  );
}
