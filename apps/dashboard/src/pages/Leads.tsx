import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Search, Phone, Mail, Globe, Star, RefreshCw, Download, MessageCircle,
  Filter, ChevronDown, TrendingUp, Users, CheckCircle2, XCircle,
  LayoutGrid, List, Kanban, Facebook, Instagram, Twitter, Linkedin,
  Music2, Youtube, Pin, Lock
} from "lucide-react";
import { api } from "../lib/api";
import LeadDetailModal from "../components/LeadDetailModal";
import type { FullLead } from "../components/LeadDetailModal";
import { useDemo } from "../hooks/useDemo";

// ── Types ─────────────────────────────────────────────────────────────────────
interface Lead {
  id: string; name: string; address: string; phone: string; email: string;
  website: string; rating: string; reviewCount: number; category: string;
  score: number; priority: string; crmStatus: string; crmNotes: string;
  source: string; emailSent: boolean; whatsappSent: boolean;
  referenceUrl?: string;   // Google Maps / source link
  socialMedia?: Record<string, string>;
  city?: string; state?: string; zipCode?: string; country?: string;
  additionalEmails?: string[];
  aiAnalysis?: unknown;
}

// ── Constants ─────────────────────────────────────────────────────────────────
const PRIORITY_COLOR: Record<string, string> = { HIGH: "#34d399", MEDIUM: "#fbbf24", LOW: "#94a3b8" };
const PRIORITY_BG:    Record<string, string> = { HIGH: "rgba(52,211,153,.1)", MEDIUM: "rgba(251,191,36,.1)", LOW: "rgba(148,163,184,.06)" };

const CRM_STAGES = [
  { key: "all",        label: "All Leads",  color: "#6b7280", bg: "rgba(107,114,128,.1)" },
  { key: "new",        label: "New",        color: "#9ca3af", bg: "rgba(156,163,175,.1)" },
  { key: "contacted",  label: "Contacted",  color: "#60a5fa", bg: "rgba(96,165,250,.1)"  },
  { key: "replied",    label: "Replied",    color: "#a78bfa", bg: "rgba(167,139,250,.1)" },
  { key: "interested", label: "Interested", color: "#fbbf24", bg: "rgba(251,191,36,.1)"  },
  { key: "pitched",    label: "Pitched",    color: "#f97316", bg: "rgba(249,115,22,.1)"  },
  { key: "won",        label: "Won ✓",      color: "#34d399", bg: "rgba(52,211,153,.1)"  },
  { key: "lost",       label: "Lost ✗",     color: "#f87171", bg: "rgba(248,113,113,.1)" },
];

const SOCIAL_META: Record<string, { icon: React.ReactNode; color: string }> = {
  facebook:  { icon: <Facebook  style={{ width: 11, height: 11 }} />, color: "#1877f2" },
  instagram: { icon: <Instagram style={{ width: 11, height: 11 }} />, color: "#e1306c" },
  twitter:   { icon: <Twitter   style={{ width: 11, height: 11 }} />, color: "#1da1f2" },
  linkedin:  { icon: <Linkedin  style={{ width: 11, height: 11 }} />, color: "#0a66c2" },
  youtube:   { icon: <Youtube   style={{ width: 11, height: 11 }} />, color: "#ff0000" },
  tiktok:    { icon: <Music2    style={{ width: 11, height: 11 }} />, color: "#ff0050" },
  pinterest: { icon: <Pin       style={{ width: 11, height: 11 }} />, color: "#e60023" },
};

