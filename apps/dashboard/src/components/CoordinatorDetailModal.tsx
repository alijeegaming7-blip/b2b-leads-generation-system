import { motion, AnimatePresence } from "framer-motion";
import { X, Zap, Activity, CheckCircle2, XCircle, AlertTriangle, TrendingUp, Database } from "lucide-react";

// Accepts the coordinator state shape from useAgents (no required `internals`)
interface CoordinatorState {
  id: string;
  name: string;
  emoji: string;
  status: string;
  total_received: number;
  total_verified: number;
  total_rejected: number;
  total_saved: number;
  total_duplicates: number;
  queue_depth: number;
  internals?: {
    strategy?: string;
    verification_steps?: string[];
    rejection_reasons?: string[];
    workspace_id?: string;
    campaign_id?: string;
  };
}

interface Props {
  coordinator: CoordinatorState | null;
  onClose: () => void;
}

const DEFAULT_STEPS = [
  "1. Deduplicate by (business_name + address) hash",
  "2. Validate email format (RFC 5322 regex)",
  "3. Validate phone number (7-15 digits, E.164)",
  "4. Score lead 0-100 using AI intelligence engine",
  "5. Save to database with full enriched data",
  "6. Emit verified event to live network visualization",
];

const DEFAULT_REASONS = [
  "Duplicate lead already in database",
  "No business name",
  "Score < 20 (very low quality lead)",
];

