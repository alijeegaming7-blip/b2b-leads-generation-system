import { useState, useEffect, useCallback } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Mail, Search, Send, CheckCircle2, RefreshCw, Users, Zap, AlertCircle } from "lucide-react";
import { api } from "../lib/api";
import LeadDetailModal from "../components/LeadDetailModal";
import type { FullLead } from "../components/LeadDetailModal";

// Use FullLead for detail modal; local interface just for list display
interface EmailLead {
  id:string; name:string; email:string; address:string; score:number;
  priority:string; category:string; email_sent:boolean; email_opened:boolean;
  email_replied:boolean; email_bounced:boolean;
}
interface Stats { totalSent:number; dailyLimit:number; remaining:number; }

const TMPLS = [
  { label:"Intro",    subj:"Quick question about your online presence",
    body:(n:string)=>`Hi ${n},\n\nI came across your business and noticed you might benefit from a stronger online presence.\n\nWe help businesses like yours get more customers through professional websites and SEO.\n\nWould you be open to a quick 10-minute call this week?\n\nBest regards,\n[Your Name]` },
  { label:"SEO",     subj:"Your website is losing customers",
    body:(n:string)=>`Hi ${n},\n\nI ran a quick audit on your website and found several issues that may be costing you customers.\n\nI'd love to send you a free report. Interested?\n\nBest,\n[Your Name]` },
  { label:"Follow-up",subj:"Following up on my last message",
    body:(n:string)=>`Hi ${n},\n\nJust following up! We offer a free consultation with no commitment.\n\nWould 15 minutes this week work?\n\nBest,\n[Your Name]` },
  { label:"Offer",    subj:"Free resource for your business",
    body:(n:string)=>`Hi ${n},\n\nWe're running a special offer this month — free website audit + consultation.\n\nNo strings attached. Interested?\n\nBest,\n[Your Name]` },
];

