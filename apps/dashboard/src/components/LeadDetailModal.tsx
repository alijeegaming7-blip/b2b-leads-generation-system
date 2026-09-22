import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X, MapPin, Phone, Mail, Globe, Star, MessageCircle, ExternalLink,
  AlertTriangle, ChevronRight, Copy, Check, Loader2, Send, FileText,
  StickyNote, TrendingUp, Zap, Facebook, Instagram, Twitter,
  Linkedin, Youtube, Music2, Pin,
} from "lucide-react";
import { api } from "../lib/api";
import DemoBlur, { DemoUpgradeBox } from "./DemoBlur";
import { useDemo } from "../hooks/useDemo";

// ── Shared types ──────────────────────────────────────────────────────────────
export interface Activity {
  id: string;
  type: string;
  note: string;
  createdAt: string;
}

export interface FullLead {
  id: string;
  name: string;
  address: string;
  phone: string;
  email: string;
  website: string;
  rating: string;
  reviewCount: number;
  score: number;
  priority: string;
  category: string;
  source: string;
  referenceUrl?: string;   // ← Google Maps / source page link
  pipelineStage?: string;
  crmStatus?: string;
  crmNotes?: string;
  followUpDate?: string;
  aiAnalysis?: unknown;
  salesBrief?: unknown;
  city?: string;
  state?: string;
  zipCode?: string;
  country?: string;
  socialMedia?: Record<string, string>;
  additionalEmails?: string[];
  activities?: Activity[];
  emailSent?: boolean;
  whatsappSent?: boolean;
}

interface Props {
  lead: FullLead | null;
  onClose: () => void;
  onUpdated?: (l: FullLead) => void;
}

// ── Constants ─────────────────────────────────────────────────────────────────
const CRM_STAGES = [
  { key: "new",        label: "New",        color: "#6b7280" },
  { key: "contacted",  label: "Contacted",  color: "#60a5fa" },
  { key: "replied",    label: "Replied",    color: "#a78bfa" },
  { key: "interested", label: "Interested", color: "#fbbf24" },
  { key: "pitched",    label: "Pitched",    color: "#f97316" },
  { key: "won",        label: "Won ✓",      color: "#34d399" },
  { key: "lost",       label: "Lost ✗",     color: "#f87171" },
];

const SOCIAL_ICONS: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  facebook:  { icon: <Facebook  style={{ width:14,height:14 }} />, color:"#1877f2", label:"Facebook"  },
  instagram: { icon: <Instagram style={{ width:14,height:14 }} />, color:"#e1306c", label:"Instagram" },
  twitter:   { icon: <Twitter   style={{ width:14,height:14 }} />, color:"#1da1f2", label:"Twitter/X" },
  linkedin:  { icon: <Linkedin  style={{ width:14,height:14 }} />, color:"#0a66c2", label:"LinkedIn"  },
  youtube:   { icon: <Youtube   style={{ width:14,height:14 }} />, color:"#ff0000", label:"YouTube"   },
  tiktok:    { icon: <Music2    style={{ width:14,height:14 }} />, color:"#ff0050", label:"TikTok"    },
  pinterest: { icon: <Pin       style={{ width:14,height:14 }} />, color:"#e60023", label:"Pinterest" },
};

const PITCH_SERVICES = [
  { key:"website",   label:"Website Dev",  emoji:"💻" },
  { key:"seo",       label:"SEO Audit",    emoji:"🎯" },
  { key:"inventory", label:"Inventory",    emoji:"📦" },
  { key:"analytics", label:"Analytics",    emoji:"📊" },
  { key:"ai",        label:"AI Assistant", emoji:"🤖" },
];

const PITCH_TONES = [
  { key:"professional", label:"Professional" },
  { key:"friendly",     label:"Friendly 😊"  },
  { key:"urgent",       label:"Urgent ⚡"    },
];

const NOTE_TYPES = [
  { key:"note",     label:"Note",     emoji:"📝" },
  { key:"call",     label:"Call",     emoji:"📞" },
  { key:"meeting",  label:"Meeting",  emoji:"🤝" },
  { key:"email",    label:"Email",    emoji:"✉️"  },
  { key:"whatsapp", label:"WhatsApp", emoji:"💬" },
];

// ── Helpers ───────────────────────────────────────────────────────────────────
function scoreColor(s: number) { return s>=75?"#34d399":s>=50?"#fbbf24":"#6b7280"; }
function priorityColor(p?: string) { return p==="HIGH"?"#34d399":p==="MEDIUM"?"#fbbf24":"#6b7280"; }