export default function CoordinatorDetailModal({ coordinator, onClose }: Props) {
  if (!coordinator) return null;

  const internals = coordinator.internals ?? {};
  const steps     = internals.verification_steps   ?? DEFAULT_STEPS;
  const reasons   = internals.rejection_reasons    ?? DEFAULT_REASONS;
  const strategy  = internals.strategy             ?? "Receives leads from all 5 specialist agents, verifies, deduplicates, scores, and saves to database.";
  const wsId      = internals.workspace_id         ?? "—";
  const camId     = internals.campaign_id          ?? "—";

  const saveRate   = coordinator.total_received > 0
    ? Math.round((coordinator.total_saved    / coordinator.total_received) * 100) : 0;
  const rejectRate = coordinator.total_received > 0
    ? Math.round((coordinator.total_rejected / coordinator.total_received) * 100) : 0;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
        style={{ position:"fixed", inset:0, zIndex:500, background:"rgba(0,0,0,.85)", backdropFilter:"blur(4px)", display:"flex", alignItems:"center", justifyContent:"center", padding:"20px" }}
        onClick={onClose}
      >
        <motion.div
          initial={{ scale:0.95, opacity:0 }} animate={{ scale:1, opacity:1 }} exit={{ scale:0.95, opacity:0 }}
          transition={{ type:"spring", damping:25 }}
          style={{ background:"#0d0d1f", border:"1px solid rgba(251,191,36,.3)", borderRadius:24, maxWidth:720, width:"100%", maxHeight:"90vh", overflowY:"auto", boxShadow:"0 0 100px rgba(251,191,36,.2), 0 20px 60px rgba(0,0,0,.8)" }}
          onClick={e => e.stopPropagation()}
        >
          {/* Header */}
          <div style={{ padding:"24px 28px", borderBottom:"1px solid rgba(251,191,36,.2)", background:"linear-gradient(135deg, rgba(251,191,36,.15) 0%, transparent 100%)" }}>
            <div style={{ display:"flex", alignItems:"flex-start", gap:16 }}>
              <div style={{ width:64, height:64, borderRadius:20, background:"linear-gradient(135deg,#fbbf24,#f59e0b)", border:"3px solid rgba(251,191,36,.4)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:36, boxShadow:"0 0 30px rgba(251,191,36,.3)" }}>⚡</div>
              <div style={{ flex:1, minWidth:0 }}>
                <h2 style={{ fontSize:22, fontWeight:700, color:"#fff", margin:"0 0 4px" }}>NEXUS — Central Coordinator</h2>
                <p style={{ fontSize:13, color:"#9ca3af", lineHeight:1.5, margin:"0 0 8px" }}>{strategy}</p>
                <div style={{ display:"flex", alignItems:"center", gap:8 }}>
                  <span style={{ display:"inline-flex", alignItems:"center", gap:4, padding:"3px 10px", borderRadius:12, fontSize:11, fontWeight:600, background:"rgba(251,191,36,.2)", color:"#fbbf24", textTransform:"uppercase", letterSpacing:"0.05em" }}>
                    <Activity style={{ width:11, height:11 }} />{coordinator.status}
                  </span>
                  <span style={{ fontSize:11, color:"#4b5563" }}>•</span>
                  <span style={{ fontSize:11, color:"#6b7280" }}>Queue: {coordinator.queue_depth} pending</span>
                </div>
              </div>
              <button onClick={onClose} style={{ background:"rgba(255,255,255,.06)", border:"1px solid rgba(255,255,255,.1)", borderRadius:10, width:36, height:36, display:"flex", alignItems:"center", justifyContent:"center", cursor:"pointer", color:"#9ca3af" }}>
                <X style={{ width:18, height:18 }} />
              </button>
            </div>
          </div>

          {/* Stats Grid */}
          <div style={{ display:"grid", gridTemplateColumns:"repeat(5,1fr)", gap:1, background:"rgba(255,255,255,.04)" }}>
            {[
              { label:"Received",   value:coordinator.total_received,   color:"#60a5fa" },
              { label:"Verified",   value:coordinator.total_verified,   color:"#34d399" },
              { label:"Saved",      value:coordinator.total_saved,      color:"#fbbf24" },
              { label:"Rejected",   value:coordinator.total_rejected,   color:"#f87171" },
              { label:"Duplicates", value:coordinator.total_duplicates, color:"#9ca3af" },
            ].map(s => (
              <div key={s.label} style={{ padding:"16px 12px", background:"#0d0d1f", textAlign:"center" }}>
                <div style={{ fontSize:24, fontWeight:700, color:s.color, marginBottom:4 }}>{s.value}</div>
                <div style={{ fontSize:10, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em" }}>{s.label}</div>
              </div>
            ))}
          </div>

          {/* Performance */}
          <div style={{ padding:"20px 28px", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12 }}>
              <TrendingUp style={{ width:14, height:14, color:"#fbbf24" }} />
              <h3 style={{ fontSize:12, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", margin:0 }}>Performance</h3>
            </div>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
              {[{label:"Save Rate", pct:saveRate, color:"#34d399"}, {label:"Rejection Rate", pct:rejectRate, color:"#f87171"}].map(m => (
                <div key={m.label}>
                  <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:6 }}>
                    <span style={{ fontSize:12, color:"#9ca3af" }}>{m.label}</span>
                    <span style={{ fontSize:13, fontWeight:600, color:m.color }}>{m.pct}%</span>
                  </div>
                  <div style={{ height:6, background:"rgba(255,255,255,.05)", borderRadius:3, overflow:"hidden" }}>
                    <div style={{ width:`${m.pct}%`, height:"100%", background:m.color, borderRadius:3, transition:"width 0.3s" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Verification Pipeline */}
          <div style={{ padding:"20px 28px", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12 }}>
              <CheckCircle2 style={{ width:14, height:14, color:"#34d399" }} />
              <h3 style={{ fontSize:12, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", margin:0 }}>Verification Pipeline</h3>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              {steps.map((step, i) => (
                <div key={i} style={{ display:"flex", alignItems:"flex-start", gap:12 }}>
                  <div style={{ width:24, height:24, borderRadius:"50%", background:"rgba(52,211,153,.15)", border:"2px solid rgba(52,211,153,.3)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:11, fontWeight:700, color:"#34d399", flexShrink:0 }}>{i+1}</div>
                  <p style={{ fontSize:12, color:"#9ca3af", lineHeight:1.6, margin:0, paddingTop:2 }}>{step}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Rejection Criteria */}
          <div style={{ padding:"20px 28px", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12 }}>
              <XCircle style={{ width:14, height:14, color:"#f87171" }} />
              <h3 style={{ fontSize:12, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", margin:0 }}>Rejection Criteria</h3>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:8 }}>
              {reasons.map((reason, i) => (
                <div key={i} style={{ display:"flex", alignItems:"flex-start", gap:10, padding:"8px 12px", background:"rgba(248,113,113,.08)", border:"1px solid rgba(248,113,113,.2)", borderRadius:10 }}>
                  <AlertTriangle style={{ width:14, height:14, color:"#f87171", flexShrink:0, marginTop:2 }} />
                  <p style={{ fontSize:12, color:"#fca5a5", lineHeight:1.6, margin:0 }}>{reason}</p>
                </div>
              ))}
            </div>
          </div>

          {/* Config */}
          <div style={{ padding:"20px 28px" }}>
            <div style={{ display:"flex", alignItems:"center", gap:8, marginBottom:12 }}>
              <Database style={{ width:14, height:14, color:"#818cf8" }} />
              <h3 style={{ fontSize:12, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", margin:0 }}>Configuration</h3>
            </div>
            <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
              {[{label:"Workspace ID", val:wsId, color:"#818cf8"}, {label:"Campaign ID", val:camId, color:"#34d399"}].map(row => (
                <div key={row.label} style={{ display:"flex", justifyContent:"space-between", alignItems:"center", padding:"10px 12px", background:"rgba(255,255,255,.03)", borderRadius:10 }}>
                  <span style={{ fontSize:12, color:"#9ca3af" }}>{row.label}</span>
                  <code style={{ fontSize:11, fontFamily:"monospace", color:row.color, background:`${row.color}18`, padding:"4px 8px", borderRadius:6 }}>{row.val.slice(0,20)}{row.val.length>20?"...":""}</code>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
