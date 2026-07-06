import { useMutation, useQueryClient } from "@tanstack/react-query";
import { KeyRound, LogIn, LogOut, Save } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import {
  authExpiredEventName,
  clearStoredCredentials,
  clearStoredToken,
  enterpriseApi,
  getStoredApiKey,
  getStoredToken,
  storeApiKey,
  storeToken,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function AuthPanel() {
  const queryClient = useQueryClient();
  const panelRef = useRef<HTMLDivElement>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [apiKey, setApiKey] = useState(() => getStoredApiKey() ?? "");
  const [hasToken, setHasToken] = useState(() => Boolean(getStoredToken()));
  const [authMessage, setAuthMessage] = useState("");
  const [authMessageKind, setAuthMessageKind] = useState<"error" | "success">("success");
  const login = useMutation({
    mutationFn: () => enterpriseApi.login(username, password),
    onSuccess: (token) => {
      storeToken(token.access_token, token.expires_in);
      setHasToken(true);
      setAuthMessage("");
      setAuthMessageKind("success");
      setPassword("");
      queryClient.invalidateQueries();
    },
    onError: (error) => {
      setAuthMessage(error instanceof Error ? error.message : "Sign in failed. Check your credentials.");
      setAuthMessageKind("error");
    },
  });

  useEffect(() => {
    function handleAuthExpired() {
      clearStoredToken();
      setHasToken(false);
      setAuthMessage("Your session expired. Sign in again to continue.");
      setAuthMessageKind("error");
      queryClient.clear();
      panelRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    window.addEventListener(authExpiredEventName, handleAuthExpired);
    return () => window.removeEventListener(authExpiredEventName, handleAuthExpired);
  }, [queryClient]);

  function saveApiKey() {
    storeApiKey(apiKey);
    setAuthMessage(apiKey ? "Internal API key saved for service requests." : "Internal API key cleared.");
    setAuthMessageKind("success");
    queryClient.invalidateQueries();
  }

  function clearCredentials() {
    clearStoredCredentials();
    setApiKey("");
    setHasToken(false);
    setAuthMessage("");
    setAuthMessageKind("success");
    queryClient.invalidateQueries();
  }

  return (
    <div id="login" ref={panelRef} className="grid gap-2 rounded-lg border bg-card p-3 md:grid-cols-[1fr_1fr_auto_1fr_auto_auto]">
      <Input placeholder="Username" value={username} onChange={(event) => setUsername(event.target.value)} />
      <Input placeholder="Password" type="password" value={password} onChange={(event) => setPassword(event.target.value)} />
      <Button variant={hasToken ? "secondary" : "default"} onClick={() => login.mutate()} disabled={login.isPending}>
        <LogIn className="h-4 w-4" />
        {hasToken ? "JWT active" : "Sign in"}
      </Button>
      <Input placeholder="Internal API key" value={apiKey} onChange={(event) => setApiKey(event.target.value)} />
      <Button variant="outline" onClick={saveApiKey}>
        <Save className="h-4 w-4" />
        Save key
      </Button>
      <Button variant="ghost" size="icon" onClick={clearCredentials} title="Clear credentials">
        <LogOut className="h-4 w-4" />
      </Button>
      {authMessage ? (
        <p className={`md:col-span-6 text-sm ${authMessageKind === "error" ? "text-destructive" : "text-emerald-700"}`}>
          {authMessage}
        </p>
      ) : null}
      <p className="md:col-span-6 flex items-center gap-2 text-xs text-muted-foreground">
        <KeyRound className="h-3.5 w-3.5" />
        JWT sessions use browser session storage. Internal API keys remain available for trusted service access.
      </p>
    </div>
  );
}