function CopyBtn({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button onClick={() => { navigator.clipboard.writeText(text); setCopied(true); setTimeout(()=>setCopied(false),1500); }}
      style={{ background:"none", border:"none", cursor:"pointer", color:copied?"#34d399":"#4b5563", padding:"2px 4px", borderRadius:4 }}>
      {copied ? <Check style={{width:12,height:12}}/> : <Copy style={{width:12,height:12}}/>}
    </button>
  );
}

// ── Main Modal ────────────────────────────────────────────────────────────────
export default function LeadDetailModal({ lead, onClose, onUpdated }: Props) {
  const demo = useDemo();
  const [tab,           setTab]           = useState<"overview"|"pitch"|"notes"|"crm">("overview");
  const [crmStatus,     setCrmStatus]     = useState("new");
  const [crmNotes,      setCrmNotes]      = useState("");
  const [savingCrm,     setSavingCrm]     = useState(false);
  const [pitchService,  setPitchService]  = useState("website");
  const [pitchTone,     setPitchTone]     = useState("professional");
  const [pitch,         setPitch]         = useState("");
  const [generatingPitch, setGeneratingPitch] = useState(false);
  const [pitchCopied,   setPitchCopied]   = useState(false);
  const [noteText,      setNoteText]      = useState("");
  const [noteType,      setNoteType]      = useState("note");
  const [savingNote,    setSavingNote]    = useState(false);
  const [activities,    setActivities]    = useState<Activity[]>([]);
  const [fullLead,      setFullLead]      = useState<FullLead | null>(null);

  useEffect(() => {
    if (!lead) return;
    setCrmStatus(lead.crmStatus ?? "new");
    setCrmNotes(lead.crmNotes  ?? "");
    setTab("overview");
    setPitch("");
    setFullLead(lead);
    setActivities(lead.activities ?? []);

    api.get<FullLead>(`/leads/${lead.id}`)
      .then(full => {
        setFullLead(full);
        setCrmStatus(full.crmStatus ?? "new");
        setCrmNotes(full.crmNotes   ?? "");
        setActivities(full.activities ?? []);
        const ai = (typeof full.aiAnalysis === "object" && full.aiAnalysis !== null)
          ? full.aiAnalysis as Record<string,unknown> : {};
        const agentId = String(ai?.agent_id ?? "");
        if (agentId.includes("seo"))       setPitchService("seo");
        else if (agentId.includes("inv"))  setPitchService("inventory");
        else if (agentId.includes("ana"))  setPitchService("analytics");
        else if (agentId.includes("ai"))   setPitchService("ai");
        else                               setPitchService("website");
      })
      .catch(() => {});
  }, [lead?.id]); // eslint-disable-line

  if (!lead) return null;
  const data = fullLead ?? lead;

  const issues: string[] = (() => {
    try {
      const p = (typeof data.aiAnalysis === "object" && data.aiAnalysis !== null)
        ? data.aiAnalysis as Record<string,unknown>
        : JSON.parse(String(data.aiAnalysis ?? "{}"));
      return (p?.issues_found as string[]) ?? [];
    } catch { return []; }
  })();

  const socialMedia = data.socialMedia ?? {};
  const hasSocial   = Object.keys(socialMedia).length > 0;
  const fullAddress = [data.address, data.city, data.state, data.zipCode, data.country].filter(Boolean).join(", ");
  const waNumber    = (data.phone ?? "").replace(/[^0-9+]/g, "");

  async function saveCrm() {
    setSavingCrm(true);
    try {
      const updated = await api.patch<FullLead>(`/leads/${data.id}/crm`, { crmStatus: crmStatus, crmNotes: crmNotes });
      setFullLead(updated);
      onUpdated?.(updated);
    } catch {/* ignore */} finally { setSavingCrm(false); }
  }

  async function generatePitch() {
    setGeneratingPitch(true); setPitch("");
    try {
      const res = await api.post<{ pitch: string }>(`/leads/${data.id}/pitch`, { tone: pitchTone, service: pitchService });
      setPitch(res.pitch);
    } catch { setPitch("Failed to generate pitch. Check connection and try again."); }
    finally   { setGeneratingPitch(false); }
  }

  async function saveNote() {
    if (!noteText.trim()) return;
    setSavingNote(true);
    try {
      const act = await api.post<Activity>(`/leads/${data.id}/notes`, { note: noteText, type: noteType });
      setActivities(prev => [act, ...prev]);
      setNoteText("");
    } catch {/* ignore */} finally { setSavingNote(false); }
  }

  const TabBtn = (key: typeof tab, label: string, emoji: string) => (
    <button key={key} onClick={() => setTab(key)} style={{
      flex:1, display:"flex", alignItems:"center", justifyContent:"center", gap:5,
      padding:"8px 4px", borderRadius:8, border:"none", cursor:"pointer", fontSize:12, fontWeight:600,
      background: tab===key ? "#4f46e5" : "transparent",
      color:       tab===key ? "#fff"    : "#6b7280",
      transition:"all .15s",
    }}><span>{emoji}</span>{label}</button>
  );

  return (
    <AnimatePresence>
      <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}
        style={{ position:"fixed", inset:0, zIndex:500, background:"rgba(0,0,0,.85)", backdropFilter:"blur(6px)", display:"flex", alignItems:"center", justifyContent:"center", padding:"16px" }}
        onClick={onClose}>
        <motion.div initial={{scale:0.96,opacity:0}} animate={{scale:1,opacity:1}} exit={{scale:0.96,opacity:0}}
          transition={{type:"spring",damping:26,stiffness:300}}
          style={{ background:"#0a0a1a", border:"1px solid rgba(255,255,255,.1)", borderRadius:24, width:"100%", maxWidth:720, maxHeight:"92vh", overflowY:"auto", display:"flex", flexDirection:"column" }}
          onClick={e=>e.stopPropagation()}>

          {/* Header */}
          <div style={{ padding:"22px 26px 16px", borderBottom:"1px solid rgba(255,255,255,.07)", flexShrink:0 }}>
            <div style={{ display:"flex", alignItems:"flex-start", gap:14 }}>
              <div style={{ width:52, height:52, borderRadius:16, background:"linear-gradient(135deg,#4f46e5,#7c3aed)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:26, flexShrink:0 }}>🏢</div>
              <div style={{ flex:1, minWidth:0 }}>
                <h2 style={{ fontSize:18, fontWeight:700, color:"#fff", margin:0, lineHeight:1.3 }}>{data.name}</h2>
                {fullAddress && <p style={{ fontSize:11, color:"#6b7280", margin:"4px 0 0", display:"flex", alignItems:"center", gap:4 }}><MapPin style={{width:11,height:11}}/>{fullAddress}</p>}
                <div style={{ display:"flex", gap:6, marginTop:7, flexWrap:"wrap" }}>
                  {data.score>0 && <span style={{ padding:"2px 8px", borderRadius:8, fontSize:10, fontWeight:700, color:"#fff", background:scoreColor(data.score) }}>Score {data.score}</span>}
                  {data.priority && <span style={{ padding:"2px 8px", borderRadius:8, fontSize:10, fontWeight:600, color:priorityColor(data.priority), background:`${priorityColor(data.priority)}20`, border:`1px solid ${priorityColor(data.priority)}44` }}>{data.priority}</span>}
                  <span style={{ padding:"2px 8px", borderRadius:8, fontSize:10, fontWeight:600, color:CRM_STAGES.find(s=>s.key===crmStatus)?.color??"#6b7280", background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)" }}>
                    {CRM_STAGES.find(s=>s.key===crmStatus)?.label ?? crmStatus}
                  </span>
                  {data.source && <span style={{ padding:"2px 8px", borderRadius:8, fontSize:10, color:"#4b5563", background:"rgba(255,255,255,.04)", border:"1px solid rgba(255,255,255,.07)" }}>via {data.source}</span>}
                </div>
              </div>
              <button onClick={onClose} style={{ width:34, height:34, borderRadius:10, background:"rgba(255,255,255,.06)", border:"1px solid rgba(255,255,255,.1)", color:"#9ca3af", cursor:"pointer", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
                <X style={{width:16,height:16}}/>
              </button>
            </div>
            {/* Quick action buttons */}
            <div style={{ display:"flex", gap:8, marginTop:14, flexWrap:"wrap" }}>
              {data.phone && !demo.demo_mode && <a href={`tel:${data.phone}`} style={{ display:"flex", alignItems:"center", gap:5, padding:"6px 12px", borderRadius:8, background:"rgba(52,211,153,.12)", border:"1px solid rgba(52,211,153,.25)", color:"#34d399", fontSize:12, fontWeight:600, textDecoration:"none" }}><Phone style={{width:13,height:13}}/>{data.phone}</a>}
              {data.phone && !demo.demo_mode && <a href={`https://wa.me/${(data.phone||"").replace(/\D/g,"")}`} target="_blank" rel="noreferrer" style={{ display:"flex", alignItems:"center", gap:5, padding:"6px 12px", borderRadius:8, background:"rgba(37,211,102,.12)", border:"1px solid rgba(37,211,102,.25)", color:"#25d366", fontSize:12, fontWeight:600, textDecoration:"none" }}>
                <MessageCircle style={{width:13,height:13}}/>WhatsApp
                {(data.socialMedia||{}).whatsapp && <span style={{fontSize:9,background:"rgba(37,211,102,.3)",padding:"1px 4px",borderRadius:4}}>✓</span>}
              </a>}
              {data.email && !demo.demo_mode && <a href={`mailto:${data.email}`} style={{ display:"flex", alignItems:"center", gap:5, padding:"6px 12px", borderRadius:8, background:"rgba(192,132,252,.12)", border:"1px solid rgba(192,132,252,.25)", color:"#c084fc", fontSize:12, fontWeight:600, textDecoration:"none" }}><Mail style={{width:13,height:13}}/>{data.email}</a>}
              {data.website && <a href={data.website} target="_blank" rel="noreferrer" style={{ display:"flex", alignItems:"center", gap:5, padding:"6px 12px", borderRadius:8, background:"rgba(129,140,248,.12)", border:"1px solid rgba(129,140,248,.25)", color:"#818cf8", fontSize:12, fontWeight:600, textDecoration:"none" }}><Globe style={{width:13,height:13}}/>Website <ExternalLink style={{width:10,height:10}}/></a>}
              {data.referenceUrl && <a href={data.referenceUrl} target="_blank" rel="noreferrer" style={{ display:"flex", alignItems:"center", gap:5, padding:"6px 12px", borderRadius:8, background:"rgba(66,133,244,.12)", border:"1px solid rgba(66,133,244,.25)", color:"#4285f4", fontSize:12, fontWeight:600, textDecoration:"none" }}>🗺️ Maps <ExternalLink style={{width:10,height:10}}/></a>}
              {/* Demo mode: show blurred phone/email placeholders + buy button */}
              {demo.demo_mode && (
                <a href={demo.buy_link||"#"} target="_blank" rel="noreferrer"
                  style={{ display:"flex", alignItems:"center", gap:6, padding:"6px 14px", borderRadius:8, background:"linear-gradient(135deg,#7c3aed,#4f46e5)", color:"#fff", fontSize:12, fontWeight:700, textDecoration:"none" }}>
                  🔒 Unlock Contact Details
                </a>
              )}
            </div>
          </div>

          {/* Tab bar */}
          <div style={{ display:"flex", gap:4, padding:"10px 26px", borderBottom:"1px solid rgba(255,255,255,.06)", background:"rgba(0,0,0,.2)", flexShrink:0 }}>
            {TabBtn("overview","Overview","📋")}
            {TabBtn("pitch",   "Pitch",   "🚀")}
            {TabBtn("notes",   "Notes",   "📝")}
            {TabBtn("crm",     "CRM",     "🎯")}
          </div>

          {/* Tab content */}
          <div style={{ flex:1, overflowY:"auto", padding:"20px 26px" }}>

            {/* ═══ OVERVIEW ═══ */}
            {tab==="overview" && (
              <div style={{ display:"flex", flexDirection:"column", gap:20 }}>
                {(data.rating || data.reviewCount) && (
                  <div style={{ display:"grid", gridTemplateColumns:"repeat(3,1fr)", gap:10 }}>
                    {data.rating && data.rating!=="N/A" && (
                      <Stat><div style={{ display:"flex", alignItems:"center", justifyContent:"center", gap:5, marginBottom:4 }}><Star style={{width:14,height:14,fill:"#fbbf24",color:"#fbbf24"}}/><span style={{fontSize:22,fontWeight:700,color:"#fbbf24"}}>{data.rating}</span></div><div style={{fontSize:10,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.1em"}}>Rating</div></Stat>
                    )}
                    {(data.reviewCount??0)>0 && <Stat><div style={{fontSize:22,fontWeight:700,color:"#60a5fa",marginBottom:4}}>{(data.reviewCount??0).toLocaleString()}</div><div style={{fontSize:10,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.1em"}}>Reviews</div></Stat>}
                    {data.score>0 && <Stat><div style={{fontSize:22,fontWeight:700,color:scoreColor(data.score),marginBottom:4}}>{data.score}</div><div style={{fontSize:10,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.1em"}}>Lead Score</div></Stat>}
                  </div>
                )}

                {hasSocial && (
                  <Section title="Social Media" icon="🌐">
                    <div style={{display:"flex",flexWrap:"wrap",gap:8}}>
                      {Object.entries(socialMedia).map(([platform,url]) => {
                        const info = SOCIAL_ICONS[platform] ?? { icon:<Globe style={{width:14,height:14}}/>, color:"#6b7280", label:platform };
                        return (
                          <a key={platform} href={url} target="_blank" rel="noreferrer"
                            style={{display:"inline-flex",alignItems:"center",gap:6,padding:"6px 12px",borderRadius:8,background:`${info.color}18`,border:`1px solid ${info.color}44`,color:info.color,fontSize:12,fontWeight:600,textDecoration:"none"}}>
                            {info.icon}{info.label}
                          </a>
                        );
                      })}
                    </div>
                  </Section>
                )}

                {(data.additionalEmails ?? []).length > 0 && (
                  <Section title="Additional Emails" icon="📧">
                    {(data.additionalEmails!).map((em,i) => (
                      <div key={i} style={{display:"flex",alignItems:"center",gap:8,marginBottom:4}}>
                        <a href={`mailto:${em}`} style={{fontSize:13,color:"#c084fc",textDecoration:"none"}}>{em}</a>
                        <CopyBtn text={em}/>
                      </div>
                    ))}
                  </Section>
                )}

                {issues.length>0 && (
                  <Section title="Opportunities Detected" icon="⚡">
                    {issues.map((issue,i) => (
                      <div key={i} style={{display:"flex",alignItems:"flex-start",gap:10,padding:"10px 12px",background:"rgba(245,158,11,.07)",border:"1px solid rgba(245,158,11,.2)",borderRadius:10,marginBottom:6}}>
                        <AlertTriangle style={{width:13,height:13,color:"#f59e0b",flexShrink:0,marginTop:2}}/>
                        <p style={{fontSize:12,color:"#fbbf24",lineHeight:1.6,margin:0}}>{issue}</p>
                      </div>
                    ))}
                  </Section>
                )}

                <Section title="Contact Details" icon="📞">
                  {/* In demo mode show upgrade box instead of contact details */}
                  {demo.demo_mode ? (
                    <DemoUpgradeBox buyLink={demo.buy_link} price={demo.demo_price} />
                  ) : (
                    <>
                      {/* Phone + WhatsApp verified */}
                      {data.phone && (
                        <ContactRow icon={<Phone style={{width:14,height:14,color:"#34d399"}}/>}>
                          <a href={`tel:${data.phone}`} style={{color:"#34d399",textDecoration:"none",fontSize:13,fontWeight:600}}>{data.phone}</a>
                          <CopyBtn text={data.phone}/>
                          <a href={`https://wa.me/${(data.phone||"").replace(/\D/g,"")}`} target="_blank" rel="noreferrer"
                            style={{display:"inline-flex",alignItems:"center",gap:4,padding:"3px 8px",borderRadius:6,background:"rgba(37,211,102,.15)",border:"1px solid rgba(37,211,102,.3)",color:"#25d366",fontSize:11,fontWeight:700,textDecoration:"none",marginLeft:4}}>
                            <MessageCircle style={{width:11,height:11}}/>WhatsApp
                          </a>
                          {(data.socialMedia || {}).whatsapp && (
                            <span style={{display:"inline-flex",alignItems:"center",gap:3,padding:"2px 7px",borderRadius:6,background:"rgba(37,211,102,.2)",border:"1px solid rgba(37,211,102,.4)",color:"#25d366",fontSize:10,fontWeight:700}}>
                              ✓ WA Verified
                            </span>
                          )}
                        </ContactRow>
                      )}
                      {data.email && (
                        <ContactRow icon={<Mail style={{width:14,height:14,color:"#c084fc"}}/>}>
                          <a href={`mailto:${data.email}`} style={{color:"#c084fc",textDecoration:"none",fontSize:13}}>{data.email}</a>
                          <CopyBtn text={data.email}/>
                        </ContactRow>
                      )}
                      {(data.additionalEmails || []).map((em, i) => (
                        <ContactRow key={i} icon={<Mail style={{width:14,height:14,color:"#a78bfa"}}/>}>
                          <a href={`mailto:${em}`} style={{color:"#a78bfa",textDecoration:"none",fontSize:12}}>{em}</a>
                          <CopyBtn text={em}/>
                          <span style={{fontSize:10,color:"#6b7280"}}>alt email</span>
                        </ContactRow>
                      ))}
                      {data.website && (
                        <ContactRow icon={<Globe style={{width:14,height:14,color:"#818cf8"}}/>}>
                          <a href={data.website} target="_blank" rel="noreferrer"
                            style={{color:"#818cf8",textDecoration:"none",fontSize:13}}>
                            {data.website.replace(/^https?:\/\/(www\.)?/,"")}
                          </a>
                          <ExternalLink style={{width:11,height:11,color:"#818cf8"}}/>
                          <CopyBtn text={data.website}/>
                        </ContactRow>
                      )}
                      {fullAddress && (
                        <ContactRow icon={<MapPin style={{width:14,height:14,color:"#60a5fa"}}/>}>
                          <span style={{color:"#d1d5db",fontSize:13}}>{fullAddress}</span>
                          <CopyBtn text={fullAddress}/>
                        </ContactRow>
                      )}
                      {data.referenceUrl && (
                        <ContactRow icon={<span style={{fontSize:14}}>🗺️</span>}>
                          <a href={data.referenceUrl} target="_blank" rel="noreferrer"
                            style={{color:"#4285f4",textDecoration:"none",fontSize:12,fontWeight:600}}>
                            View on Google Maps
                          </a>
                          <ExternalLink style={{width:11,height:11,color:"#4285f4"}}/>
                        </ContactRow>
                      )}
                    </>
                  )}
                </Section>
              </div>
            )}

            {/* ═══ PITCH ═══ */}
            {tab==="pitch" && (
              <div style={{display:"flex",flexDirection:"column",gap:16}}>
                <div style={{padding:14,background:"rgba(99,102,241,.1)",border:"1px solid rgba(99,102,241,.25)",borderRadius:12,fontSize:12,color:"#a5b4fc",lineHeight:1.6}}>
                  🚀 Generate a personalised cold outreach pitch for <strong style={{color:"#fff"}}>{data.name}</strong> based on their data and detected issues.
                </div>
                <div>
                  <Label>Service</Label>
                  <div style={{display:"flex",gap:6,flexWrap:"wrap",marginTop:8}}>
                    {PITCH_SERVICES.map(s=>(
                      <button key={s.key} onClick={()=>setPitchService(s.key)}
                        style={{display:"flex",alignItems:"center",gap:5,padding:"7px 12px",borderRadius:8,border:`1px solid ${pitchService===s.key?"#6366f1":"rgba(255,255,255,.1)"}`,background:pitchService===s.key?"rgba(99,102,241,.25)":"rgba(255,255,255,.04)",color:pitchService===s.key?"#a5b4fc":"#9ca3af",fontSize:12,fontWeight:600,cursor:"pointer"}}>
                        {s.emoji} {s.label}
                      </button>
                    ))}
                  </div>
                </div>
                <div>
                  <Label>Tone</Label>
                  <div style={{display:"flex",gap:6,marginTop:8}}>
                    {PITCH_TONES.map(t=>(
                      <button key={t.key} onClick={()=>setPitchTone(t.key)}
                        style={{flex:1,padding:"8px",borderRadius:8,border:`1px solid ${pitchTone===t.key?"#6366f1":"rgba(255,255,255,.1)"}`,background:pitchTone===t.key?"rgba(99,102,241,.25)":"rgba(255,255,255,.04)",color:pitchTone===t.key?"#a5b4fc":"#9ca3af",fontSize:12,fontWeight:600,cursor:"pointer"}}>
                        {t.label}
                      </button>
                    ))}
                  </div>
                </div>
                <button onClick={generatePitch} disabled={generatingPitch}
                  style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,padding:"12px",borderRadius:10,background:generatingPitch?"#374151":"linear-gradient(135deg,#4f46e5,#7c3aed)",border:"none",color:"#fff",fontSize:13,fontWeight:700,cursor:generatingPitch?"not-allowed":"pointer"}}>
                  {generatingPitch ? <><Loader2 style={{width:15,height:15,animation:"spin .8s linear infinite"}}/>Generating…</> : <><Zap style={{width:15,height:15}}/>Generate Pitch</>}
                  <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
                </button>
                {pitch && (
                  <div style={{position:"relative"}}>
                    <div style={{position:"absolute",top:10,right:10,display:"flex",gap:6}}>
                      <button onClick={()=>{navigator.clipboard.writeText(pitch);setPitchCopied(true);setTimeout(()=>setPitchCopied(false),2000);}}
                        style={{display:"flex",alignItems:"center",gap:5,padding:"5px 10px",borderRadius:7,background:pitchCopied?"rgba(52,211,153,.2)":"rgba(255,255,255,.08)",border:`1px solid ${pitchCopied?"rgba(52,211,153,.3)":"rgba(255,255,255,.12)"}`,color:pitchCopied?"#34d399":"#9ca3af",fontSize:11,cursor:"pointer"}}>
                        {pitchCopied ? <><Check style={{width:11,height:11}}/>Copied!</> : <><Copy style={{width:11,height:11}}/>Copy</>}
                      </button>
                      {data.email && <a href={`mailto:${data.email}?subject=Quick%20question&body=${encodeURIComponent(pitch)}`} style={{display:"flex",alignItems:"center",gap:5,padding:"5px 10px",borderRadius:7,background:"rgba(192,132,252,.15)",border:"1px solid rgba(192,132,252,.3)",color:"#c084fc",fontSize:11,textDecoration:"none"}}><Send style={{width:11,height:11}}/>Email</a>}
                      {data.phone && <a href={`https://wa.me/${waNumber}?text=${encodeURIComponent(pitch)}`} target="_blank" rel="noreferrer" style={{display:"flex",alignItems:"center",gap:5,padding:"5px 10px",borderRadius:7,background:"rgba(37,211,102,.15)",border:"1px solid rgba(37,211,102,.3)",color:"#25d366",fontSize:11,textDecoration:"none"}}><MessageCircle style={{width:11,height:11}}/>WA</a>}
                    </div>
                    <pre style={{whiteSpace:"pre-wrap",wordBreak:"break-word",fontSize:12.5,color:"#e5e7eb",lineHeight:1.75,background:"rgba(255,255,255,.03)",border:"1px solid rgba(255,255,255,.1)",borderRadius:12,padding:"44px 16px 16px",margin:0,fontFamily:"inherit"}}>
                      {pitch}
                    </pre>
                  </div>
                )}
              </div>
            )}

            {/* ═══ NOTES ═══ */}
            {tab==="notes" && (
              <div style={{display:"flex",flexDirection:"column",gap:14}}>
                <div style={{background:"rgba(255,255,255,.03)",border:"1px solid rgba(255,255,255,.08)",borderRadius:14,padding:16}}>
                  <Label>Log Activity</Label>
                  <div style={{display:"flex",gap:6,marginTop:8,marginBottom:10,flexWrap:"wrap"}}>
                    {NOTE_TYPES.map(t=>(
                      <button key={t.key} onClick={()=>setNoteType(t.key)}
                        style={{display:"flex",alignItems:"center",gap:4,padding:"5px 10px",borderRadius:7,border:`1px solid ${noteType===t.key?"#6366f1":"rgba(255,255,255,.1)"}`,background:noteType===t.key?"rgba(99,102,241,.2)":"transparent",color:noteType===t.key?"#a5b4fc":"#6b7280",fontSize:11,fontWeight:600,cursor:"pointer"}}>
                        {t.emoji} {t.label}
                      </button>
                    ))}
                  </div>
                  <textarea value={noteText} onChange={e=>setNoteText(e.target.value)}
                    placeholder={`Write a ${noteType} note about ${data.name}…`} rows={3}
                    style={{width:"100%",background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.1)",borderRadius:8,padding:"10px 12px",fontSize:13,color:"#fff",outline:"none",resize:"vertical",boxSizing:"border-box",fontFamily:"inherit",lineHeight:1.5}}/>
                  <button onClick={saveNote} disabled={!noteText.trim()||savingNote}
                    style={{marginTop:8,display:"flex",alignItems:"center",gap:6,padding:"8px 16px",borderRadius:8,background:noteText.trim()?"#4f46e5":"#1f2937",border:"none",color:noteText.trim()?"#fff":"#4b5563",fontSize:12,fontWeight:600,cursor:noteText.trim()?"pointer":"not-allowed"}}>
                    {savingNote ? <Loader2 style={{width:13,height:13,animation:"spin .8s linear infinite"}}/> : <StickyNote style={{width:13,height:13}}/>}
                    Save {NOTE_TYPES.find(t=>t.key===noteType)?.label}
                  </button>
                </div>
                {activities.length > 0 ? activities.map(act => {
                  const t = NOTE_TYPES.find(n=>n.key===act.type);
                  return (
                    <div key={act.id} style={{display:"flex",gap:12,padding:"12px 14px",background:"rgba(255,255,255,.03)",border:"1px solid rgba(255,255,255,.06)",borderRadius:12}}>
                      <div style={{fontSize:18,flexShrink:0}}>{t?.emoji??"📌"}</div>
                      <div style={{flex:1,minWidth:0}}>
                        <p style={{fontSize:13,color:"#e5e7eb",margin:0,lineHeight:1.6}}>{act.note}</p>
                        <p style={{fontSize:10,color:"#4b5563",margin:"4px 0 0"}}>{t?.label??act.type} · {act.createdAt ? new Date(act.createdAt).toLocaleString() : "—"}</p>
                      </div>
                    </div>
                  );
                }) : <p style={{textAlign:"center",color:"#4b5563",fontSize:13,padding:"24px 0"}}>No activity yet — add a note above</p>}
              </div>
            )}

            {/* ═══ CRM ═══ */}
            {tab==="crm" && (
              <div style={{display:"flex",flexDirection:"column",gap:16}}>
                <div>
                  <Label>Pipeline Stage</Label>
                  <div style={{display:"flex",alignItems:"center",marginTop:10,overflowX:"auto",paddingBottom:4}}>
                    {CRM_STAGES.map((stage,i) => (
                      <div key={stage.key} style={{display:"flex",alignItems:"center",flexShrink:0}}>
                        <button onClick={()=>setCrmStatus(stage.key)}
                          style={{display:"flex",flexDirection:"column",alignItems:"center",gap:5,padding:"10px 14px",borderRadius:10,border:`2px solid ${crmStatus===stage.key?stage.color:"rgba(255,255,255,.08)"}`,background:crmStatus===stage.key?`${stage.color}20`:"rgba(255,255,255,.03)",color:crmStatus===stage.key?stage.color:"#6b7280",cursor:"pointer",transition:"all .15s",minWidth:72}}>
                          <span style={{fontSize:11,fontWeight:700,whiteSpace:"nowrap"}}>{stage.label}</span>
                        </button>
                        {i < CRM_STAGES.length-1 && <ChevronRight style={{width:14,height:14,color:"#374151",flexShrink:0,margin:"0 2px"}}/>}
                      </div>
                    ))}
                  </div>
                </div>
                <div>
                  <Label>CRM Notes</Label>
                  <textarea value={crmNotes} onChange={e=>setCrmNotes(e.target.value)}
                    placeholder={`Notes about conversations with ${data.name}…`} rows={5}
                    style={{width:"100%",marginTop:8,background:"rgba(255,255,255,.05)",border:"1px solid rgba(255,255,255,.1)",borderRadius:10,padding:"12px",fontSize:13,color:"#fff",outline:"none",resize:"vertical",boxSizing:"border-box",fontFamily:"inherit",lineHeight:1.6}}/>
                </div>
                <button onClick={saveCrm} disabled={savingCrm}
                  style={{display:"flex",alignItems:"center",justifyContent:"center",gap:8,padding:"12px",borderRadius:10,background:savingCrm?"#374151":"#059669",border:"none",color:"#fff",fontSize:13,fontWeight:700,cursor:savingCrm?"not-allowed":"pointer"}}>
                  {savingCrm ? <><Loader2 style={{width:15,height:15,animation:"spin .8s linear infinite"}}/>Saving…</> : <><TrendingUp style={{width:15,height:15}}/>Save CRM Status</>}
                </button>
                <div style={{borderTop:"1px solid rgba(255,255,255,.06)",paddingTop:14}}>
                  <Label>Quick Actions</Label>
                  <div style={{display:"flex",gap:8,marginTop:10,flexWrap:"wrap"}}>
                    {data.phone && <a href={`https://wa.me/${waNumber}`} target="_blank" rel="noreferrer" style={{display:"flex",alignItems:"center",gap:6,padding:"9px 14px",borderRadius:9,background:"rgba(37,211,102,.12)",border:"1px solid rgba(37,211,102,.3)",color:"#25d366",fontSize:12,fontWeight:600,textDecoration:"none"}}><MessageCircle style={{width:14,height:14}}/>WhatsApp</a>}
                    {data.email && <a href={`mailto:${data.email}`} style={{display:"flex",alignItems:"center",gap:6,padding:"9px 14px",borderRadius:9,background:"rgba(192,132,252,.12)",border:"1px solid rgba(192,132,252,.3)",color:"#c084fc",fontSize:12,fontWeight:600,textDecoration:"none"}}><Mail style={{width:14,height:14}}/>Email</a>}
                    <button onClick={()=>setTab("pitch")} style={{display:"flex",alignItems:"center",gap:6,padding:"9px 14px",borderRadius:9,background:"rgba(99,102,241,.12)",border:"1px solid rgba(99,102,241,.3)",color:"#818cf8",fontSize:12,fontWeight:600,cursor:"pointer"}}><FileText style={{width:14,height:14}}/>Generate Pitch</button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

// ── Small layout helpers ──────────────────────────────────────────────────────
function Section({ title, icon, children }: { title:string; icon:string; children:React.ReactNode }) {
  return (
    <div>
      <div style={{display:"flex",alignItems:"center",gap:7,marginBottom:12}}>
        <span style={{fontSize:14}}>{icon}</span>
        <h3 style={{fontSize:11,fontWeight:700,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.1em",margin:0}}>{title}</h3>
      </div>
      {children}
    </div>
  );
}

function Stat({ children }: { children:React.ReactNode }) {
  return <div style={{padding:"14px 0",textAlign:"center",background:"rgba(255,255,255,.03)",borderRadius:12,border:"1px solid rgba(255,255,255,.07)"}}>{children}</div>;
}

function ContactRow({ icon, children }: { icon:React.ReactNode; children:React.ReactNode }) {
  return (
    <div style={{display:"flex",alignItems:"center",gap:10,marginBottom:8}}>
      <div style={{flexShrink:0}}>{icon}</div>
      <div style={{display:"flex",alignItems:"center",gap:6,flex:1,minWidth:0}}>{children}</div>
    </div>
  );
}

function Label({ children }: { children:React.ReactNode }) {
  return <p style={{fontSize:11,fontWeight:700,color:"#6b7280",textTransform:"uppercase",letterSpacing:"0.1em",margin:0}}>{children}</p>;
}
