import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Check, Loader2, ExternalLink, AlertCircle, Zap, Eye, EyeOff, ChevronRight, RefreshCw } from "lucide-react";
import { api } from "../lib/api";
import { useDemo } from "../hooks/useDemo";

// ── Types ─────────────────────────────────────────────────────────────────────
interface Connector {
  name: string;
  display_name: string;
  requires_api_key: boolean;
  is_enabled: boolean;
  is_configured: boolean;
}

interface Props {
  onClose: () => void;
  onConnectorChange?: () => void;
}

// ── Per-connector metadata ─────────────────────────────────────────────────────
const META: Record<string, {
  icon: string; color: string; description: string;
  getKeyUrl?: string; badge?: string; keyPlaceholder?: string;
}> = {
  google_maps: {
    icon: "🗺️", color: "#4285f4",
    description: "Scrape businesses from Google Maps — extracts email, phone, social media automatically",
    badge: "Free · Always On",
  },
  yelp: {
    icon: "⭐", color: "#d32323",
    description: "Yelp Fusion API — businesses with ratings, reviews, categories",
    getKeyUrl: "https://www.yelp.com/developers/v3/manage_app",
    badge: "5,000/mo free",
    keyPlaceholder: "Paste Yelp API key here…",
  },
  yellowpages: {
    icon: "📞", color: "#f5c518",
    description: "Yellow Pages US directory — verified phone numbers",
    badge: "Free · US Only",
  },
  facebook: {
    icon: "👤", color: "#1877f2",
    description: "Facebook Business pages (experimental — may be blocked)",
    badge: "Experimental",
  },
  linkedin: {
    icon: "💼", color: "#0a66c2",
    description: "B2B companies & decision-makers via Proxycurl API",
    getKeyUrl: "https://nubela.co/proxycurl/",
    badge: "B2B · Best for leads",
    keyPlaceholder: "Paste Proxycurl API key…",
  },
  apollo: {
    icon: "🚀", color: "#5b47fb",
    description: "Apollo.io — verified B2B emails + direct phone numbers",
    getKeyUrl: "https://app.apollo.io/#/settings/integrations/api",
    badge: "50 free/mo",
    keyPlaceholder: "Paste Apollo API key…",
  },
  hunter: {
    icon: "🔍", color: "#ff6b35",
    description: "Hunter.io — find & verify professional email addresses",
    getKeyUrl: "https://hunter.io/api_keys",
    badge: "50 free/mo",
    keyPlaceholder: "Paste Hunter API key…",
  },
  clearbit: {
    icon: "💎", color: "#4a90e2",
    description: "Clearbit — company enrichment with industry & tech data",
    getKeyUrl: "https://dashboard.clearbit.com/api",
    keyPlaceholder: "Paste Clearbit API key…",
  },
  crunchbase: {
    icon: "💰", color: "#0288d1",
    description: "Crunchbase — startup & funding data",
    getKeyUrl: "https://data.crunchbase.com/docs",
    keyPlaceholder: "Paste Crunchbase API key…",
  },
  twitter: {
    icon: "🐦", color: "#1da1f2",
    description: "Twitter/X Business API — find business accounts",
    getKeyUrl: "https://developer.twitter.com/en/portal/dashboard",
    keyPlaceholder: "Paste Twitter Bearer token…",
  },
  zoominfo: {
    icon: "📊", color: "#e8710a",
    description: "ZoomInfo enterprise database (requires sales contract)",
    getKeyUrl: "https://www.zoominfo.com/",
    badge: "Enterprise",
    keyPlaceholder: "ZoomInfo API key…",
  },
};

