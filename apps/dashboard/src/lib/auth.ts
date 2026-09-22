// Always use relative /api so it works via ngrok, local network, or any host
const BASE  = "/api";
const EMAIL = "dev@prospex-demo.com";
const PASS  = "DevPass123!";

export interface AuthUser { id: string; name: string; email: string; }
export interface AuthWorkspace { id: string; name: string; slug: string; }

export function getToken()     { return localStorage.getItem("px_token") ?? ""; }
export function getUser(): AuthUser | null {
  try { return JSON.parse(localStorage.getItem("px_user") ?? "null"); } catch { return null; }
}
export function getWorkspace(): AuthWorkspace | null {
  try { return JSON.parse(localStorage.getItem("px_workspace") ?? "null"); } catch { return null; }
}

function store(data: { token: string; user: AuthUser; workspace?: AuthWorkspace | null }) {
  localStorage.setItem("px_token", data.token);
  localStorage.setItem("px_user",  JSON.stringify(data.user));
  if (data.workspace) localStorage.setItem("px_workspace", JSON.stringify(data.workspace));
}

export async function ensureAuth(): Promise<boolean> {
  const existing = getToken();
  if (existing) {
    try {
      const r = await fetch(`${BASE}/auth/me`, { headers: { Authorization: `Bearer ${existing}` } });
      if (r.ok) return true;
    } catch { return true; /* backend unreachable but we have a token */ }
  }

  // Try login first
  try {
    const r = await fetch(`${BASE}/auth/login`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email: EMAIL, password: PASS }),
    });
    if (r.ok) { store(await r.json()); return true; }
  } catch { /* ignore */ }

  // Register if login failed
  try {
    const r = await fetch(`${BASE}/auth/register`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: "Developer", email: EMAIL, password: PASS, workspace_name: "My Workspace" }),
    });
    if (r.ok) { store(await r.json()); return true; }
  } catch { /* ignore */ }

  return false;
}

export function logout() {
  localStorage.removeItem("px_token");
  localStorage.removeItem("px_user");
  localStorage.removeItem("px_workspace");
}
