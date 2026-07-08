import type {
  ApiEnvelope,
  DreResponse,
  Health,
  Kpis,
  PipelineExecutionDetail,
  PipelineExecutionSummary,
  Version,
} from "@/lib/types";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "/api";
const jwtStorageKey = "enterprise.jwt";
const jwtExpiresAtStorageKey = "enterprise.jwt.expiresAt";
const apiKeyStorageKey = "enterprise.apiKey";
export const authExpiredEventName = "enterprise-auth-expired";

export class AuthenticationError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "AuthenticationError";
  }
}

export class AuthSessionExpiredError extends AuthenticationError {
  constructor() {
    super("Your session expired. Sign in again to continue.");
    this.name = "AuthSessionExpiredError";
  }
}

function browserStorage() {
  return {
    session: window.sessionStorage,
    local: window.localStorage,
  };
}

export function getStoredToken() {
  return browserStorage().session.getItem(jwtStorageKey);
}

export function getStoredApiKey() {
  return browserStorage().local.getItem(apiKeyStorageKey);
}

export function storeToken(accessToken: string, expiresIn: number) {
  const expiresAt = Date.now() + expiresIn * 1000;
  const { session } = browserStorage();
  session.setItem(jwtStorageKey, accessToken);
  session.setItem(jwtExpiresAtStorageKey, String(expiresAt));
}

export function clearStoredToken() {
  const { session } = browserStorage();
  session.removeItem(jwtStorageKey);
  session.removeItem(jwtExpiresAtStorageKey);
}

export function storeApiKey(apiKey: string) {
  const { local } = browserStorage();
  if (apiKey) {
    local.setItem(apiKeyStorageKey, apiKey);
  } else {
    local.removeItem(apiKeyStorageKey);
  }
}

export function clearStoredCredentials() {
  clearStoredToken();
  browserStorage().local.removeItem(apiKeyStorageKey);
}

function tokenExpired() {
  const expiresAt = Number(browserStorage().session.getItem(jwtExpiresAtStorageKey));
  return Number.isFinite(expiresAt) && expiresAt > 0 && Date.now() >= expiresAt;
}

function redirectToLogin() {
  clearStoredToken();
  window.dispatchEvent(new CustomEvent(authExpiredEventName));
  if (window.location.hash !== "#login") {
    window.location.hash = "login";
  }
}

function authHeaders() {
  if (tokenExpired()) {
    redirectToLogin();
    throw new AuthSessionExpiredError();
  }
  const token = getStoredToken();
  const apiKey = getStoredApiKey();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  if (apiKey) headers["X-API-Key"] = apiKey;
  return headers;
}

function authHeadersWithoutContentType() {
  const headers = authHeaders();
  delete headers["Content-Type"];
  return headers;
}

async function request<T>(path: string, secured = true): Promise<ApiEnvelope<T>> {
  const response = await fetch(`${apiBaseUrl}${path}`, {
    headers: secured ? authHeaders() : { "Content-Type": "application/json" },
  });
  if (response.status === 401 && secured) {
    redirectToLogin();
    throw new AuthSessionExpiredError();
  }
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<ApiEnvelope<T>>;
}

export const enterpriseApi = {
  login: async (username: string, password: string) => {
    const body = new URLSearchParams();
    body.set("username", username);
    body.set("password", password);
    const response = await fetch(`${apiBaseUrl}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (!response.ok) {
      throw new AuthenticationError("Sign in failed. Check your username and password.");
    }
    return response.json() as Promise<{ access_token: string; token_type: string; expires_in: number }>;
  },
  health: () => request<Health>("/health", false),
  version: () => request<Version>("/version", false),
  kpis: () => request<Kpis>("/analytics/kpis"),
  pipelineHistory: (limit = 50) =>
    request<{ executions: PipelineExecutionSummary[] }>(`/pipeline/history?limit=${limit}`),
  pipelineExecution: (executionId: string) =>
    request<{ execution: PipelineExecutionDetail }>(`/pipeline/${executionId}`),
  downloads: () => request<{ latest_execution_id: string | null; artifacts: Array<Record<string, unknown>> }>("/downloads"),
  runPipeline: async (workbook: File) => {
    const body = new FormData();
    body.append("workbook", workbook);
    const response = await fetch(`${apiBaseUrl}/pipeline/run`, {
      method: "POST",
      headers: authHeadersWithoutContentType(),
      body,
    });
    if (response.status === 401) {
      redirectToLogin();
      throw new AuthSessionExpiredError();
    }
    if (!response.ok) {
      throw new Error(`Pipeline failed with status ${response.status}`);
    }
    return response.json() as Promise<ApiEnvelope<{ execution: PipelineExecutionDetail }>>;
  },
  dre: (company?: string, period?: string) => {
    if (company && period) return request<DreResponse>(`/financial/dre/${company}/${period}`);
    if (company) return request<DreResponse>(`/financial/dre/${company}`);
    return request<DreResponse>("/financial/dre");
  },
};