// ── Component ─────────────────────────────────────────────────────────────────
export default function ConnectorPanel({ onClose, onConnectorChange }: Props) {
  const demo = useDemo();
  const [connectors,  setConnectors]  = useState<Connector[]>([]);
  const [loading,     setLoading]     = useState(true);
  const [refreshing,  setRefreshing]  = useState(false);
  const [error,       setError]       = useState<string | null>(null);
  const [apiKeys,     setApiKeys]     = useState<Record<string, string>>({});
  const [showKey,     setShowKey]     = useState<Record<string, boolean>>({});
  const [updating,    setUpdating]    = useState<string | null>(null);
  const [saved,       setSaved]       = useState<Record<string, boolean>>({});
  const [testResults, setTestResults] = useState<Record<string, { ok: boolean; msg: string }>>({});
  const [testing,     setTesting]     = useState<string | null>(null);
  const [tab,         setTab]         = useState<"all" | "enabled">("all");
  const inputRefs = useRef<Record<string, HTMLInputElement | null>>({});

  useEffect(() => { load(); }, []);

  async function load(quiet = false) {
    if (!quiet) setLoading(true);
    else setRefreshing(true);
    setError(null);
    try {
      const data = await api.get<Connector[]>("/connectors");
      setConnectors(Array.isArray(data) ? data : []);
    } catch (err: any) {
      setError(
        err?.message?.includes("401")
          ? "Session expired — please refresh the page and log in again."
          : err?.message || "Cannot reach backend. Make sure it is running on port 3001."
      );
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  async function toggle(name: string, enabled: boolean) {
    setUpdating(name);
    setError(null);
    try {
      await api.put(`/connectors/${name}/config`, {
        enabled,
        api_key: apiKeys[name]?.trim() || null,
      });
      await load(true);
      onConnectorChange?.();
      // Auto-focus API key input when enabling a connector that needs a key
      if (enabled) {
        setTimeout(() => inputRefs.current[name]?.focus(), 200);
      }
    } catch (err: any) {
      setError(`Could not update "${name}": ${err?.message}`);
    } finally {
      setUpdating(null);
    }
  }

  async function saveKey(name: string) {
    const key = apiKeys[name]?.trim();
    if (!key) { inputRefs.current[name]?.focus(); return; }
    setUpdating(name);
    setError(null);
    try {
      const conn = connectors.find(c => c.name === name);
      await api.put(`/connectors/${name}/config`, {
        enabled: conn?.is_enabled ?? true,   // auto-enable on key save
        api_key: key,
      });
      setSaved(prev => ({ ...prev, [name]: true }));
      setTimeout(() => setSaved(prev => ({ ...prev, [name]: false })), 2500);
      await load(true);
      onConnectorChange?.();
    } catch (err: any) {
      setError(`Key save failed for "${name}": ${err?.message}`);
    } finally {
      setUpdating(null);
    }
  }

  async function testConnector(name: string) {
    setTesting(name);
    setTestResults(prev => ({ ...prev, [name]: { ok: false, msg: "Testing…" } }));
    try {
      const res = await api.post<any>("/connectors/test", {
        connector_name: name,
        query: "restaurant",
        location: "New York, NY",
        limit: 3,
      });
      const count = res.results_count ?? 0;
      setTestResults(prev => ({
        ...prev,
        [name]: {
          ok: count > 0,
          msg: count > 0
            ? `✅ Working — found ${count} results`
            : "⚠️ Connected but 0 results returned",
        },
      }));
    } catch (err: any) {
      setTestResults(prev => ({
        ...prev,
        [name]: { ok: false, msg: `❌ ${err?.message || "Test failed — check API key"}` },
      }));
    } finally {
      setTesting(null);
    }
  }

  const shown          = tab === "enabled" ? connectors.filter(c => c.is_enabled) : connectors;
  const enabledCount   = connectors.filter(c => c.is_enabled).length;
  const readyCount     = connectors.filter(c => c.is_enabled && c.is_configured).length;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        style={{ position: "fixed", inset: 0, zIndex: 600, background: "rgba(0,0,0,.9)", backdropFilter: "blur(8px)", display: "flex", alignItems: "center", justifyContent: "center", padding: 20 }}
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.94, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.94, opacity: 0 }}
          transition={{ type: "spring", damping: 26, stiffness: 280 }}
          style={{ background: "#0a0a1e", border: "1px solid rgba(52,211,153,.3)", borderRadius: 24, width: "100%", maxWidth: 900, maxHeight: "92vh", overflowY: "auto", boxShadow: "0 0 100px rgba(52,211,153,.15), 0 30px 80px rgba(0,0,0,.8)" }}
          onClick={e => e.stopPropagation()}
        >
          {/* ── Header ── */}
          <div style={{ padding: "22px 28px 18px", borderBottom: "1px solid rgba(255,255,255,.08)", background: "linear-gradient(135deg, rgba(52,211,153,.08) 0%, transparent 60%)", position: "sticky", top: 0, zIndex: 10, backdropFilter: "blur(12px)" }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 14 }}>
              <div style={{ width: 54, height: 54, borderRadius: 16, background: "linear-gradient(135deg,#34d399,#059669)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 0 28px rgba(52,211,153,.35)", flexShrink: 0 }}>
                <Zap style={{ width: 28, height: 28, color: "#fff" }} />
              </div>
              <div style={{ flex: 1 }}>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: "#fff", margin: "0 0 4px" }}>Lead Source Connectors</h2>
                <p style={{ fontSize: 12, color: "#9ca3af", margin: 0, lineHeight: 1.5 }}>
                  Connect data sources — all enabled connectors run automatically when you start agents
                </p>
                <div style={{ display: "flex", gap: 10, marginTop: 10, flexWrap: "wrap" }}>
                  <span style={{ fontSize: 11, fontWeight: 700, padding: "3px 10px", borderRadius: 20, background: "rgba(52,211,153,.15)", color: "#34d399", border: "1px solid rgba(52,211,153,.25)" }}>
                    {readyCount} Ready / {enabledCount} Enabled
                  </span>
                  <span style={{ fontSize: 11, color: "#6b7280" }}>{connectors.length} connectors total</span>
                </div>
              </div>
              <div style={{ display: "flex", gap: 8 }}>
                <button onClick={() => load(true)} disabled={refreshing}
                  style={{ width: 34, height: 34, borderRadius: 10, background: "rgba(255,255,255,.06)", border: "1px solid rgba(255,255,255,.1)", color: "#9ca3af", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <RefreshCw style={{ width: 15, height: 15, animation: refreshing ? "spin .8s linear infinite" : "none" }} />
                  <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
                </button>
                <button onClick={onClose}
                  style={{ width: 34, height: 34, borderRadius: 10, background: "rgba(255,255,255,.06)", border: "1px solid rgba(255,255,255,.1)", color: "#9ca3af", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
                  <X style={{ width: 16, height: 16 }} />
                </button>
              </div>
            </div>
          </div>

          {/* ── Tab bar ── */}
          <div style={{ display: "flex", gap: 4, padding: "12px 28px", borderBottom: "1px solid rgba(255,255,255,.06)", background: "rgba(0,0,0,.2)" }}>
            {(["all", "enabled"] as const).map(t => (
              <button key={t} onClick={() => setTab(t)}
                style={{ padding: "7px 18px", borderRadius: 8, border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600, transition: "all .15s", background: tab === t ? "rgba(52,211,153,.2)" : "transparent", color: tab === t ? "#34d399" : "#6b7280" }}>
                {t === "all" ? `All Connectors (${connectors.length})` : `Enabled (${enabledCount})`}
              </button>
            ))}
          </div>

          {/* Demo mode banner inside panel */}
          {demo.demo_mode && (
            <div style={{ margin: "12px 28px 0", padding: "12px 16px", background: "linear-gradient(135deg,rgba(251,191,36,.15),rgba(124,58,237,.15))", border: "1px solid rgba(251,191,36,.35)", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "space-between", gap: 12, flexWrap: "wrap" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontSize: 18 }}>🔒</span>
                <div>
                  <p style={{ fontSize: 12, fontWeight: 700, color: "#fbbf24", margin: 0 }}>Demo Mode — Only Google Maps is active</p>
                  <p style={{ fontSize: 11, color: "#9ca3af", margin: 0 }}>Buy the full system to unlock Yelp, LinkedIn, Apollo, Hunter and 7 more</p>
                </div>
              </div>
              <a href={demo.buy_link || "#"} target="_blank" rel="noreferrer"
                style={{ flexShrink: 0, padding: "7px 16px", borderRadius: 8, background: "#fbbf24", color: "#1a1a1a", fontWeight: 800, fontSize: 12, textDecoration: "none" }}>
                Buy Full System
              </a>
            </div>
          )}

          {/* ── Error banner ── */}
          {error && (
            <div style={{ margin: "12px 28px 0", padding: "12px 16px", background: "rgba(248,113,113,.1)", border: "1px solid rgba(248,113,113,.25)", borderRadius: 10, fontSize: 12, color: "#f87171", display: "flex", gap: 8, alignItems: "flex-start" }}>
              <AlertCircle style={{ width: 14, height: 14, flexShrink: 0, marginTop: 1 }} />
              <span style={{ flex: 1 }}>{error}</span>
              <button onClick={() => setError(null)} style={{ background: "none", border: "none", color: "#f87171", cursor: "pointer", fontSize: 16, lineHeight: 1 }}>×</button>
            </div>
          )}

          {/* ── Connector grid ── */}
          <div style={{ padding: "16px 28px 28px" }}>
            {loading ? (
              <div style={{ display: "flex", alignItems: "center", justifyContent: "center", padding: "60px 0", color: "#6b7280", gap: 12, flexDirection: "column" }}>
                <Loader2 style={{ width: 28, height: 28, animation: "spin .8s linear infinite" }} />
                <p style={{ fontSize: 13, margin: 0 }}>Loading connectors…</p>
              </div>
            ) : shown.length === 0 ? (
              <div style={{ textAlign: "center", padding: "60px 0", color: "#4b5563" }}>
                <p style={{ fontSize: 14 }}>No connectors enabled yet.</p>
                <button onClick={() => setTab("all")} style={{ marginTop: 10, padding: "8px 16px", borderRadius: 8, background: "#4f46e5", border: "none", color: "#fff", fontSize: 12, cursor: "pointer" }}>View All</button>
              </div>
            ) : (
              <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(390px, 1fr))", gap: 14 }}>
                {shown.map(conn => {
                  const meta     = META[conn.name] || { icon: "🔌", color: "#6b7280", description: "" };
                  const busy     = updating === conn.name;
                  const isTest   = testing  === conn.name;
                  const isSaved  = saved[conn.name];
                  const testR    = testResults[conn.name];
                  const keyVal   = apiKeys[conn.name] ?? "";

                  const statusColor  = conn.is_configured ? "#34d399" : conn.is_enabled ? "#fbbf24" : "#4b5563";
                  const statusText   = conn.is_configured ? "Ready" : conn.is_enabled ? "Needs API key" : "Disabled";

                  return (
                    <div key={conn.name} style={{
                      padding: 18,
                      background: "rgba(255,255,255,.03)",
                      border: `1px solid ${conn.is_enabled ? (conn.is_configured ? "rgba(52,211,153,.25)" : "rgba(251,191,36,.2)") : "rgba(255,255,255,.07)"}`,
                      borderRadius: 16, display: "flex", flexDirection: "column", gap: 12,
                      transition: "all .2s",
                    }}>

                      {/* Top row */}
                      <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
                        <span style={{ fontSize: 30, lineHeight: 1, flexShrink: 0 }}>{meta.icon}</span>
                        <div style={{ flex: 1, minWidth: 0 }}>
                          <div style={{ display: "flex", alignItems: "center", gap: 7, flexWrap: "wrap", marginBottom: 4 }}>
                            <h3 style={{ fontSize: 14, fontWeight: 700, color: "#fff", margin: 0 }}>{conn.display_name}</h3>
                            {meta.badge && <span style={{ fontSize: 10, padding: "1px 8px", borderRadius: 10, fontWeight: 600, background: `${meta.color}20`, color: meta.color, border: `1px solid ${meta.color}35` }}>{meta.badge}</span>}
                          </div>
                          <p style={{ fontSize: 11, color: "#6b7280", margin: 0, lineHeight: 1.5 }}>{meta.description}</p>
                        </div>

                        {/* Enable / Disable — locked in demo for non-google connectors */}
                        {demo.demo_mode && conn.name !== "google_maps" ? (
                          <a href={demo.buy_link || "#"} target="_blank" rel="noreferrer"
                            style={{ flexShrink: 0, display: "inline-flex", alignItems: "center", gap: 5, padding: "6px 14px", borderRadius: 8, fontSize: 12, fontWeight: 700, background: "rgba(251,191,36,.2)", color: "#fbbf24", textDecoration: "none", border: "1px solid rgba(251,191,36,.3)" }}>
                            🔒 Buy to Unlock
                          </a>
                        ) : (
                          <button onClick={() => toggle(conn.name, !conn.is_enabled)} disabled={busy}
                            style={{ flexShrink: 0, padding: "6px 16px", borderRadius: 8, border: "none", cursor: busy ? "wait" : "pointer", fontSize: 12, fontWeight: 700, transition: "all .15s", background: conn.is_enabled ? "rgba(248,113,113,.18)" : "rgba(52,211,153,.18)", color: conn.is_enabled ? "#f87171" : "#34d399" }}>
                            {busy ? <Loader2 style={{ width: 12, height: 12, animation: "spin .8s linear infinite" }} /> : conn.is_enabled ? "Disable" : "Enable"}
                          </button>
                        )}
                      </div>

                      {/* Status indicator */}
                      <div style={{ display: "flex", alignItems: "center", gap: 7 }}>
                        <div style={{ width: 8, height: 8, borderRadius: "50%", background: statusColor, boxShadow: `0 0 8px ${statusColor}88`, flexShrink: 0 }} />
                        <span style={{ fontSize: 11, fontWeight: 600, color: statusColor }}>{statusText}</span>
                        {conn.is_enabled && !conn.requires_api_key && (
                          <span style={{ fontSize: 10, color: "#34d399", marginLeft: 4 }}>— No API key needed</span>
                        )}
                      </div>

                      {/* API key input (shown when enabled AND requires key) */}
                      {conn.is_enabled && conn.requires_api_key && (
                        <div>
                          <label style={{ display: "block", fontSize: 10, fontWeight: 700, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", marginBottom: 6 }}>
                            API Key
                          </label>
                          <div style={{ display: "flex", gap: 8 }}>
                            <div style={{ position: "relative", flex: 1 }}>
                              <input
                                ref={el => { inputRefs.current[conn.name] = el; }}
                                type={showKey[conn.name] ? "text" : "password"}
                                value={keyVal}
                                onChange={e => setApiKeys(prev => ({ ...prev, [conn.name]: e.target.value }))}
                                onKeyDown={e => { if (e.key === "Enter") saveKey(conn.name); }}
                                placeholder={meta.keyPlaceholder || `${conn.display_name} API key…`}
                                style={{ width: "100%", height: 38, background: "rgba(255,255,255,.07)", border: `1px solid ${keyVal ? "rgba(129,140,248,.4)" : "rgba(255,255,255,.12)"}`, borderRadius: 8, padding: "0 38px 0 12px", fontSize: 12, color: "#fff", outline: "none", boxSizing: "border-box", transition: "border-color .15s" }}
                              />
                              <button onClick={() => setShowKey(prev => ({ ...prev, [conn.name]: !prev[conn.name] }))}
                                style={{ position: "absolute", right: 8, top: "50%", transform: "translateY(-50%)", background: "none", border: "none", cursor: "pointer", color: "#6b7280", padding: 0, display: "flex" }}>
                                {showKey[conn.name] ? <EyeOff style={{ width: 14, height: 14 }} /> : <Eye style={{ width: 14, height: 14 }} />}
                              </button>
                            </div>
                            <button onClick={() => saveKey(conn.name)} disabled={!keyVal || busy}
                              style={{ flexShrink: 0, padding: "0 16px", height: 38, borderRadius: 8, border: "none", fontSize: 12, fontWeight: 700, cursor: keyVal && !busy ? "pointer" : "not-allowed", background: isSaved ? "#059669" : keyVal ? "#4f46e5" : "#1f2937", color: keyVal ? "#fff" : "#4b5563", transition: "all .2s", display: "flex", alignItems: "center", gap: 6 }}>
                              {busy ? <Loader2 style={{ width: 13, height: 13, animation: "spin .8s linear infinite" }} /> : isSaved ? <><Check style={{ width: 13, height: 13 }} />Saved!</> : "Save & Enable"}
                            </button>
                          </div>

                          {/* Get key link */}
                          {meta.getKeyUrl && (
                            <div style={{ marginTop: 8, display: "flex", alignItems: "center", gap: 8 }}>
                              <a href={meta.getKeyUrl} target="_blank" rel="noreferrer"
                                style={{ display: "inline-flex", alignItems: "center", gap: 4, fontSize: 11, color: "#818cf8", textDecoration: "none" }}>
                                <ExternalLink style={{ width: 11, height: 11 }} />
                                Get free API key →
                              </a>
                              <span style={{ fontSize: 10, color: "#374151" }}>— opens in new tab, then paste key above</span>
                            </div>
                          )}
                        </div>
                      )}

                      {/* Test button */}
                      {conn.is_enabled && conn.is_configured && (
                        <div>
                          <button onClick={() => testConnector(conn.name)} disabled={isTest}
                            style={{ display: "inline-flex", alignItems: "center", gap: 6, padding: "6px 14px", borderRadius: 8, background: "rgba(255,255,255,.06)", border: "1px solid rgba(255,255,255,.1)", color: "#9ca3af", fontSize: 11, cursor: isTest ? "wait" : "pointer", fontWeight: 600 }}>
                            {isTest ? <Loader2 style={{ width: 12, height: 12, animation: "spin .8s linear infinite" }} /> : <ChevronRight style={{ width: 12, height: 12 }} />}
                            {isTest ? "Testing…" : "Test Connection"}
                          </button>
                          {testR && (
                            <p style={{ fontSize: 11, marginTop: 6, color: testR.ok ? "#34d399" : "#f87171", margin: "6px 0 0" }}>{testR.msg}</p>
                          )}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* ── Footer tip ── */}
          <div style={{ padding: "14px 28px", borderTop: "1px solid rgba(255,255,255,.06)", background: "rgba(0,0,0,.2)", fontSize: 11, color: "#4b5563", display: "flex", alignItems: "center", gap: 8 }}>
            <Zap style={{ width: 12, height: 12, color: "#34d399" }} />
            <span>Agents automatically use ALL enabled+ready connectors in parallel. More connectors = more leads with more contact details.</span>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