function scoreBg(s: number) { return s >= 75 ? "#059669" : s >= 50 ? "#d97706" : "#475569"; }

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function LeadsPage() {
  const demo = useDemo();
  const [leads, setLeads]           = useState<Lead[]>([]);
  const [loading, setLoading]       = useState(true);
  const [search, setSearch]         = useState("");
  const [crmFilter, setCrmFilter]   = useState("all");
  const [priorityFilter, setPriority] = useState("ALL");
  const [categoryFilter, setCategory] = useState("ALL");
  const [viewMode, setViewMode]     = useState<"grid" | "list" | "kanban">("grid");
  const [openDd, setOpenDd]         = useState<"p" | "c" | null>(null);
  const [selectedLead, setSelectedLead] = useState<Lead | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const d = await api.get<any>("/leads?limit=200");
      const arr = d.data ?? d.leads ?? d;
      setLeads(Array.isArray(arr) ? arr : []);
    } catch { setLeads([]); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  // Derived data
  const categories  = ["ALL", ...Array.from(new Set(leads.map(l => l.category || "other").filter(Boolean)))];
  const priorities  = ["ALL", "HIGH", "MEDIUM", "LOW"];

  const filtered = leads.filter(l => {
    const q = search.toLowerCase();
    const matchQ = !q || l.name?.toLowerCase().includes(q) || l.phone?.includes(q) || l.email?.toLowerCase().includes(q) || l.address?.toLowerCase().includes(q);
    const matchCrm  = crmFilter === "all"  || (l.crmStatus || "new") === crmFilter;
    const matchPri  = priorityFilter === "ALL" || l.priority === priorityFilter;
    const matchCat  = categoryFilter === "ALL" || (l.category || "other") === categoryFilter;
    return matchQ && matchCrm && matchPri && matchCat;
  });

  // Stats
  const statsTotal  = leads.length;
  const statsEmails = leads.filter(l => l.email).length;
  const statsWon    = leads.filter(l => l.crmStatus === "won").length;
  const statsHigh   = leads.filter(l => l.priority === "HIGH").length;

  // Stage counts for kanban headers
  const stageCounts = CRM_STAGES.reduce<Record<string, number>>((acc, s) => {
    acc[s.key] = s.key === "all" ? leads.length : leads.filter(l => (l.crmStatus || "new") === s.key).length;
    return acc;
  }, {});

  function exportCSV() {
    const headers = [
      "Name","Phone","WhatsApp Link","Email","Additional Emails",
      "Website","Google Maps Link","Address","City","Country",
      "Category","Rating","Reviews","Score","Priority","CRM Status",
      "Facebook","Instagram","Twitter","LinkedIn","YouTube","TikTok","WhatsApp",
      "Source"
    ].join(",");
    const esc = (v: string) => `"${(v || "").replace(/"/g, '""')}"`;
    const rows = filtered.map(l => {
      const sm  = l.socialMedia || {};
      const wa  = l.phone ? `https://wa.me/${l.phone.replace(/\D/g, "")}` : "";
      return [
        esc(l.name),
        esc(l.phone || ""),
        esc(wa),
        esc(l.email || ""),
        esc((l.additionalEmails || []).join(" | ")),
        esc(l.website || ""),
        esc(l.referenceUrl || ""),
        esc(l.address || ""),
        esc(l.city || ""),
        esc(l.country || ""),
        esc(l.category || ""),
        esc(l.rating || ""),
        String(l.reviewCount || 0),
        String(l.score || 0),
        esc(l.priority || ""),
        esc(l.crmStatus || "new"),
        esc(sm.facebook  || ""),
        esc(sm.instagram || ""),
        esc(sm.twitter   || ""),
        esc(sm.linkedin  || ""),
        esc(sm.youtube   || ""),
        esc(sm.tiktok    || ""),
        esc(sm.whatsapp  || ""),
        esc(l.source || ""),
      ].join(",");
    });
    // Add BOM so Excel opens UTF-8 correctly
    const csv  = "\uFEFF" + [headers, ...rows].join("\n");
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement("a");
    a.href     = url;
    a.download = `leads_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  function handleLeadUpdated(updated: FullLead) {
    setLeads(prev => prev.map(l => l.id === updated.id
      ? { ...l, crmStatus: updated.crmStatus ?? l.crmStatus, crmNotes: updated.crmNotes ?? l.crmNotes }
      : l
    ));
    // Re-open with fresh full data
    setSelectedLead(updated as unknown as Lead);
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%", background: "#05050f", overflow: "hidden", paddingTop: demo.demo_mode ? 52 : 0 }}
      onClick={() => setOpenDd(null)}>

      {/* ── Stats Bar ── */}
      <div style={{ display: "flex", gap: 1, borderBottom: "1px solid rgba(255,255,255,.06)", flexShrink: 0 }}>
        {[
          { label: "Total Leads", value: statsTotal,  color: "#818cf8", icon: <Users style={{ width: 14, height: 14 }} /> },
          { label: "With Emails", value: statsEmails, color: "#c084fc", icon: <Mail  style={{ width: 14, height: 14 }} /> },
          { label: "High Priority",value: statsHigh,  color: "#fbbf24", icon: <TrendingUp style={{ width: 14, height: 14 }} /> },
          { label: "Won",          value: statsWon,   color: "#34d399", icon: <CheckCircle2 style={{ width: 14, height: 14 }} /> },
        ].map(stat => (
          <div key={stat.label} style={{ flex: 1, padding: "14px 20px", borderRight: "1px solid rgba(255,255,255,.05)", display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{ color: stat.color }}>{stat.icon}</div>
            <div>
              <div style={{ fontSize: 20, fontWeight: 700, color: stat.color, lineHeight: 1 }}>{stat.value.toLocaleString()}</div>
              <div style={{ fontSize: 10, color: "#4b5563", marginTop: 3, textTransform: "uppercase", letterSpacing: "0.08em" }}>{stat.label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* ── Toolbar ── */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "12px 24px", borderBottom: "1px solid rgba(255,255,255,.06)", flexShrink: 0, gap: 10, flexWrap: "wrap" }}
        onClick={e => e.stopPropagation()}>
        <div style={{ display: "flex", alignItems: "center", gap: 8, flex: 1, flexWrap: "wrap" }}>
          {/* Search */}
          <div style={{ position: "relative" }}>
            <Search style={{ position: "absolute", left: 10, top: "50%", transform: "translateY(-50%)", width: 13, height: 13, color: "#6b7280" }} />
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Search name, email, phone…"
              style={{ paddingLeft: 30, paddingRight: 12, height: 34, width: 220, background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, fontSize: 12, color: "#fff", outline: "none" }} />
          </div>

          {/* Priority dropdown */}
          <div style={{ position: "relative" }}>
            <button onClick={() => setOpenDd(p => p === "p" ? null : "p")}
              style={{ display: "flex", alignItems: "center", gap: 6, height: 34, padding: "0 10px", background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, fontSize: 12, color: "#e5e7eb", cursor: "pointer", minWidth: 100 }}>
              <Filter style={{ width: 11, height: 11 }} />{priorityFilter} <ChevronDown style={{ width: 11, height: 11, marginLeft: "auto" }} />
            </button>
            {openDd === "p" && (
              <div style={{ position: "absolute", top: 38, left: 0, zIndex: 100, background: "#0d0d1f", border: "1px solid rgba(255,255,255,.1)", borderRadius: 10, width: 120, overflow: "hidden" }}>
                {priorities.map(p => (
                  <button key={p} onClick={() => { setPriority(p); setOpenDd(null); }}
                    style={{ display: "block", width: "100%", textAlign: "left", padding: "8px 12px", fontSize: 12, color: p === priorityFilter ? "#fff" : "#d1d5db", background: p === priorityFilter ? "rgba(79,70,229,.3)" : "transparent", border: "none", cursor: "pointer" }}>
                    {p}
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Category dropdown */}
          <div style={{ position: "relative" }}>
            <button onClick={() => setOpenDd(p => p === "c" ? null : "c")}
              style={{ display: "flex", alignItems: "center", gap: 6, height: 34, padding: "0 10px", background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, fontSize: 12, color: "#e5e7eb", cursor: "pointer", minWidth: 120 }}>
              🏢 {categoryFilter === "ALL" ? "Category" : categoryFilter} <ChevronDown style={{ width: 11, height: 11, marginLeft: "auto" }} />
            </button>
            {openDd === "c" && (
              <div style={{ position: "absolute", top: 38, left: 0, zIndex: 100, background: "#0d0d1f", border: "1px solid rgba(255,255,255,.1)", borderRadius: 10, maxHeight: 200, overflowY: "auto", width: 160 }}>
                {categories.map(c => (
                  <button key={c} onClick={() => { setCategory(c); setOpenDd(null); }}
                    style={{ display: "block", width: "100%", textAlign: "left", padding: "8px 12px", fontSize: 12, color: c === categoryFilter ? "#fff" : "#d1d5db", background: c === categoryFilter ? "rgba(79,70,229,.3)" : "transparent", border: "none", cursor: "pointer" }}>
                    {c}
                  </button>
                ))}
              </div>
            )}
          </div>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          {/* View mode */}
          <div style={{ display: "flex", background: "rgba(255,255,255,.04)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, overflow: "hidden" }}>
            {([["grid", <LayoutGrid style={{ width: 13, height: 13 }} />], ["list", <List style={{ width: 13, height: 13 }} />], ["kanban", <Kanban style={{ width: 13, height: 13 }} />]] as const).map(([mode, icon]) => (
              <button key={mode} onClick={() => setViewMode(mode as any)}
                style={{ width: 32, height: 34, border: "none", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center", background: viewMode === mode ? "rgba(79,70,229,.5)" : "transparent", color: viewMode === mode ? "#fff" : "#6b7280" }}>
                {icon}
              </button>
            ))}
          </div>

          <button onClick={load} style={{ width: 34, height: 34, background: "rgba(255,255,255,.05)", border: "1px solid rgba(255,255,255,.1)", borderRadius: 8, color: "#6b7280", display: "flex", alignItems: "center", justifyContent: "center", cursor: "pointer" }}>
            <RefreshCw style={{ width: 13, height: 13 }} />
          </button>

          <button onClick={exportCSV}
            style={{ display: "flex", alignItems: "center", gap: 6, height: 34, padding: "0 12px", background: "#4f46e5", border: "none", borderRadius: 8, fontSize: 12, color: "#fff", fontWeight: 600, cursor: "pointer" }}>
            <Download style={{ width: 12, height: 12 }} />Export CSV
          </button>
        </div>
      </div>

      {/* ── CRM Stage Tabs ── */}
      <div style={{ display: "flex", gap: 0, borderBottom: "1px solid rgba(255,255,255,.06)", overflowX: "auto", flexShrink: 0, background: "rgba(0,0,0,.2)" }}>
        {CRM_STAGES.map(stage => (
          <button key={stage.key} onClick={() => setCrmFilter(stage.key)}
            style={{
              flexShrink: 0, padding: "10px 16px", border: "none", cursor: "pointer", fontSize: 12, fontWeight: 600,
              background: crmFilter === stage.key ? stage.bg : "transparent",
              color: crmFilter === stage.key ? stage.color : "#4b5563",
              borderBottom: crmFilter === stage.key ? `2px solid ${stage.color}` : "2px solid transparent",
              transition: "all .15s",
            }}>
            {stage.label}
            <span style={{ marginLeft: 6, fontSize: 10, opacity: .7, background: "rgba(255,255,255,.06)", padding: "1px 5px", borderRadius: 8 }}>
              {stageCounts[stage.key] || 0}
            </span>
          </button>
        ))}
      </div>

      {/* ── Content ── */}
      <div style={{ flex: 1, overflowY: "auto", padding: "20px 24px" }}>
        {loading ? (
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: 160, color: "#4b5563" }}>
            <div style={{ width: 20, height: 20, borderRadius: "50%", border: "2px solid #6366f1", borderTopColor: "transparent", animation: "spin .8s linear infinite", marginRight: 10 }} />
            Loading leads…<style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
          </div>
        ) : filtered.length === 0 ? (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", height: 160, gap: 10, color: "#4b5563" }}>
            <span style={{ fontSize: 40 }}>📋</span>
            <p style={{ fontSize: 13 }}>No leads match — try changing filters or start the agents</p>
          </div>
        ) : viewMode === "kanban" ? (
          <KanbanView leads={filtered} onOpen={setSelectedLead} />
        ) : viewMode === "list" ? (
          <ListView leads={filtered} onOpen={setSelectedLead} />
        ) : (
          <GridView leads={filtered} onOpen={setSelectedLead} categories={categories} crmFilter={crmFilter} demoMode={demo.demo_mode} buyLink={demo.buy_link} />
        )}
      </div>

      <LeadDetailModal lead={selectedLead as unknown as FullLead} onClose={() => setSelectedLead(null)} onUpdated={handleLeadUpdated} />

      {/* Demo upgrade floating notification */}
      {demo.demo_mode && (
        <div style={{
          position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
          zIndex: 800, display: "flex", alignItems: "center", gap: 12,
          padding: "14px 22px", borderRadius: 16,
          background: "linear-gradient(135deg, #7c3aed, #4f46e5)",
          boxShadow: "0 8px 32px rgba(124,58,237,.6)",
          maxWidth: 500, width: "calc(100% - 48px)",
        }}>
          <span style={{ fontSize: 22, flexShrink: 0 }}>🔒</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 13, fontWeight: 700, color: "#fff", margin: 0 }}>Contact details are hidden in Demo Mode</p>
            <p style={{ fontSize: 11, color: "rgba(255,255,255,.7)", margin: "2px 0 0" }}>Buy the full system to unlock phone, email &amp; social media for every lead</p>
          </div>
          <a href={demo.buy_link || "#"} target="_blank" rel="noreferrer"
            style={{ flexShrink: 0, padding: "8px 16px", borderRadius: 10, background: "#fbbf24", color: "#1a1a1a", fontWeight: 800, fontSize: 12, textDecoration: "none", whiteSpace: "nowrap" }}>
            Buy Now
          </a>
        </div>
      )}
    </div>
  );
}

// ── Grid View ─────────────────────────────────────────────────────────────────
function GridView({ leads, onOpen, categories, crmFilter, demoMode, buyLink }: { leads: Lead[]; onOpen: (l: Lead) => void; categories: string[]; crmFilter: string; demoMode?: boolean; buyLink?: string }) {
  const grouped: Record<string, Lead[]> = {};
  leads.forEach(l => {
    const c = l.category || "other";
    if (!grouped[c]) grouped[c] = [];
    grouped[c].push(l);
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
      {Object.entries(grouped).sort((a, b) => b[1].length - a[1].length).map(([cat, catLeads]) => (
        <div key={cat}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 12 }}>
            <h2 style={{ fontSize: 13, fontWeight: 700, color: "#fff", textTransform: "capitalize", margin: 0 }}>{cat}</h2>
            <span style={{ fontSize: 10, color: "#6b7280", background: "rgba(255,255,255,.05)", padding: "2px 8px", borderRadius: 20 }}>{catLeads.length}</span>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill,minmax(290px,1fr))", gap: 12 }}>
            {catLeads.map(l => <LeadCard key={l.id} lead={l} onClick={() => onOpen(l)} demoMode={demoMode} buyLink={buyLink} />)}
          </div>
        </div>
      ))}
    </div>
  );
}

// ── List View ─────────────────────────────────────────────────────────────────
function ListView({ leads, onOpen }: { leads: Lead[]; onOpen: (l: Lead) => void }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {/* Header */}
      <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1.5fr 1fr 100px 80px", gap: 12, padding: "8px 14px", fontSize: 10, fontWeight: 700, color: "#4b5563", textTransform: "uppercase", letterSpacing: "0.08em" }}>
        <span>Business</span><span>Phone</span><span>Email</span><span>Social</span><span>Score</span><span>Status</span>
      </div>
      {leads.map(l => {
        const sm = l.socialMedia || {};
        const smKeys = Object.keys(sm).filter(k => SOCIAL_META[k]);
        const stage  = CRM_STAGES.find(s => s.key === (l.crmStatus || "new"));
        return (
          <motion.div key={l.id} initial={{ opacity: 0 }} animate={{ opacity: 1 }}
            onClick={() => onOpen(l)}
            style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1.5fr 1fr 100px 80px", gap: 12, padding: "12px 14px", background: "rgba(255,255,255,.03)", border: "1px solid rgba(255,255,255,.06)", borderRadius: 10, cursor: "pointer", alignItems: "center" }}
            onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,.06)")}
            onMouseLeave={e => (e.currentTarget.style.background = "rgba(255,255,255,.03)")}>
            <div>
              <p style={{ fontSize: 13, fontWeight: 600, color: "#fff", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{l.name}</p>
              {l.address && <p style={{ fontSize: 11, color: "#6b7280", margin: "2px 0 0", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{l.address}</p>}
            </div>
            <span style={{ fontSize: 12, color: "#9ca3af", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{l.phone || "—"}</span>
            <span style={{ fontSize: 12, color: l.email ? "#c084fc" : "#4b5563", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{l.email || "—"}</span>
            <div style={{ display: "flex", gap: 4 }}>
              {smKeys.slice(0, 4).map(k => (
                <a key={k} href={sm[k]} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                  style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 22, height: 22, borderRadius: 6, background: `${SOCIAL_META[k].color}20`, color: SOCIAL_META[k].color, textDecoration: "none" }}>
                  {SOCIAL_META[k].icon}
                </a>
              ))}
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              {l.score > 0 && <span style={{ padding: "2px 7px", borderRadius: 6, fontSize: 10, fontWeight: 700, color: "#fff", background: scoreBg(l.score) }}>{l.score}</span>}
              {l.priority && <span style={{ fontSize: 10, color: PRIORITY_COLOR[l.priority] || "#6b7280" }}>{l.priority}</span>}
            </div>
            <span style={{ fontSize: 10, fontWeight: 600, color: stage?.color || "#6b7280", background: stage?.bg || "rgba(255,255,255,.04)", padding: "3px 8px", borderRadius: 8, whiteSpace: "nowrap" }}>
              {stage?.label || l.crmStatus || "New"}
            </span>
          </motion.div>
        );
      })}
    </div>
  );
}

// ── Kanban View ───────────────────────────────────────────────────────────────
function KanbanView({ leads, onOpen }: { leads: Lead[]; onOpen: (l: Lead) => void }) {
  const stages = CRM_STAGES.filter(s => s.key !== "all");
  const byStage = stages.reduce<Record<string, Lead[]>>((acc, s) => {
    acc[s.key] = leads.filter(l => (l.crmStatus || "new") === s.key);
    return acc;
  }, {});

  return (
    <div style={{ display: "flex", gap: 14, overflowX: "auto", paddingBottom: 12, minHeight: 400, alignItems: "flex-start" }}>
      {stages.map(stage => (
        <div key={stage.key} style={{ flexShrink: 0, width: 240, display: "flex", flexDirection: "column", gap: 8 }}>
          {/* Column header */}
          <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "10px 12px", background: stage.bg, border: `1px solid ${stage.color}33`, borderRadius: 10 }}>
            <span style={{ fontSize: 12, fontWeight: 700, color: stage.color }}>{stage.label}</span>
            <span style={{ fontSize: 11, color: stage.color, background: `${stage.color}20`, padding: "1px 7px", borderRadius: 8, fontWeight: 600 }}>{byStage[stage.key]?.length || 0}</span>
          </div>
          {/* Cards */}
          {(byStage[stage.key] || []).map(lead => (
            <motion.div key={lead.id} initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }}
              onClick={() => onOpen(lead)}
              style={{ padding: "12px", background: "rgba(255,255,255,.04)", border: "1px solid rgba(255,255,255,.08)", borderRadius: 10, cursor: "pointer" }}
              onMouseEnter={e => (e.currentTarget.style.background = "rgba(255,255,255,.08)")}
              onMouseLeave={e => (e.currentTarget.style.background = "rgba(255,255,255,.04)")}>
              <p style={{ fontSize: 12, fontWeight: 600, color: "#fff", margin: "0 0 6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{lead.name}</p>
              {lead.phone && <p style={{ fontSize: 11, color: "#34d399", margin: "0 0 3px", display: "flex", alignItems: "center", gap: 4 }}><Phone style={{ width: 10, height: 10 }} />{lead.phone}</p>}
              {lead.email && <p style={{ fontSize: 11, color: "#c084fc", margin: "0 0 6px", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", display: "flex", alignItems: "center", gap: 4 }}><Mail style={{ width: 10, height: 10 }} />{lead.email}</p>}
              <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                {lead.score > 0 && <span style={{ fontSize: 10, fontWeight: 700, padding: "1px 6px", borderRadius: 5, background: scoreBg(lead.score), color: "#fff" }}>{lead.score}</span>}
                <div style={{ display: "flex", gap: 3 }}>
                  {Object.entries(lead.socialMedia || {}).filter(([k]) => SOCIAL_META[k]).slice(0, 3).map(([k, url]) => (
                    <a key={k} href={url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
                      style={{ display: "flex", alignItems: "center", justifyContent: "center", width: 18, height: 18, borderRadius: 4, background: `${SOCIAL_META[k].color}20`, color: SOCIAL_META[k].color, textDecoration: "none" }}>
                      {SOCIAL_META[k].icon}
                    </a>
                  ))}
                </div>
              </div>
            </motion.div>
          ))}
          {(byStage[stage.key] || []).length === 0 && (
            <div style={{ padding: "20px 0", textAlign: "center", color: "#374151", fontSize: 12, border: "1px dashed rgba(255,255,255,.06)", borderRadius: 10 }}>Empty</div>
          )}
        </div>
      ))}
    </div>
  );
}

// ── Lead Card (Grid) ──────────────────────────────────────────────────────────
function LeadCard({ lead, onClick, demoMode, buyLink }: { lead: Lead; onClick: () => void; demoMode?: boolean; buyLink?: string }) {
  const digits = (lead.phone || "").replace(/\D/g, "");
  const sm     = lead.socialMedia || {};
  const smKeys = Object.keys(sm).filter(k => SOCIAL_META[k]);
  const stage  = CRM_STAGES.find(s => s.key === (lead.crmStatus || "new"));

  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }}
      onClick={onClick}
      style={{ background: "rgba(255,255,255,.03)", border: "1px solid rgba(255,255,255,.07)", borderRadius: 14, padding: "14px 16px", cursor: "pointer", display: "flex", flexDirection: "column", gap: 10 }}
      onMouseEnter={e => { e.currentTarget.style.background = "rgba(255,255,255,.06)"; e.currentTarget.style.borderColor = "rgba(255,255,255,.12)"; }}
      onMouseLeave={e => { e.currentTarget.style.background = "rgba(255,255,255,.03)"; e.currentTarget.style.borderColor = "rgba(255,255,255,.07)"; }}>

      {/* Name + badges */}
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 8 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <p style={{ fontSize: 13, fontWeight: 600, color: "#fff", margin: 0, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{lead.name}</p>
          {lead.address && <p style={{ fontSize: 11, color: "#6b7280", margin: "2px 0 0", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{lead.address}</p>}
        </div>
        <div style={{ display: "flex", gap: 5, flexShrink: 0, flexWrap: "wrap", justifyContent: "flex-end" }}>
          {lead.score > 0 && <span style={{ padding: "2px 7px", borderRadius: 6, fontSize: 10, fontWeight: 700, color: "#fff", background: scoreBg(lead.score) }}>{lead.score}</span>}
          {lead.priority && <span style={{ padding: "2px 7px", borderRadius: 10, fontSize: 10, fontWeight: 500, color: PRIORITY_COLOR[lead.priority] || "#94a3b8", background: PRIORITY_BG[lead.priority] || "rgba(148,163,184,.06)", border: `1px solid ${PRIORITY_COLOR[lead.priority] || "#94a3b8"}33` }}>{lead.priority}</span>}
        </div>
      </div>

      {/* Contact info */}
      <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
        {lead.phone && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Phone style={{ width: 11, height: 11, color: "#34d399", flexShrink: 0 }} />
            {demoMode ? (
              <span style={{filter:"blur(4px)",userSelect:"none",fontSize:12,color:"#34d399",cursor:"not-allowed"}}>{lead.phone}</span>
            ) : (
              <a href={`tel:${lead.phone}`} onClick={e => e.stopPropagation()} style={{ fontSize: 12, color: "#34d399", textDecoration: "none" }}>{lead.phone}</a>
            )}
          </div>
        )}
        {lead.email && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Mail style={{ width: 11, height: 11, color: "#c084fc", flexShrink: 0 }} />
            {demoMode ? (
              <span style={{filter:"blur(4px)",userSelect:"none",fontSize:12,color:"#c084fc",cursor:"not-allowed"}}>{lead.email}</span>
            ) : (
              <a href={`mailto:${lead.email}`} onClick={e => e.stopPropagation()} style={{ fontSize: 12, color: "#c084fc", textDecoration: "none" }}>{lead.email}</a>
            )}
          </div>
        )}
        {lead.website && (
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <Globe style={{ width: 11, height: 11, color: "#818cf8", flexShrink: 0 }} />
            <a href={lead.website} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} style={{ fontSize: 12, color: "#818cf8", textDecoration: "none", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{lead.website.replace(/^https?:\/\/(www\.)?/, "")}</a>
          </div>
        )}
        {lead.rating && lead.rating !== "N/A" && (
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <Star style={{ width: 11, height: 11, fill: "#fbbf24", color: "#fbbf24" }} />
            <span style={{ fontSize: 12, color: "#fbbf24" }}>{lead.rating}</span>
            {lead.reviewCount > 0 && <span style={{ fontSize: 11, color: "#4b5563" }}>({lead.reviewCount.toLocaleString()})</span>}
          </div>
        )}
      </div>

      {/* Social media icons */}
      {smKeys.length > 0 && (
        <div style={{ display: "flex", gap: 5, flexWrap: "wrap" }}>
          {smKeys.map(k => (
            <a key={k} href={sm[k]} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
              style={{ display: "inline-flex", alignItems: "center", gap: 4, padding: "3px 7px", borderRadius: 6, background: `${SOCIAL_META[k].color}18`, border: `1px solid ${SOCIAL_META[k].color}33`, color: SOCIAL_META[k].color, fontSize: 10, textDecoration: "none", fontWeight: 600 }}>
              {SOCIAL_META[k].icon}
            </a>
          ))}
        </div>
      )}

      {/* Footer: CRM status + quick actions */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", paddingTop: 6, borderTop: "1px solid rgba(255,255,255,.05)" }}>
        <span style={{ fontSize: 10, fontWeight: 600, color: stage?.color || "#6b7280", background: stage?.bg || "rgba(255,255,255,.04)", padding: "2px 8px", borderRadius: 8 }}>
          {stage?.label || lead.crmStatus || "New"}
        </span>
        <div style={{ display: "flex", gap: 5, alignItems: "center" }}>
          {lead.emailSent    && <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 8, background: "rgba(96,165,250,.1)",  color: "#60a5fa", border: "1px solid rgba(96,165,250,.2)"  }}>✉</span>}
          {lead.whatsappSent && <span style={{ fontSize: 10, padding: "2px 6px", borderRadius: 8, background: "rgba(52,211,153,.1)",  color: "#34d399", border: "1px solid rgba(52,211,153,.2)"  }}>💬</span>}
          {/* WhatsApp verified badge */}
          {sm.whatsapp && <span title="WhatsApp Verified" style={{ fontSize: 9, padding: "1px 6px", borderRadius: 8, background: "rgba(37,211,102,.2)", color: "#25d366", border: "1px solid rgba(37,211,102,.35)", fontWeight:700 }}>✓WA</span>}
          {digits && (
            <a href={`https://wa.me/${digits}`} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
              style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 11, color: "#25d366", padding: "2px 7px", borderRadius: 8, background: "rgba(37,211,102,.08)", border: "1px solid rgba(37,211,102,.2)", textDecoration: "none" }}>
              <MessageCircle style={{ width: 10, height: 10 }} />WA
            </a>
          )}
          {/* Google Maps link */}
          {lead.referenceUrl && (
            <a href={lead.referenceUrl} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()}
              title="View on Google Maps"
              style={{ fontSize: 12, padding: "1px 5px", borderRadius: 6, background: "rgba(66,133,244,.12)", border: "1px solid rgba(66,133,244,.25)", textDecoration: "none" }}>
              🗺️
            </a>
          )}
        </div>
      </div>
    </motion.div>
  );
}
