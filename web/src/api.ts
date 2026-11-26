import type { Costs, Estimate, Outputs, RunSummary, StageName, Storyboard } from "./types";

export class ApiError extends Error {
  constructor(public status: number, public detail: unknown) {
    super(typeof detail === "string" ? detail : `request failed (${status})`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
  });
  const body = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, body?.detail ?? body);
  return body as T;
}

export const api = {
  schema: () => request<object>("/api/schema"),
  showcase: () => request<{ storyboard: Storyboard; outputs: Outputs }>("/api/showcase"),
  createProject: (source: "example" | "blank") =>
    request<{ id: string }>("/api/projects", { method: "POST", body: JSON.stringify({ source }) }),
  storyboard: (id: string) => request<Storyboard>(`/api/projects/${id}/storyboard`),
  saveStoryboard: (id: string, storyboard: Storyboard) =>
    request<{ ok: true }>(`/api/projects/${id}/storyboard`, { method: "PUT", body: JSON.stringify(storyboard) }),
  outputs: (id: string) => request<Outputs>(`/api/projects/${id}/outputs`),
  estimate: (id: string, stages: StageName[], quality: "draft" | "final") =>
    request<Estimate>(`/api/projects/${id}/estimate`, { method: "POST", body: JSON.stringify({ stages, quality }) }),
  startRun: (id: string, stages: StageName[], quality: "draft" | "final", keys: Record<string, string>) =>
    request<RunSummary>(`/api/projects/${id}/runs`, {
      method: "POST",
      body: JSON.stringify({ stages, quality }),
      headers: { "X-Provider-Keys": JSON.stringify(keys) },
    }),
  activeRun: (id: string) => request<RunSummary | null>(`/api/projects/${id}/runs/active`),
  cancelRun: (runId: string) => request<{ ok: true }>(`/api/runs/${runId}/cancel`, { method: "POST" }),
  costs: (id: string) => request<Costs>(`/api/projects/${id}/costs`),
};

export function describeError(error: unknown): string[] {
  if (!(error instanceof ApiError)) return [String(error)];
  const detail = error.detail as { errors?: string[]; missing_keys?: string[]; problems?: string[] } | string;
  if (typeof detail === "string") return [detail];
  if (detail?.missing_keys) return [`Add these keys first: ${detail.missing_keys.join(", ")}`];
  return detail?.errors ?? detail?.problems ?? [error.message];
}
