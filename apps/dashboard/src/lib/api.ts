// Auto-detect: use relative /api so proxy works for both localhost AND network IP access
const BASE = "/api";

function token() {
  return localStorage.getItem("px_token") ?? "";
}

function headers(extra?: Record<string, string>): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const t = token();
  if (t) h["Authorization"] = `Bearer ${t}`;
  return { ...h, ...extra };
}

async function req<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { ...headers(), ...(init?.headers ?? {}) },
  });
  if (res.status === 401) {
    localStorage.removeItem("px_token");
    localStorage.removeItem("px_user");
    throw new Error("Unauthorized");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: `HTTP ${res.status}` }));
    throw new Error(err.message ?? `HTTP ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  get:    <T>(p: string)                 => req<T>(p),
  post:   <T>(p: string, body: unknown)  => req<T>(p, { method: "POST",   body: JSON.stringify(body) }),
  put:    <T>(p: string, body: unknown)  => req<T>(p, { method: "PUT",    body: JSON.stringify(body) }),
  patch:  <T>(p: string, body: unknown)  => req<T>(p, { method: "PATCH",  body: JSON.stringify(body) }),
  delete: <T>(p: string)                 => req<T>(p, { method: "DELETE" }),
};

// For SSE (EventSource) we need an absolute URL — use current host
export const SSE_BASE = `${window.location.protocol}//${window.location.hostname}:3001/api`;
