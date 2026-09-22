import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, Phone, Search, Send, CheckCircle2, Copy, ExternalLink, RefreshCw, Users } from "lucide-react";
import { api } from "../lib/api";
import LeadDetailModal from "../components/LeadDetailModal";
import type { FullLead } from "../components/LeadDetailModal";

interface WaLead { business_name:string; phone:string; address:string; score:number; from_agent:string; waUrl:string; digits:string; templateMessage:string; timestamp:string; }
const ACOLORS: Record<string,string> = { website_dev:"#818cf8", seo_audit:"#fbbf24", inventory_systems:"#34d399", analytics_dashboards:"#60a5fa", ai_assistants:"#c084fc" };
const ALABELS: Record<string,string> = { website_dev:"WebVerse", seo_audit:"SEOVerse", inventory_systems:"StockVerse", analytics_dashboards:"DataVerse", ai_assistants:"AIVerse" };
const TMPLS = [
  { label:"Intro",    msg:(n:string)=>`Hi ${n}! I noticed your business online and wanted to connect about growing your digital presence. Would you be open to a quick chat? 🚀` },
  { label:"Website",  msg:(n:string)=>`Hi ${n}! I noticed you may not have a website yet. We build fast, mobile-friendly websites that bring in new customers 24/7. Interested? 💻` },
  { label:"Follow-up",msg:(n:string)=>`Hi ${n}! Just following up — we'd love to help your business grow online. When's a good time to chat? 😊` },
  { label:"Offer",    msg:(n:string)=>`Hi ${n}! We're running a special promotion this month — free website audit + consultation. No commitment. Interested? 🎁` },
];