export default function EmailPage() {
  const [leads, setLeads] = useState<EmailLead[]>([]);
  const [stats, setStats] = useState<Stats|null>(null);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<"all"|"unsent"|"sent">("all");
  const [selected, setSelected] = useState<EmailLead|null>(null);
  const [tpl, setTpl] = useState(0);
  const [subj, setSubj] = useState(TMPLS[0].subj);
  const [body, setBody] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState<Set<string>>(new Set());
  const [selectedDetail, setSelectedDetail] = useState<FullLead|null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ld, st] = await Promise.all([api.get<any>("/leads?limit=200"), api.get<Stats>("/email/stats").catch(()=>null)]);
      const arr = ld.data ?? ld.leads ?? ld;
      setLeads((Array.isArray(arr) ? arr : []).filter((l:EmailLead)=>l.email));
      setStats(st);
    } catch { setLeads([]); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { setSubj(TMPLS[tpl].subj); if (selected) setBody(TMPLS[tpl].body(selected.name)); }, [tpl, selected]);
  useEffect(() => { if (selected) setBody(TMPLS[tpl].body(selected.name)); }, [selected]); // eslint-disable-line

  const filtered = leads.filter(l => {
    const q=search.toLowerCase();
    return (!q||l.name?.toLowerCase().includes(q)||l.email?.toLowerCase().includes(q))
      && (filter==="all"||(filter==="sent"?(l.email_sent||sent.has(l.id)):(!l.email_sent&&!sent.has(l.id))));
  });

  async function sendEmail(lead:EmailLead) {
    setSending(true);
    try {
      await api.post("/email/send", { to:lead.email, subject:subj, body, lead_id:lead.id });
      setSent(s=>new Set([...s,lead.id]));
    } catch { alert("Send failed — configure Gmail in Settings first"); } finally { setSending(false); }
  }

  async function openDetail(id: string) {
    try {
      const full = await api.get<FullLead>(`/leads/${id}`);
      setSelectedDetail(full);
    } catch { /* ignore */ }
  }

  async function sendBulk() {
    const targets = filtered.filter(l=>!sent.has(l.id)&&!l.email_sent).slice(0, stats?.remaining??10);
    if (!targets.length) { alert("No unsent leads or daily limit reached"); return; }
    if (!confirm(`Send to ${targets.length} leads?`)) return;
    setSending(true);
    try {
      await api.post("/email/bulk", { emails:targets.map(l=>({ to:l.email, subject:subj, body:TMPLS[tpl].body(l.name), lead_id:l.id })), daily_limit:stats?.remaining??10, delay_seconds:90 });
      targets.forEach(l=>setSent(s=>new Set([...s,l.id])));
    } catch { alert("Bulk send failed — check Gmail configuration in Settings"); } finally { setSending(false); }
  }

  return (
    <div style={{ display:"flex", height:"100%", background:"#05050f", overflow:"hidden" }}>
      {/* Left panel */}
      <div style={{ width:350, flexShrink:0, borderRight:"1px solid rgba(255,255,255,.06)", display:"flex", flexDirection:"column" }}>
        <div style={{ padding:"16px", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:12 }}>
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              <div style={{ width:32, height:32, borderRadius:10, background:"rgba(96,165,250,.15)", display:"flex", alignItems:"center", justifyContent:"center" }}><Mail style={{width:16,height:16,color:"#60a5fa"}}/></div>
              <div><p style={{ fontSize:13, fontWeight:700, color:"#fff" }}>Email Agent</p><p style={{ fontSize:10, color:"#6b7280" }}>{filtered.length} leads with email</p></div>
            </div>
            <button onClick={load} style={{ background:"none", border:"none", color:"#6b7280", cursor:"pointer" }}><RefreshCw style={{width:14,height:14}}/></button>
          </div>
          <div style={{ position:"relative", marginBottom:10 }}>
            <Search style={{ position:"absolute", left:10, top:"50%", transform:"translateY(-50%)", width:13, height:13, color:"#6b7280" }}/>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search leads…"
              style={{ paddingLeft:30, paddingRight:10, height:32, width:"100%", background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, fontSize:12, color:"#fff", outline:"none" }}/>
          </div>
          <div style={{ display:"flex", gap:6 }}>
            {(["all","unsent","sent"] as const).map(f=>(
              <button key={f} onClick={()=>setFilter(f)} style={{ flex:1, padding:"5px 0", borderRadius:8, fontSize:11, fontWeight:500, cursor:"pointer", border:"none", background:filter===f?"#3b82f6":"rgba(255,255,255,.06)", color:filter===f?"#fff":"#9ca3af", textTransform:"capitalize" }}>{f}</button>
            ))}
          </div>
        </div>
        {stats && (
          <div style={{ display:"flex", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
            {[{l:"Sent",v:stats.totalSent,c:"#60a5fa"},{l:"Remaining",v:stats.remaining,c:"#fbbf24"},{l:"Limit",v:stats.dailyLimit,c:"#6b7280"}].map(s=>(
              <div key={s.l} style={{ flex:1, padding:"8px 0", textAlign:"center", borderRight:"1px solid rgba(255,255,255,.06)" }}>
                <p style={{ fontSize:15, fontWeight:700, color:s.c }}>{s.v}</p><p style={{ fontSize:10, color:"#6b7280" }}>{s.l}</p>
              </div>
            ))}
          </div>
        )}
        <div style={{ flex:1, overflowY:"auto" }}>
          {loading ? <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:100, color:"#4b5563", fontSize:12 }}>Loading…</div>
           : filtered.length===0 ? <div style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", height:100, color:"#374151" }}><Users style={{width:24,height:24,opacity:.3}}/><p style={{fontSize:12,marginTop:8}}>No leads with emails yet</p></div>
           : filtered.map(lead=>{
               const isSent=lead.email_sent||sent.has(lead.id), isActive=selected?.id===lead.id;
               return (
                 <button key={lead.id} onClick={()=>setSelected(lead)} onContextMenu={(e)=>{e.preventDefault();openDetail(lead.id);}}
                   onDoubleClick={()=>openDetail(lead.id)}
                   style={{ width:"100%", textAlign:"left", padding:"10px 16px", borderBottom:"1px solid rgba(255,255,255,.04)", background:isActive?"rgba(96,165,250,.05)":"transparent", borderLeft:isActive?"3px solid #60a5fa":"3px solid transparent", cursor:"pointer" }}>
                   <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", gap:8 }}>
                     <div style={{ flex:1, minWidth:0 }}>
                       <p style={{ fontSize:12, fontWeight:500, color:"#fff", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{lead.name}</p>
                       <p style={{ fontSize:11, color:"#6b7280", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{lead.email}</p>
                     </div>
                     <div style={{ display:"flex", flexDirection:"column", alignItems:"flex-end", gap:3 }}>
                       {isSent && <span style={{ fontSize:10, color:"#60a5fa", display:"flex", alignItems:"center", gap:3 }}><CheckCircle2 style={{width:10,height:10}}/>Sent</span>}
                       {lead.email_opened  && <span style={{ fontSize:9, color:"#34d399" }}>Opened</span>}
                       {lead.email_replied && <span style={{ fontSize:9, color:"#c084fc" }}>Replied</span>}
                       {lead.email_bounced && <span style={{ fontSize:9, color:"#f87171" }}>Bounced</span>}
                     </div>
                   </div>
                 </button>
               );
             })}
        </div>
        <div style={{ padding:"12px 16px", borderTop:"1px solid rgba(255,255,255,.06)" }}>
          <button onClick={sendBulk} disabled={sending}
            style={{ width:"100%", display:"flex", alignItems:"center", justifyContent:"center", gap:8, padding:"10px", background:sending?"#374151":"#3b82f6", border:"none", borderRadius:8, fontSize:13, color:"#fff", fontWeight:600, cursor:sending?"not-allowed":"pointer" }}>
            <Zap style={{width:14,height:14}}/>{sending?"Sending…":"Bulk Send to All Unsent"}
          </button>
          <p style={{ fontSize:10, color:"#4b5563", textAlign:"center", marginTop:6 }}>90s delay · CAN-SPAM compliant</p>
        </div>
      </div>

      {/* Right composer */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
        {selected ? <>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"16px 24px", borderBottom:"1px solid rgba(255,255,255,.06)", background:"rgba(255,255,255,.02)" }}>
            <div style={{ display:"flex", alignItems:"center", gap:12 }}>
              <div style={{ width:40, height:40, borderRadius:"50%", background:"rgba(96,165,250,.15)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18 }}>🏢</div>
              <div><p style={{ fontSize:13, fontWeight:600, color:"#fff" }}>{selected.name}</p><p style={{ fontSize:11, color:"#6b7280" }}>{selected.email}</p></div>
            </div>
            <div style={{ display:"flex", gap:8 }}>
              {selected.email_opened  && <span style={{ fontSize:11, color:"#34d399", display:"flex", alignItems:"center", gap:4 }}><CheckCircle2 style={{width:12,height:12}}/>Opened</span>}
              {selected.email_replied && <span style={{ fontSize:11, color:"#c084fc", display:"flex", alignItems:"center", gap:4 }}><Mail style={{width:12,height:12}}/>Replied</span>}
              {selected.email_bounced && <span style={{ fontSize:11, color:"#f87171", display:"flex", alignItems:"center", gap:4 }}><AlertCircle style={{width:12,height:12}}/>Bounced</span>}
            </div>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:8, padding:"8px 24px", borderBottom:"1px solid rgba(255,255,255,.04)", background:"rgba(0,0,0,.2)", overflowX:"auto" }}>
            <span style={{ fontSize:10, color:"#6b7280", flexShrink:0 }}>Templates:</span>
            {TMPLS.map((t,i)=>(
              <button key={t.label} onClick={()=>setTpl(i)}
                style={{ flexShrink:0, padding:"4px 10px", borderRadius:8, fontSize:11, cursor:"pointer", border:"none", background:tpl===i?"#3b82f6":"rgba(255,255,255,.06)", color:tpl===i?"#fff":"#d1d5db", fontWeight:tpl===i?600:400 }}>{t.label}</button>
            ))}
          </div>
          <div style={{ flex:1, padding:"20px 24px", display:"flex", flexDirection:"column", gap:14, overflowY:"auto" }}>
            <div>
              <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>Subject</label>
              <input value={subj} onChange={e=>setSubj(e.target.value)}
                style={{ width:"100%", height:38, background:"rgba(255,255,255,.03)", border:"1px solid rgba(255,255,255,.1)", borderRadius:10, padding:"0 12px", fontSize:13, color:"#fff", outline:"none" }}/>
            </div>
            <div style={{ flex:1 }}>
              <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>Message</label>
              <textarea value={body} onChange={e=>setBody(e.target.value)} rows={12}
                style={{ width:"100%", background:"rgba(255,255,255,.03)", border:"1px solid rgba(255,255,255,.1)", borderRadius:12, padding:"12px 14px", fontSize:13, color:"#fff", outline:"none", resize:"none", lineHeight:1.7 }}/>
            </div>
            <div style={{ display:"flex", alignItems:"center", gap:12, paddingTop:14, borderTop:"1px solid rgba(255,255,255,.06)" }}>
              <p style={{ flex:1, fontSize:11, color:"#4b5563" }}>📧 Sends via Gmail SMTP · Configure in Settings{stats?` · ${stats.remaining} remaining today`:""}</p>
              <button onClick={()=>sendEmail(selected)} disabled={sending}
                style={{ display:"flex", alignItems:"center", gap:8, padding:"10px 20px", background:sending?"#374151":"#3b82f6", border:"none", borderRadius:8, fontSize:13, color:"#fff", fontWeight:600, cursor:sending?"not-allowed":"pointer" }}>
                <Send style={{width:14,height:14}}/>{sending?"Sending…":(sent.has(selected.id)||selected.email_sent)?"Resend":"Send Email"}
              </button>
            </div>
          </div>
        </>
        : <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:12, color:"#374151" }}>
            <Mail style={{width:52,height:52,opacity:.2}}/>
            <p style={{ fontSize:13, color:"#6b7280" }}>Select a lead to compose an email</p>
            <p style={{ fontSize:11, color:"#4b5563" }}>Configure Gmail in Settings to start sending</p>
          </div>}
      </div>
      <LeadDetailModal lead={selectedDetail} onClose={()=>setSelectedDetail(null)} />
    </div>
  );
}
