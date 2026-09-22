import { useState, useEffect, useRef, useCallback } from "react";
import { api, SSE_BASE } from "../lib/api";

export type AgentStatus = "idle"|"running"|"paused"|"error"|"stopped";

export interface AgentState {
  id: string; name: string; emoji: string; status: AgentStatus;
  leads_found: number; leads_verified: number; errors: number;
  last_error: string|null; last_active: string|null; cycle_count: number;
  current_query: string; search_targets: string[]; primary_source: string;
  internals: Record<string,unknown>;
}
export interface CoordinatorState {
  id: string; name: string; emoji: string; status: AgentStatus;
  total_received: number; total_verified: number; total_rejected: number;
  total_saved: number; total_duplicates: number; queue_depth: number;
}
export interface SessionLead {
  business_name: string; address: string; phone: string; email: string;
  website: string; rating: string; score: number; priority: string;
  issues_found: string[]; from_agent: string; saved: boolean; timestamp: string;
}
export interface AgentEvent {
  agent_id: string; event_type: string; payload: Record<string,unknown>; timestamp: string;
}

export const AGENT_CFG: Record<string, { label:string; sub:string; emoji:string; color:string; bg:string; bg2:string }> = {
  website_dev:          { label:"WEBVERSE",   sub:"Web Dev",   emoji:"💻", color:"#818cf8", bg:"#1e1b4b", bg2:"#3730a3" },
  seo_audit:            { label:"SEOVERSE",   sub:"SEO Audit", emoji:"🎨", color:"#fbbf24", bg:"#292400", bg2:"#b45309" },
  inventory_systems:    { label:"STOCKVERSE", sub:"Inventory", emoji:"📦", color:"#34d399", bg:"#022c22", bg2:"#065f46" },
  analytics_dashboards: { label:"DATAVERSE",  sub:"Analytics", emoji:"📊", color:"#60a5fa", bg:"#0c1a2e", bg2:"#1e40af" },
  ai_assistants:        { label:"AIVERSE",    sub:"AI Agents", emoji:"🧠", color:"#c084fc", bg:"#1a0a2e", bg2:"#6b21a8" },
};

export function useAgents() {
  const [agents,       setAgents]       = useState<AgentState[]>([]);
  const [coordinator,  setCoordinator]  = useState<CoordinatorState|null>(null);
  const [leads,        setLeads]        = useState<SessionLead[]>([]);
  const [events,       setEvents]       = useState<AgentEvent[]>([]);
  const [connected,    setConnected]    = useState(false);
  const [loading,      setLoading]      = useState(true);
  const esRef = useRef<EventSource|null>(null);

  const fetchSnap = useCallback(async () => {
    try {
      const d = await api.get<{ agents: AgentState[]; coordinator: CoordinatorState }>("/agents");
      setAgents(d.agents ?? []);
      setCoordinator(d.coordinator ?? null);
    } catch { /* ignore */ } finally { setLoading(false); }
  }, []);

  const connectSSE = useCallback(() => {
    esRef.current?.close();
    const tok = localStorage.getItem("px_token");
    if (!tok) return;
    const es = new EventSource(`${SSE_BASE}/agents/stream?token=${encodeURIComponent(tok)}`);
    esRef.current = es;
    es.onopen  = () => setConnected(true);
    es.onerror = () => setConnected(false);
    es.onmessage = (e) => {
      try {
        const ev: AgentEvent = JSON.parse(e.data);
        if (ev.event_type === "snapshot") {
          const p = ev.payload as { agents: AgentState[]; coordinator: CoordinatorState };
          setAgents(p.agents ?? []); setCoordinator(p.coordinator ?? null); setConnected(true);
        } else if (ev.event_type === "status_change") {
          const p = ev.payload as { new: AgentStatus };
          setAgents(prev => prev.map(a => a.id === ev.agent_id ? { ...a, status: p.new } : a));
        } else if (ev.event_type === "lead_found") {
          setAgents(prev => prev.map(a => a.id === ev.agent_id ? { ...a, leads_found: a.leads_found+1, last_active: ev.timestamp } : a));
          setEvents(prev => [ev, ...prev].slice(0, 200));
        } else if (ev.event_type === "verified") {
          const lead = ev.payload as unknown as SessionLead;
          setLeads(prev => [lead, ...prev].slice(0, 200));
          setCoordinator(prev => prev ? { ...prev, total_verified: prev.total_verified+1, total_received: prev.total_received+1 } : prev);
          setEvents(prev => [ev, ...prev].slice(0, 200));
        } else if (ev.event_type === "heartbeat" && ev.agent_id === "coordinator") {
          const p = ev.payload as Record<string,number>;
          setCoordinator(prev => prev ? { ...prev, total_received: p.total_received??prev.total_received, total_verified: p.total_verified??prev.total_verified } : prev);
          setConnected(true);
        } else if (ev.event_type === "error") {
          setAgents(prev => prev.map(a => a.id === ev.agent_id ? { ...a, status:"error", errors:a.errors+1, last_error:(ev.payload.message as string)||"Unknown" } : a));
        }
      } catch { /* ignore */ }
    };
  }, []);

  useEffect(() => {
    fetchSnap();
    connectSSE();
    return () => { esRef.current?.close(); };
  }, [fetchSnap, connectSSE]);

  const startAll = useCallback(async (location: string, maxLeads: number, category?: string) => {
    await api.post("/agents/start", { location, max_leads: maxLeads, category: category ?? null });
    await fetchSnap();
  }, [fetchSnap]);

  const stopAll = useCallback(async () => {
    await api.post("/agents/stop-all", {});
    await fetchSnap();
  }, [fetchSnap]);

  return { agents, coordinator, leads, events, connected, loading, startAll, stopAll, refresh: fetchSnap };
}
