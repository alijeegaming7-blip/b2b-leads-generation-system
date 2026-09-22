import { useState, useEffect, useCallback, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Plus, Play, Trash2, RefreshCw, CheckCircle2, Clock, AlertCircle, Loader2, ChevronDown, X, Search } from "lucide-react";
import { api } from "../lib/api";
import { GEO, CATEGORIES, COUNTRIES } from "../lib/geoData";

interface Campaign { id:string; name:string; industry:string; location:string; status:string; progress:number; totalLeads:number; priorityLeads:number; createdAt:string; startedAt:string|null; completedAt:string|null; error:string|null; }

const STATUS_STYLE: Record<string,{bg:string;color:string;icon:React.ReactNode}> = {
  draft:     { bg:"rgba(148,163,184,.12)", color:"#94a3b8", icon:<Clock style={{width:11,height:11}}/> },
  running:   { bg:"rgba(251,191,36,.12)",  color:"#fbbf24", icon:<Loader2 style={{width:11,height:11,animation:"spin .8s linear infinite"}}/> },
  completed: { bg:"rgba(52,211,153,.12)",  color:"#34d399", icon:<CheckCircle2 style={{width:11,height:11}}/> },
  failed:    { bg:"rgba(248,113,113,.12)", color:"#f87171", icon:<AlertCircle style={{width:11,height:11}}/> },
};

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [showNew, setShowNew] = useState(false);
  const [polling, setPolling] = useState<Set<string>>(new Set());
  const pollRef = useRef<Record<string,ReturnType<typeof setInterval>>>({});

  // New campaign form
  const [name, setName] = useState(""); const [industry, setIndustry] = useState(CATEGORIES[0]);
  const [country, setCountry] = useState("United States"); const [city, setCity] = useState("New York");
  const [maxRes, setMaxRes] = useState(50); const [service, setService] = useState("Web Development");
  const [creating, setCreating] = useState(false);
  const [openDd, setOpenDd] = useState<string|null>(null);

  useEffect(() => { if (!GEO[country]) return; setCity(GEO[country][0]); }, [country]);

  const load = useCallback(async () => {
    setLoading(true);
    try { const d = await api.get<Campaign[]>("/campaigns"); setCampaigns(d??[]); }
    catch { setCampaigns([]); } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); return ()=>{ Object.values(pollRef.current).forEach(clearInterval); }; }, [load]);

  function startPolling(id:string) {
    setPolling(p=>new Set([...p,id]));
    pollRef.current[id] = setInterval(async()=>{
      try {
        const s = await api.get<{status:string;progress:number;totalLeads:number;error:string|null}>(`/campaigns/${id}/status`);
        setCampaigns(prev=>prev.map(c=>c.id===id?{...c,...s}:c));
        if (s.status!=="running") { clearInterval(pollRef.current[id]); delete pollRef.current[id]; setPolling(p=>{const n=new Set(p);n.delete(id);return n;}); }
      } catch { clearInterval(pollRef.current[id]); }
    }, 2500);
  }

  async function runCampaign(id:string) {
    try { await api.post(`/campaigns/${id}/run`,{}); startPolling(id); await load(); }
    catch (e:any) { alert(e.message??"Failed to start"); }
  }

  async function deleteCampaign(id:string) {
    if (!confirm("Delete this campaign?")) return;
    await api.delete(`/campaigns/${id}`); setCampaigns(p=>p.filter(c=>c.id!==id));
  }

  async function createCampaign() {
    if (!name.trim()) { alert("Give your campaign a name"); return; }
    setCreating(true);
    try {
      const c = await api.post<Campaign>("/campaigns",{ name, industry, location:`${city}, ${country}`, search_queries:[`${industry} in ${city}`], max_results:maxRes, your_service:service, content_style:"balanced", language:"english", sources:["google_maps"] });
      setCampaigns(p=>[c,...p]); setShowNew(false); setName("");
    } catch (e:any) { alert(e.message??"Creation failed"); } finally { setCreating(false); }
  }

  function DD({ id, value, options, onSelect }: { id:string; value:string; options:string[]; onSelect:(v:string)=>void }) {
    const [q, setQ] = useState("");
    const filtered = q ? options.filter(o => o.toLowerCase().includes(q.toLowerCase())) : options;

    return (
      <div style={{ position:"relative" }} onClick={e=>e.stopPropagation()}>
        <button onClick={()=>{setQ("");setOpenDd(p=>p===id?null:id);}} style={{ display:"flex", alignItems:"center", gap:6, width:"100%", height:36, padding:"0 10px", background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, fontSize:12, color:"#e5e7eb", cursor:"pointer" }}>
          <span style={{ flex:1, textAlign:"left", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{value}</span>
          <ChevronDown style={{width:12,height:12,color:"#6b7280"}}/>
        </button>
        {openDd===id && <div style={{ position:"absolute", left:0, top:40, zIndex:200, background:"#0d0d1f", border:"1px solid rgba(255,255,255,.12)", borderRadius:10, boxShadow:"0 20px 40px rgba(0,0,0,.7)", width:"100%", minWidth:200 }}>
          <div style={{ padding:"8px 10px", borderBottom:"1px solid rgba(255,255,255,.08)", display:"flex", alignItems:"center", gap:6 }}>
            <Search style={{ width:12, height:12, color:"#6b7280", flexShrink:0 }} />
            <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Search…" autoFocus
              style={{ flex:1, background:"transparent", border:"none", outline:"none", fontSize:12, color:"#e5e7eb" }}
              onClick={e=>e.stopPropagation()} />
          </div>
          <div style={{ maxHeight:200, overflowY:"auto" }}>
            {filtered.length===0 && <p style={{ padding:"10px 12px", fontSize:11, color:"#4b5563" }}>No results</p>}
            {filtered.map(o=><button key={o} onClick={()=>{onSelect(o);setOpenDd(null);setQ("");}} style={{ display:"block", width:"100%", textAlign:"left", padding:"7px 12px", fontSize:12, color:"#d1d5db", background:"transparent", border:"none", cursor:"pointer" }}
              onMouseEnter={e=>((e.target as HTMLElement).style.background="rgba(255,255,255,.07)")} onMouseLeave={e=>((e.target as HTMLElement).style.background="transparent")}>{o}</button>)}
          </div>
        </div>}
      </div>
    );
  }

  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100%", background:"#05050f", overflow:"hidden" }} onClick={()=>setOpenDd(null)}>
      {/* Header */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"16px 24px", borderBottom:"1px solid rgba(255,255,255,.06)", flexShrink:0 }}>
        <div><h1 style={{ fontSize:20, fontWeight:700, color:"#fff" }}>Campaigns</h1><p style={{ fontSize:12, color:"#6b7280", marginTop:2 }}>{campaigns.length} campaigns</p></div>
        <div style={{ display:"flex", gap:8 }}>
          <button onClick={load} style={{ width:34, height:34, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, color:"#6b7280", display:"flex", alignItems:"center", justifyContent:"center", cursor:"pointer" }}><RefreshCw style={{width:14,height:14}}/></button>
          <button onClick={()=>setShowNew(true)} style={{ display:"flex", alignItems:"center", gap:6, height:34, padding:"0 14px", background:"#4f46e5", border:"none", borderRadius:8, fontSize:12, color:"#fff", fontWeight:600, cursor:"pointer" }}><Plus style={{width:14,height:14}}/>New Campaign</button>
        </div>
      </div>

      <div style={{ flex:1, overflowY:"auto", padding:"20px 24px" }}>
        {loading ? <div style={{ display:"flex", alignItems:"center", justifyContent:"center", height:120, color:"#4b5563", fontSize:12 }}>Loading…</div>
         : campaigns.length===0 ? <div style={{ display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", height:200, gap:12, color:"#374151" }}>
             <span style={{ fontSize:48 }}>🎯</span>
             <p style={{ fontSize:14, color:"#6b7280" }}>No campaigns yet</p>
             <button onClick={()=>setShowNew(true)} style={{ display:"flex", alignItems:"center", gap:6, padding:"8px 16px", background:"#4f46e5", border:"none", borderRadius:8, fontSize:12, color:"#fff", fontWeight:600, cursor:"pointer" }}><Plus style={{width:12,height:12}}/>Create your first campaign</button>
           </div>
         : <div style={{ display:"flex", flexDirection:"column", gap:10 }}>
             <AnimatePresence initial={false}>
               {campaigns.map(c=>{
                 const ss = STATUS_STYLE[c.status]??STATUS_STYLE.draft;
                 const isPolling = polling.has(c.id);
                 return (
                   <motion.div key={c.id} initial={{opacity:0,y:8}} animate={{opacity:1,y:0}} exit={{opacity:0}}
                     style={{ background:"rgba(255,255,255,.03)", border:"1px solid rgba(255,255,255,.07)", borderRadius:14, padding:"16px 20px" }}>
                     <div style={{ display:"flex", alignItems:"flex-start", justifyContent:"space-between", gap:12 }}>
                       <div style={{ flex:1, minWidth:0 }}>
                         <div style={{ display:"flex", alignItems:"center", gap:10, marginBottom:6 }}>
                           <h3 style={{ fontSize:14, fontWeight:600, color:"#fff", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{c.name}</h3>
                           <span style={{ display:"flex", alignItems:"center", gap:4, padding:"2px 8px", borderRadius:12, fontSize:10, fontWeight:500, background:ss.bg, color:ss.color, flexShrink:0 }}>
                             {ss.icon} {c.status}
                           </span>
                         </div>
                         <div style={{ display:"flex", gap:16, fontSize:11, color:"#6b7280", flexWrap:"wrap" }}>
                           <span>📍 {c.location}</span><span>🏢 {c.industry}</span>
                           {c.totalLeads>0 && <span style={{ color:"#34d399" }}>✓ {c.totalLeads} leads</span>}
                           {c.priorityLeads>0 && <span style={{ color:"#fbbf24" }}>⭐ {c.priorityLeads} priority</span>}
                         </div>
                         {c.status==="running" && (
                           <div style={{ marginTop:10 }}>
                             <div style={{ display:"flex", justifyContent:"space-between", fontSize:11, color:"#6b7280", marginBottom:4 }}>
                               <span>{isPolling?"Running…":"Progress"}</span><span>{c.progress}%</span>
                             </div>
                             <div style={{ height:4, background:"rgba(255,255,255,.08)", borderRadius:2, overflow:"hidden" }}>
                               <motion.div style={{ height:"100%", background:"linear-gradient(90deg,#4f46e5,#7c3aed)", borderRadius:2 }}
                                 animate={{ width:`${c.progress}%` }} transition={{ duration:.4 }}/>
                             </div>
                           </div>
                         )}
                         {c.error && <p style={{ fontSize:11, color:"#f87171", marginTop:6 }}>⚠ {c.error}</p>}
                       </div>
                       <div style={{ display:"flex", gap:6, flexShrink:0 }}>
                         {(c.status==="draft"||c.status==="failed") && (
                           <button onClick={()=>runCampaign(c.id)} style={{ display:"flex", alignItems:"center", gap:5, padding:"6px 12px", background:"rgba(52,211,153,.15)", border:"1px solid rgba(52,211,153,.3)", borderRadius:8, fontSize:12, color:"#34d399", fontWeight:600, cursor:"pointer" }}>
                             <Play style={{width:12,height:12}}/>Run
                           </button>
                         )}
                         <button onClick={()=>deleteCampaign(c.id)} style={{ width:32, height:32, background:"rgba(248,113,113,.1)", border:"1px solid rgba(248,113,113,.2)", borderRadius:8, color:"#f87171", display:"flex", alignItems:"center", justifyContent:"center", cursor:"pointer" }}>
                           <Trash2 style={{width:13,height:13}}/>
                         </button>
                       </div>
                     </div>
                   </motion.div>
                 );
               })}
             </AnimatePresence>
           </div>}
      </div>

      {/* New campaign modal */}
      <AnimatePresence>
        {showNew && (
          <motion.div initial={{opacity:0}} animate={{opacity:1}} exit={{opacity:0}}
            style={{ position:"fixed", inset:0, background:"rgba(0,0,0,.7)", zIndex:300, display:"flex", alignItems:"center", justifyContent:"center" }}
            onClick={()=>setShowNew(false)}>
            <motion.div initial={{scale:.95,opacity:0}} animate={{scale:1,opacity:1}} exit={{scale:.95,opacity:0}}
              style={{ background:"#0d0d1f", border:"1px solid rgba(255,255,255,.1)", borderRadius:20, padding:28, width:520, maxHeight:"90vh", overflowY:"auto" }}
              onClick={e=>e.stopPropagation()}>
              <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", marginBottom:20 }}>
                <h2 style={{ fontSize:16, fontWeight:700, color:"#fff" }}>New Campaign</h2>
                <button onClick={()=>setShowNew(false)} style={{ background:"none", border:"none", color:"#6b7280", cursor:"pointer" }}><X style={{width:18,height:18}}/></button>
              </div>
              <div style={{ display:"flex", flexDirection:"column", gap:14 }}>
                <div>
                  <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>Campaign Name</label>
                  <input value={name} onChange={e=>setName(e.target.value)} placeholder="e.g. Dubai Restaurants Q4"
                    style={{ width:"100%", height:36, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, padding:"0 10px", fontSize:13, color:"#fff", outline:"none" }}/>
                </div>
                <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:12 }}>
                  <div>
                    <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>Country</label>
                    <DD id="country" value={country} options={COUNTRIES} onSelect={setCountry}/>
                  </div>
                  <div>
                    <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>City</label>
                    <DD id="city" value={city} options={GEO[country]??[city]} onSelect={setCity}/>
                  </div>
                </div>
                <div>
                  <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>Business Category</label>
                  <DD id="cat" value={industry} options={CATEGORIES} onSelect={setIndustry}/>
                </div>
                <div>
                  <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>Your Service</label>
                  <input value={service} onChange={e=>setService(e.target.value)} placeholder="e.g. Web Development, SEO, AI Chatbot"
                    style={{ width:"100%", height:36, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, padding:"0 10px", fontSize:13, color:"#fff", outline:"none" }}/>
                </div>
                <div>
                  <label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em", display:"block", marginBottom:6 }}>Max Leads: {maxRes}</label>
                  <input type="range" min={10} max={200} step={10} value={maxRes} onChange={e=>setMaxRes(+e.target.value)} style={{ width:"100%" }}/>
                  <div style={{ display:"flex", justifyContent:"space-between", fontSize:10, color:"#4b5563", marginTop:2 }}><span>10</span><span>200</span></div>
                </div>
                <div style={{ display:"flex", gap:10, paddingTop:6 }}>
                  <button onClick={()=>setShowNew(false)} style={{ flex:1, padding:"10px 0", background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, fontSize:13, color:"#9ca3af", cursor:"pointer" }}>Cancel</button>
                  <button onClick={createCampaign} disabled={creating||!name.trim()}
                    style={{ flex:2, display:"flex", alignItems:"center", justifyContent:"center", gap:8, padding:"10px 0", background:creating||!name.trim()?"#374151":"#4f46e5", border:"none", borderRadius:8, fontSize:13, color:"#fff", fontWeight:600, cursor:creating||!name.trim()?"not-allowed":"pointer" }}>
                    {creating?<div style={{ width:14, height:14, borderRadius:"50%", border:"2px solid #fff", borderTopColor:"transparent", animation:"spin .8s linear infinite" }}/>:<Plus style={{width:14,height:14}}/>}
                    {creating?"Creating…":"Create Campaign"}
                  </button>
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </div>
  );
}
