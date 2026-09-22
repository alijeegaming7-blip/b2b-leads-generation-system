import { motion, AnimatePresence } from "framer-motion";
import { X, Activity, Target, TrendingUp, Clock, Search, AlertCircle, CheckCircle2, Zap } from "lucide-react";

interface AgentState {
  id: string; name: string; emoji: string; status: string;
  leads_found: number; leads_verified: number; errors: number;
  last_error: string | null; last_active: string | null; cycle_count: number;
  current_query: string; search_targets: string[]; primary_source: string;
  internals: Record<string, any>;
}

interface Props {
  agent: AgentState | null;
  onClose: () => void;
  color: string;
}

const STATUS_COLORS: Record<string, string> = {
  running: "#fbbf24",
  idle: "#6b7280",
  stopped: "#475569",
  error: "#f87171",
};

export default function AgentDetailModal({ agent, onClose, color }: Props) {
  if (!agent) return null;

  const statusColor = STATUS_COLORS[agent.status] || "#6b7280";
  const internals = agent.internals || {};

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        style={{
          position: "fixed", inset: 0, zIndex: 500,
          background: "rgba(0,0,0,.85)", backdropFilter: "blur(4px)",
          display: "flex", alignItems: "center", justifyContent: "center",
          padding: "20px",
        }}
        onClick={onClose}
      >
        <motion.div
          initial={{ scale: 0.95, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          exit={{ scale: 0.95, opacity: 0 }}
          transition={{ type: "spring", damping: 25 }}
          style={{
            background: "#0d0d1f", border: `1px solid ${color}33`,
            borderRadius: 24, maxWidth: 720, width: "100%",
            maxHeight: "90vh", overflowY: "auto",
            boxShadow: `0 0 80px ${color}22`,
          }}
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div style={{ padding: "24px 28px", borderBottom: `1px solid ${color}22`, background: `linear-gradient(135deg, ${color}11 0%, transparent 100%)` }}>
            <div style={{ display: "flex", alignItems: "flex-start", gap: 16 }}>
              <div style={{ width: 56, height: 56, borderRadius: 16, background: `${color}22`, border: `2px solid ${color}44`, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 28 }}>
                {agent.emoji}
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <h2 style={{ fontSize: 20, fontWeight: 700, color: "#fff", margin: 0, marginBottom: 4 }}>{internals.name || agent.name}</h2>
                <p style={{ fontSize: 13, color: "#9ca3af", lineHeight: 1.5, margin: 0, marginBottom: 8 }}>{internals.description || agent.name}</p>
                <div style={{ display: "flex", alignItems: "center", gap: 8, flexWrap: "wrap" }}>
                  <span style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 10px", borderRadius: 12, fontSize: 11, fontWeight: 600, background: `${statusColor}22`, color: statusColor, textTransform: "uppercase", letterSpacing: "0.05em" }}>
                    {agent.status === "running" ? <Activity style={{ width: 11, height: 11 }} /> : <Clock style={{ width: 11, height: 11 }} />}
                    {agent.status}
                  </span>
                  <span style={{ fontSize: 11, color: "#4b5563" }}>•</span>
                  <span style={{ fontSize: 11, color: "#6b7280" }}>{agent.cycle_count} cycles completed</span>
                </div>
              </div>
              <button onClick={onClose} style={{ background: "rgba(255,255,255,.06)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 10, width: 36, height: 36, display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer", color: "#9ca3af" }}>
                <X style={{ width: 18, height: 18 }} />
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 1, background: "rgba(255,255,255,.04)" }}>
            <div style={{ padding: "16px 20px", background: "#0d0d1f", textAlign: "center" }}>
              <div style={{ fontSize: 26, fontWeight: 700, color: color, marginBottom: 4 }}>{agent.leads_found}</div>
              <div style={{ fontSize: 10, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Leads Found</div>
            </div>
            <div style={{ padding: "16px 20px", background: "#0d0d1f", textAlign: "center" }}>
              <div style={{ fontSize: 26, fontWeight: 700, color: "#34d399", marginBottom: 4 }}>{agent.leads_verified}</div>
              <div style={{ fontSize: 10, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Verified</div>
            </div>
            <div style={{ padding: "16px 20px", background: "#0d0d1f", textAlign: "center" }}>
              <div style={{ fontSize: 26, fontWeight: 700, color: agent.errors > 0 ? "#f87171" : "#4b5563", marginBottom: 4 }}>{agent.errors}</div>
              <div style={{ fontSize: 10, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em" }}>Errors</div>
            </div>
          </div>

          {/* Current Activity */}
          {agent.current_query && (
            <div style={{ padding: "20px 28px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <Search style={{ width: 14, height: 14, color: color }} />
                <h3 style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Current Search</h3>
              </div>
              <div style={{ padding: "12px 14px", background: `${color}08`, border: `1px solid ${color}22`, borderRadius: 12 }}>
                <p style={{ fontSize: 13, color: "#d1d5db", margin: 0 }}>"{agent.current_query}"</p>
              </div>
            </div>
          )}

          {/* Strategy */}
          {internals.strategy && (
            <div style={{ padding: "20px 28px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <Target style={{ width: 14, height: 14, color: color }} />
                <h3 style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Strategy</h3>
              </div>
              <p style={{ fontSize: 13, color: "#9ca3af", lineHeight: 1.7, margin: 0 }}>{internals.strategy}</p>
            </div>
          )}

          {/* Value Proposition */}
          {internals.value_proposition && (
            <div style={{ padding: "20px 28px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
                <TrendingUp style={{ width: 14, height: 14, color: "#34d399" }} />
                <h3 style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Value Proposition</h3>
              </div>
              <p style={{ fontSize: 13, color: "#9ca3af", lineHeight: 1.7, margin: 0 }}>{internals.value_proposition}</p>
            </div>
          )}

          {/* Ideal Customer Profile */}
          {internals.ideal_customer_profile && Array.isArray(internals.ideal_customer_profile) && (
            <div style={{ padding: "20px 28px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <CheckCircle2 style={{ width: 14, height: 14, color: "#60a5fa" }} />
                <h3 style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Ideal Customer Profile</h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {internals.ideal_customer_profile.map((item: string, i: number) => (
                  <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 10 }}>
                    <div style={{ width: 6, height: 6, borderRadius: "50%", background: color, marginTop: 6, flexShrink: 0 }} />
                    <p style={{ fontSize: 12, color: "#9ca3af", lineHeight: 1.6, margin: 0 }}>{item}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Qualifying Questions */}
          {internals.qualifying_questions && Array.isArray(internals.qualifying_questions) && (
            <div style={{ padding: "20px 28px", borderBottom: "1px solid rgba(255,255,255,.06)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Zap style={{ width: 14, height: 14, color: "#fbbf24" }} />
                <h3 style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Qualifying Questions</h3>
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
                {internals.qualifying_questions.map((q: string, i: number) => (
                  <div key={i} style={{ padding: "10px 12px", background: "rgba(251,191,36,.06)", border: "1px solid rgba(251,191,36,.15)", borderRadius: 10 }}>
                    <p style={{ fontSize: 12, color: "#fbbf24", lineHeight: 1.6, margin: 0 }}>💬 {q}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Search Targets */}
          {agent.search_targets && agent.search_targets.length > 0 && (
            <div style={{ padding: "20px 28px" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
                <Search style={{ width: 14, height: 14, color: "#9ca3af" }} />
                <h3 style={{ fontSize: 12, fontWeight: 600, color: "#6b7280", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Search Targets ({agent.search_targets.length})</h3>
              </div>
              <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                {agent.search_targets.slice(0, 20).map((target, i) => (
                  <span key={i} style={{ padding: "4px 10px", background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.08)", borderRadius: 8, fontSize: 11, color: "#9ca3af" }}>
                    {target}
                  </span>
                ))}
                {agent.search_targets.length > 20 && (
                  <span style={{ padding: "4px 10px", background: "rgba(255,255,255,.03)", borderRadius: 8, fontSize: 11, color: "#6b7280" }}>
                    +{agent.search_targets.length - 20} more
                  </span>
                )}
              </div>
            </div>
          )}

          {/* Last Error */}
          {agent.last_error && (
            <div style={{ padding: "20px 28px", background: "rgba(248,113,113,.05)", borderTop: "1px solid rgba(248,113,113,.2)" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8 }}>
                <AlertCircle style={{ width: 14, height: 14, color: "#f87171" }} />
                <h3 style={{ fontSize: 12, fontWeight: 600, color: "#f87171", textTransform: "uppercase", letterSpacing: "0.1em", margin: 0 }}>Last Error</h3>
              </div>
              <p style={{ fontSize: 12, color: "#fca5a5", lineHeight: 1.6, margin: 0, fontFamily: "monospace" }}>{agent.last_error}</p>
            </div>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
