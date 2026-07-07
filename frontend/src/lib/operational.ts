export type OperationalStage = "Upload workbook" | "Validation" | "Processing" | "Persistence" | "Reconciliation" | "Dashboard refresh";

export type ValidationIssue = {
  id: string;
  executionId: string;
  type: "warning" | "error" | "normalization" | "accounting";
  message: string;
  createdAt: string;
};

export type OperationalExecution = {
  id: string;
  date: string;
  user: string;
  durationSeconds: number;
  workbookName: string;
  workbookSha256: string;
  rowsProcessed: number;
  rowsIgnored: number;
  status: "succeeded" | "failed";
  stage: OperationalStage;
  validationIssues: ValidationIssue[];
};

const executionsKey = "enterprise.operational.executions";
const issuesKey = "enterprise.operational.validationIssues";

function readJson<T>(key: string, fallback: T): T {
  try {
    const value = window.localStorage.getItem(key);
    return value ? (JSON.parse(value) as T) : fallback;
  } catch {
    return fallback;
  }
}

function writeJson<T>(key: string, value: T) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

export function listOperationalExecutions() {
  return readJson<OperationalExecution[]>(executionsKey, []);
}

export function listValidationIssues() {
  return readJson<ValidationIssue[]>(issuesKey, []);
}

export function saveOperationalExecution(execution: OperationalExecution) {
  const executions = [execution, ...listOperationalExecutions()].slice(0, 50);
  const issues = [...execution.validationIssues, ...listValidationIssues()].slice(0, 100);
  writeJson(executionsKey, executions);
  writeJson(issuesKey, issues);
  window.dispatchEvent(new CustomEvent("enterprise-operational-history-updated"));
}

export async function sha256File(file: File) {
  const digest = await crypto.subtle.digest("SHA-256", await file.arrayBuffer());
  return Array.from(new Uint8Array(digest))
    .map((byte) => byte.toString(16).padStart(2, "0"))
    .join("");
}

export function validateWorkbook(file: File, executionId: string): ValidationIssue[] {
  const now = new Date().toISOString();
  const issues: ValidationIssue[] = [];
  if (!/\.(xlsx|xlsm|xls)$/i.test(file.name)) {
    issues.push({
      id: `${executionId}-extension`,
      executionId,
      type: "error",
      message: "Workbook must be an Excel file before accounting processing can start.",
      createdAt: now,
    });
  }
  if (file.size === 0) {
    issues.push({
      id: `${executionId}-empty`,
      executionId,
      type: "error",
      message: "Workbook is empty and cannot be imported.",
      createdAt: now,
    });
  }
  if (file.size > 20 * 1024 * 1024) {
    issues.push({
      id: `${executionId}-size`,
      executionId,
      type: "warning",
      message: "Large workbook detected. Daily processing may take longer than usual.",
      createdAt: now,
    });
  }
  return issues;
}

export function estimateRows(file: File) {
  return Math.max(1, Math.round(file.size / 180));
}

export function downloadTextFile(filename: string, content: string, type = "application/json") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  URL.revokeObjectURL(url);
}