export default function WhatsAppPage() {
  const [leads, setLeads] = useState<WaLead[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [selected, setSelected] = useState<WaLead|null>(null);
  const [msg, setMsg] = useState("");
  const [sent, setSent] = useState<Set<string>>(new Set());
  const [copied, setCopied] = useState(false);
  const [selectedDetail, setSelectedDetail] = useState<FullLead|null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { const d = await api.get<{leads:WaLead[]}>("/agents/whatsapp/leads"); setLeads(d.leads??[]); }
    catch { setLeads([]); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { if (selected) setMsg(selected.templateMessage); }, [selected]);

  const filtered = leads.filter(l => { const q=search.toLowerCase(); return !q||l.business_name?.toLowerCase().includes(q)||l.phone?.includes(q); });

  function sendWa(lead:WaLead, message:string) {
    window.open(`${lead.waUrl}?text=${encodeURIComponent(message)}`,"_blank");
    setSent(s=>new Set([...s,lead.digits]));
  }

  return (
    <div style={{ display:"flex", height:"100%", background:"#05050f", overflow:"hidden" }}>
      {/* Left panel */}
      <div style={{ width:360, flexShrink:0, borderRight:"1px solid rgba(255,255,255,.06)", display:"flex", flexDirection:"column" }}>
        <div style={{ padding:"16px", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:12 }}>
            <div style={{ display:"flex", alignItems:"center", gap:10 }}>
              <div style={{ width:32, height:32, borderRadius:10, background:"rgba(52,211,153,.15)", display:"flex", alignItems:"center", justifyContent:"center" }}><MessageCircle style={{width:16,height:16,color:"#34d399"}}/></div>
              <div><p style={{ fontSize:13, fontWeight:700, color:"#fff" }}>WhatsApp Agent</p><p style={{ fontSize:10, color:"#6b7280" }}>{filtered.length} leads with phone</p></div>
            </div>
            <button onClick={load} style={{ background:"none", border:"none", color:"#6b7280", cursor:"pointer" }}><RefreshCw style={{width:14,height:14}}/></button>
          </div>
          <div style={{ position:"relative" }}>
            <Search style={{ position:"absolute", left:10, top:"50%", transform:"translateY(-50%)", width:13, height:13, color:"#6b7280" }}/>
            <input value={search} onChange={e=>setSearch(e.target.value)} placeholder="Search by name or phone…"
              style={{ paddingLeft:30, paddingRight:10, height:32, width:"100%", background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, fontSize:12, color:"#fff", outline:"none" }}/>
          </div>
        </div>
        <div style={{ display:"flex", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
          {[{l:"Total",v:leads.length,c:"#818cf8"},{l:"Sent",v:sent.size,c:"#34d399"},{l:"Pending",v:leads.length-sent.size,c:"#fbbf24"}].map(s=>(
            <div key={s.l} style={{ flex:1, padding:"10px 0", textAlign:"center", borderRight:"1px solid rgba(255,255,255,.06)" }}>
              <p style={{ fontSize:16, fontWeight:700, color:s.c }}>{s.v}</p>
              <p style={{ fontSize:10, color:"#6b7280" }}>{s.l}</p>
            </div>
          ))}
        </div>
        <div style={{ flex:1, overflowY:"auto" }}>
          {loading ? <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:120, color:"#4b5563", fontSize:12 }}>Loading…</div>
           : filtered.length===0 ? <div style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", height:120, gap:8, color:"#374151" }}><Users style={{width:28,height:28,opacity:.3}}/><p style={{fontSize:12}}>No leads with phone numbers yet</p></div>
           : <AnimatePresence initial={false}>
               {filtered.map((lead,i)=>{
                 const isSent=sent.has(lead.digits), isActive=selected?.digits===lead.digits;
                 return (
                   <motion.button key={`${lead.digits}-${i}`} initial={{opacity:0,x:-10}} animate={{opacity:1,x:0}}
                     onClick={()=>setSelected(lead)} onDoubleClick={async()=>{
                       try { const full = await api.get<FullLead>(`/leads/${lead.digits}`); setSelectedDetail(full); } catch {/* ignore */}
                     }}
                     style={{ width:"100%", textAlign:"left", padding:"12px 16px", borderBottom:"1px solid rgba(255,255,255,.04)", background:isActive?"rgba(52,211,153,.05)":"transparent", borderLeft:isActive?"3px solid #34d399":"3px solid transparent", cursor:"pointer" }}>
                     <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", gap:8 }}>
                       <div style={{ flex:1, minWidth:0 }}>
                         <p style={{ fontSize:12, fontWeight:500, color:"#fff", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{lead.business_name}</p>
                         <p style={{ fontSize:11, color:"#6b7280", display:"flex", alignItems:"center", gap:4, marginTop:2 }}><Phone style={{width:10,height:10}}/>{lead.phone}</p>
                       </div>
                       <div style={{ display:"flex", flexDirection:"column", alignItems:"flex-end", gap:4 }}>
                         {isSent ? <span style={{ fontSize:10, color:"#34d399", display:"flex", alignItems:"center", gap:3 }}><CheckCircle2 style={{width:10,height:10}}/>Sent</span>
                           : <span style={{ width:8, height:8, borderRadius:"50%", background:"#fbbf24", marginTop:4, display:"inline-block" }}/>}
                         <span style={{ fontSize:10, color:ACOLORS[lead.from_agent]??"#818cf8" }}>{ALABELS[lead.from_agent]??lead.from_agent}</span>
                       </div>
                     </div>
                   </motion.button>
                 );
               })}
             </AnimatePresence>}
        </div>
      </div>

      {/* Right composer */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden" }}>
        {selected ? <>
          <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"16px 24px", borderBottom:"1px solid rgba(255,255,255,.06)", background:"rgba(255,255,255,.02)" }}>
            <div style={{ display:"flex", alignItems:"center", gap:12 }}>
              <div style={{ width:40, height:40, borderRadius:"50%", background:"rgba(52,211,153,.15)", display:"flex", alignItems:"center", justifyContent:"center", fontSize:18 }}>🏢</div>
              <div><p style={{ fontSize:13, fontWeight:600, color:"#fff" }}>{selected.business_name}</p>
                <p style={{ fontSize:11, color:"#6b7280", display:"flex", alignItems:"center", gap:4 }}><Phone style={{width:10,height:10}}/>{selected.phone}</p>
              </div>
            </div>
            <a href={selected.waUrl} target="_blank" rel="noreferrer" style={{ display:"flex", alignItems:"center", gap:6, padding:"6px 12px", background:"rgba(52,211,153,.15)", border:"1px solid rgba(52,211,153,.3)", borderRadius:8, fontSize:12, color:"#34d399" }}>
              <ExternalLink style={{width:12,height:12}}/>Open WhatsApp
            </a>
          </div>
          <div style={{ display:"flex", alignItems:"center", gap:8, padding:"8px 24px", borderBottom:"1px solid rgba(255,255,255,.04)", background:"rgba(0,0,0,.2)", overflowX:"auto" }}>
            <span style={{ fontSize:10, color:"#6b7280", flexShrink:0 }}>Templates:</span>
            {TMPLS.map((t,i)=>(
              <button key={t.label} onClick={()=>setMsg(t.msg(selected.business_name))}
                style={{ flexShrink:0, padding:"4px 10px", borderRadius:8, fontSize:11, fontWeight:500, cursor:"pointer", background:"rgba(255,255,255,.06)", border:"1px solid rgba(255,255,255,.1)", color:"#d1d5db" }}>
                {t.label}
              </button>
            ))}
          </div>
          <div style={{ flex:1, padding:"20px 24px", display:"flex", flexDirection:"column", gap:16, overflowY:"auto" }}>
            <div>
              <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:8 }}>WhatsApp Message</label>
              <textarea value={msg} onChange={e=>setMsg(e.target.value)} rows={8}
                style={{ width:"100%", background:"rgba(255,255,255,.03)", border:"1px solid rgba(255,255,255,.1)", borderRadius:12, padding:"14px", fontSize:13, color:"#fff", outline:"none", resize:"none", lineHeight:1.6 }}/>
              <p style={{ fontSize:10, color:"#4b5563", marginTop:4 }}>{msg.length} chars</p>
            </div>
            <div style={{ display:"flex", gap:10, marginTop:"auto", paddingTop:16, borderTop:"1px solid rgba(255,255,255,.06)" }}>
              <button onClick={()=>{navigator.clipboard.writeText(msg);setCopied(true);setTimeout(()=>setCopied(false),2000);}}
                style={{ display:"flex", alignItems:"center", gap:6, padding:"10px 16px", background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, fontSize:13, color:"#d1d5db", cursor:"pointer" }}>
                {copied?<CheckCircle2 style={{width:14,height:14,color:"#34d399"}}/>:<Copy style={{width:14,height:14}}/>}
                {copied?"Copied!":"Copy"}
              </button>
              <button onClick={()=>sendWa(selected,msg)}
                style={{ flex:1, display:"flex", alignItems:"center", justifyContent:"center", gap:8, padding:"10px", background:"#059669", border:"none", borderRadius:8, fontSize:13, color:"#fff", fontWeight:600, cursor:"pointer" }}>
                <Send style={{width:14,height:14}}/>Send via WhatsApp
              </button>
            </div>
          </div>
        </>
        : <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", gap:12, color:"#374151" }}>
            <MessageCircle style={{width:56,height:56,opacity:.2}}/>
            <p style={{ fontSize:13, color:"#6b7280" }}>Select a lead to compose a message</p>
            <p style={{ fontSize:11, color:"#4b5563" }}>Messages open directly in WhatsApp</p>
          </div>}
      </div>
      <LeadDetailModal lead={selectedDetail as any} onClose={()=>setSelectedDetail(null)} />
    </div>
  );
}
