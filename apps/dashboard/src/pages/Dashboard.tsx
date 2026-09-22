import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Play, Square, RefreshCw, Wifi, WifiOff, ChevronDown, Users, CheckCircle2, AlertTriangle, Search, Plug } from "lucide-react";
import { useAgents, AGENT_CFG, AgentState, CoordinatorState, SessionLead } from "../hooks/useAgents";
import { GEO, CATEGORIES, COUNTRIES } from "../lib/geoData";
import { api } from "../lib/api";
import { useDemo } from "../hooks/useDemo";
import AgentDetailModal from "../components/AgentDetailModal";
import LeadDetailModal from "../components/LeadDetailModal";
import type { FullLead } from "../components/LeadDetailModal";
import CoordinatorDetailModal from "../components/CoordinatorDetailModal";
import ConnectorPanel from "../components/ConnectorPanel";

// ── Canvas constants ──────────────────────────────────────────────────────────
const W = 760, H = 580, CX = W/2, CY = H/2, ORBIT_R = 205, NODE_R = 52, HUB_R = 68;
const AGENT_IDS = ["website_dev","seo_audit","inventory_systems","analytics_dashboards","ai_assistants"];

const POS = (() => {
  const o: Record<string,{x:number;y:number}> = {};
  AGENT_IDS.forEach((id,i) => {
    const a = (2*Math.PI*i)/AGENT_IDS.length - Math.PI/2;
    o[id] = { x: CX + ORBIT_R*Math.cos(a), y: CY + ORBIT_R*Math.sin(a) };
  });
  return o;
})();

const STARS = Array.from({length:180},(_,i)=>({
  id:i, x:Math.random()*W, y:Math.random()*H,
  r:Math.random()*1.3+.3, op:Math.random()*.7+.2, dur:Math.random()*3+2,
}));

interface Particle { id:string; agentId:string; t:number; color:string; }

// ── Searchable Dropdown ───────────────────────────────────────────────────────
function Dropdown({ icon, value, open, onToggle, options, onSelect, minW=130 }: {
  icon:string; value:string; open:boolean; onToggle:()=>void;
  options:string[]; onSelect:(v:string)=>void; minW?:number;
}) {
  const [q, setQ] = useState("");
  const filtered = q ? options.filter(o => o.toLowerCase().includes(q.toLowerCase())) : options;

  return (
    <div style={{ position:"relative" }} onClick={e=>e.stopPropagation()}>
      <button onClick={()=>{ setQ(""); onToggle(); }} style={{
        display:"flex", alignItems:"center", gap:6, height:32, padding:"0 10px", minWidth:minW,
        background:"rgba(255,255,255,.07)", border:"1px solid rgba(255,255,255,.12)",
        borderRadius:8, fontSize:12, color:"#e5e7eb", cursor:"pointer",
      }}>
        {icon}
        <span style={{ flex:1, textAlign:"left", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{value}</span>
        <ChevronDown style={{ width:12, height:12, color:"#6b7280", flexShrink:0 }} />
      </button>
      {open && (
        <div style={{
          position:"absolute", right:0, top:36, zIndex:200,
          background:"#0d0d1f", border:"1px solid rgba(255,255,255,.12)",
          borderRadius:12, boxShadow:"0 20px 40px rgba(0,0,0,.7)",
          width:Math.max(minW, 200),
        }}>
          {/* Search input */}
          <div style={{ padding:"8px 10px", borderBottom:"1px solid rgba(255,255,255,.08)", display:"flex", alignItems:"center", gap:6 }}>
            <Search style={{ width:12, height:12, color:"#6b7280", flexShrink:0 }} />
            <input
              value={q} onChange={e=>setQ(e.target.value)}
              placeholder="Search…" autoFocus
              style={{ flex:1, background:"transparent", border:"none", outline:"none", fontSize:12, color:"#e5e7eb" }}
              onClick={e=>e.stopPropagation()}
            />
          </div>
          <div style={{ maxHeight:200, overflowY:"auto" }}>
            {filtered.length === 0 && <p style={{ padding:"10px 14px", fontSize:11, color:"#4b5563" }}>No results</p>}
            {filtered.map(opt=>(
              <button key={opt} onClick={()=>{ onSelect(opt); setQ(""); }} style={{
                display:"block", width:"100%", textAlign:"left", padding:"7px 14px",
                fontSize:12, color:"#d1d5db", background:"transparent", border:"none", cursor:"pointer",
              }}
                onMouseEnter={e=>((e.target as HTMLElement).style.background="rgba(255,255,255,.08)")}
                onMouseLeave={e=>((e.target as HTMLElement).style.background="transparent")}
              >{opt}</button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatChip({ icon, label, value, color }: { icon:React.ReactNode; label:string; value:number; color:string }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:6 }}>
      <span style={{ color }}>{icon}</span>
      <span style={{ color:"#4b5563" }}>{label}:</span>
      <span style={{ fontWeight:700, color }}>{value.toLocaleString()}</span>
    </div>
  );
}

// ── Agent Node ────────────────────────────────────────────────────────────────
function AgentNode({ id,x,y,r,agent,status,onClick }: {
  id:string; x:number; y:number; r:number; agent:AgentState|null; status:string; onClick:()=>void;
}) {
  const cfg  = AGENT_CFG[id];
  const run  = status==="running", err=status==="error", idle=!run&&!err;
  return (
    <g onClick={onClick} style={{ cursor:"pointer" }}
      filter={run ? `drop-shadow(0 0 16px ${cfg.color})` : err ? "drop-shadow(0 0 10px #ef4444)" : undefined}>
      {run && <motion.circle cx={x} cy={y} r={r+8} fill="none" stroke={cfg.color} strokeWidth={1.5}
        animate={{r:[r+6,r+26],opacity:[.5,0]}} transition={{duration:2.2,repeat:Infinity,ease:"easeOut"}}/>}
      {err && <motion.circle cx={x} cy={y} r={r+6} fill="none" stroke="#ef4444" strokeWidth={2}
        animate={{opacity:[.8,.2,.8]}} transition={{duration:1,repeat:Infinity}}/>}
      <circle cx={x} cy={y} r={r-1} fill={cfg.bg} opacity={run?.85:.55}/>
      <circle cx={x} cy={y} r={r*.58} fill={cfg.bg2} opacity={run?.65:.40}/>
      {run && <>
        <motion.ellipse cx={x} cy={y} rx={r*.82} ry={r*.26} fill="none" stroke={cfg.color} strokeWidth={1} opacity={.28}
          animate={{rotate:[0,360]}} transition={{duration:7,repeat:Infinity,ease:"linear"}} style={{transformOrigin:`${x}px ${y}px`}}/>
        <motion.ellipse cx={x} cy={y} rx={r*.82} ry={r*.26} fill="none" stroke={cfg.color} strokeWidth={.7} opacity={.18}
          animate={{rotate:[60,420]}} transition={{duration:7,repeat:Infinity,ease:"linear"}} style={{transformOrigin:`${x}px ${y}px`}}/>
      </>}
      <motion.circle cx={x} cy={y} r={r} fill="none"
        stroke={err?"#ef4444":run?cfg.color:"rgba(148,163,184,.4)"}
        strokeWidth={run||err?2:1.5}
        animate={{opacity:run?[.75,1,.75]:1}} transition={{duration:2,repeat:Infinity}}/>
      <text x={x} y={y-5} textAnchor="middle" dominantBaseline="middle" fontSize={run?23:20}>{cfg.emoji}</text>
      <text x={x} y={y+16} textAnchor="middle" fontSize={8.5} fontWeight={700} letterSpacing={1.4}
        fill={idle?"rgba(148,163,184,.75)":cfg.color} style={{fontFamily:"system-ui"}}>{cfg.label}</text>
      <text x={x} y={y+27} textAnchor="middle" fontSize={7}
        fill={idle?"rgba(100,116,139,.65)":"rgba(148,163,184,.8)"} style={{fontFamily:"system-ui"}}>{cfg.sub}</text>
      <circle cx={x+r-10} cy={y-r+10} r={6.5} fill={err?"#ef4444":run?"#34d399":"rgba(71,85,105,.7)"}/>
      {run && <motion.circle cx={x+r-10} cy={y-r+10} r={6.5} fill="#34d399"
        animate={{opacity:[.7,0],r:[6.5,16]}} transition={{duration:1.6,repeat:Infinity,ease:"easeOut"}}/>}
      {(agent?.leads_found??0)>0 && <g>
        <circle cx={x-r+11} cy={y-r+11} r={12} fill={cfg.color} opacity={.92}/>
        <text x={x-r+11} y={y-r+11} textAnchor="middle" dominantBaseline="middle" fontSize={8.5} fontWeight={700} fill="#fff">
          {(agent?.leads_found??0)>99?"99+":agent!.leads_found}
        </text>
      </g>}
    </g>
  );
}

// ── Coordinator Hub ───────────────────────────────────────────────────────────
function HubNode({ cx,cy,r,coordinator,receiving,onClick }: {
  cx:number; cy:number; r:number; coordinator:CoordinatorState|null; receiving:boolean; onClick:()=>void;
}) {
  const active=(coordinator?.total_received??0)>0;
  return (
    <g onClick={onClick} style={{cursor:"pointer"}}
      filter={receiving?"drop-shadow(0 0 22px #fbbf24)":active?"drop-shadow(0 0 10px rgba(251,191,36,.4))":undefined}>
      {receiving && <>
        <motion.circle cx={cx} cy={cy} r={r+10} fill="none" stroke="#fbbf24" strokeWidth={1}
          animate={{r:[r+8,r+45],opacity:[.5,0]}} transition={{duration:2,repeat:Infinity,ease:"easeOut"}}/>
        <motion.circle cx={cx} cy={cy} r={r+10} fill="none" stroke="#f97316" strokeWidth={.8}
          animate={{r:[r+8,r+32],opacity:[.4,0]}} transition={{duration:2,repeat:Infinity,ease:"easeOut",delay:.7}}/>
      </>}
      <motion.circle cx={cx} cy={cy} r={r+16} fill="none" stroke="#fbbf24" strokeWidth={.6} strokeDasharray="4 8" opacity={.25}
        animate={{rotate:[0,-360]}} transition={{duration:22,repeat:Infinity,ease:"linear"}} style={{transformOrigin:`${cx}px ${cy}px`}}/>
      <circle cx={cx} cy={cy} r={r-1} fill="#1a1000" opacity={.92}/>
      <circle cx={cx} cy={cy} r={r*.62} fill="#2d1800" opacity={.85}/>
      <motion.ellipse cx={cx} cy={cy} rx={r*.88} ry={r*.28} fill="none" stroke="#fbbf24" strokeWidth={1.2}
        opacity={active||receiving?.35:.15} animate={{rotate:[0,360]}} transition={{duration:10,repeat:Infinity,ease:"linear"}} style={{transformOrigin:`${cx}px ${cy}px`}}/>
      {receiving
        ? <motion.circle cx={cx} cy={cy} r={r} fill="none" stroke="#fbbf24" strokeWidth={2.5} strokeDasharray="28 8"
            animate={{rotate:[0,360]}} transition={{duration:3,repeat:Infinity,ease:"linear"}} style={{transformOrigin:`${cx}px ${cy}px`}}/>
        : <circle cx={cx} cy={cy} r={r} fill="none" stroke={active?"#fbbf24":"rgba(71,85,105,.5)"}
            strokeWidth={active?2:1.5} opacity={active?.75:.5}/>
      }
      <text x={cx} y={cy-10} textAnchor="middle" dominantBaseline="middle" fontSize={30}>⚡</text>
      <text x={cx} y={cy+16} textAnchor="middle" fontSize={10} fontWeight={800} fill="#fbbf24" letterSpacing={2.5} style={{fontFamily:"system-ui"}}>NEXUS</text>
      <text x={cx} y={cy+28} textAnchor="middle" fontSize={7.5} fill="rgba(120,113,108,.9)" style={{fontFamily:"system-ui"}}>Coordinator Hub</text>
      {(coordinator?.total_verified??0)>0 && <text x={cx} y={cy+42} textAnchor="middle" fontSize={9} fontWeight={700} fill="#34d399">{coordinator!.total_verified} verified</text>}
      <motion.circle cx={cx+r-12} cy={cy-r+12} r={8}
        fill={receiving?"#fbbf24":active?"#34d399":"rgba(71,85,105,.6)"}
        animate={{opacity:receiving?[.8,1,.8]:1}} transition={{duration:.8,repeat:Infinity}}/>
    </g>
  );
}

// ── Lead Card ─────────────────────────────────────────────────────────────────
function LeadCard({ lead, onClick }: { lead:SessionLead; onClick:()=>void }) {
  const cfg = AGENT_CFG[lead.from_agent];
  return (
    <motion.div initial={{opacity:0,y:-8}} animate={{opacity:1,y:0}} exit={{opacity:0}} transition={{duration:.22}}
      onClick={onClick}
      style={{ borderRadius:10, padding:"8px 12px", marginBottom:6, background:"rgba(255,255,255,.04)", border:"1px solid rgba(255,255,255,.06)", cursor:"pointer" }}
      onMouseEnter={e=>(e.currentTarget.style.background="rgba(255,255,255,.07)")}
      onMouseLeave={e=>(e.currentTarget.style.background="rgba(255,255,255,.04)")}>
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", gap:4, marginBottom:2 }}>
        <span style={{ fontSize:11, color:"#fff", fontWeight:500, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{lead.business_name}</span>
        {lead.score>0 && <span style={{ flexShrink:0, padding:"1px 6px", borderRadius:4, fontSize:9, fontWeight:700, color:"#fff", background:lead.score>=75?"#059669":lead.score>=50?"#d97706":"#475569" }}>{lead.score}</span>}
      </div>
      <span style={{ fontSize:10, color:cfg?.color??"#818cf8" }}>{cfg?.label??lead.from_agent}</span>    </motion.div>
  );
}

// ── Main Dashboard ────────────────────────────────────────────────────────────
export default function DashboardPage() {
  const net  = useAgents();
  const demo = useDemo();
  const [country,  setCountry]  = useState("United States");
  const [city,     setCity]     = useState("New York");
  const [category, setCategory] = useState("Restaurant");
  const [openDd,   setOpenDd]   = useState<"country"|"city"|"cat"|null>(null);
  const [selectedAgent, setSelectedAgent] = useState<AgentState|null>(null);
  const [selectedLead, setSelectedLead] = useState<FullLead|null>(null);
  const [selectedCoordinator, setSelectedCoordinator] = useState<CoordinatorState|null>(null);
  const [showConnectors, setShowConnectors] = useState(false);
  const [particles, setParticles] = useState<Particle[]>([]);
  const [evLog, setEvLog] = useState<{text:string;color:string;ts:string}[]>([]);
  const pRef   = useRef<Particle[]>([]);
  const rafRef = useRef<number|null>(null);
  const lastCnt = useRef<Record<string,number>>({});

  useEffect(() => { setCity(GEO[country]?.[0] ?? ""); }, [country]);

  useEffect(() => {
    net.agents.forEach(a => {
      const prev = lastCnt.current[a.id]??0;
      if (a.leads_found>prev) {
        for (let i=0;i<a.leads_found-prev;i++) {
          const cfg = AGENT_CFG[a.id];
          pRef.current = [...pRef.current, { id:`${a.id}-${Date.now()}-${Math.random()}`, agentId:a.id, t:0, color:cfg?.color??"#fff" }];
        }
        lastCnt.current[a.id] = a.leads_found;
      }
    });
  }, [net.agents]);

  useEffect(() => {
    const ev = net.events[0]; if (!ev) return;
    if (ev.event_type==="lead_found"||ev.event_type==="verified") {
      const cfg = AGENT_CFG[ev.agent_id];
      setEvLog(p=>[{ text:`${ev.event_type==="verified"?"✓":"→"} ${(ev.payload.business_name as string)||"—"}`, color:cfg?.color??"#818cf8", ts:ev.timestamp }, ...p].slice(0,14));
    }
  }, [net.events]);

  useEffect(() => {
    const SPEED=.017;
    const tick=()=>{ pRef.current=pRef.current.map(p=>({...p,t:p.t+SPEED})).filter(p=>p.t<1); setParticles([...pRef.current]); rafRef.current=requestAnimationFrame(tick); };
    rafRef.current=requestAnimationFrame(tick);
    return ()=>{ if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, []);

  function pPos(p:Particle) {
    const from=POS[p.agentId]; if(!from) return {x:CX,y:CY};
    const t=p.t, cpx=(from.x+CX)/2+(CY-from.y)*.12, cpy=(from.y+CY)/2+(from.x-CX)*.12;
    return { x:(1-t)**2*from.x+2*(1-t)*t*cpx+t*t*CX, y:(1-t)**2*from.y+2*(1-t)*t*cpy+t*t*CY };
  }

  const anyRunning = net.agents.some(a=>a.status==="running");
  const totalFound = net.agents.reduce((s,a)=>s+a.leads_found,0);

  return (
    <div style={{ display:"flex", flexDirection:"column", height:"100%", background:"#05050f", color:"#fff", overflow:"hidden" }}
      onClick={()=>setOpenDd(null)}>

      {/* Top bar */}
      <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", flexWrap:"wrap", gap:8, padding:"8px 20px", borderBottom:"1px solid rgba(255,255,255,.06)", background:"#08081a", flexShrink:0 }}
        onClick={e=>e.stopPropagation()}>
        <div style={{ display:"flex", alignItems:"center", gap:10 }}>
          <span style={{ fontWeight:700, fontSize:13, letterSpacing:"0.12em", textTransform:"uppercase" }}>AI Agent Network</span>
          <span style={{ fontSize:9, fontWeight:700, background:"rgba(99,102,241,.2)", color:"#a5b4fc", border:"1px solid rgba(99,102,241,.3)", borderRadius:6, padding:"2px 6px" }}>LIVE</span>
          {net.connected
            ? <span style={{ display:"flex", alignItems:"center", gap:4, fontSize:10, color:"#34d399" }}><Wifi style={{width:12,height:12}}/>Connected</span>
            : <span style={{ display:"flex", alignItems:"center", gap:4, fontSize:10, color:"#4b5563" }}><WifiOff style={{width:12,height:12}}/>Offline</span>}
        </div>

        <div style={{ display:"flex", alignItems:"center", gap:8, flexWrap:"wrap" }}>
          <Dropdown icon="🌍" value={country} open={openDd==="country"} onToggle={()=>setOpenDd(p=>p==="country"?null:"country")} options={COUNTRIES} onSelect={v=>{setCountry(v);setOpenDd(null);}} minW={160}/>
          <Dropdown icon="📍" value={city}    open={openDd==="city"}    onToggle={()=>setOpenDd(p=>p==="city"?null:"city")}       options={GEO[country]??[]} onSelect={v=>{setCity(v);setOpenDd(null);}} minW={140}/>
          <Dropdown icon="🏢" value={category} open={openDd==="cat"}   onToggle={()=>setOpenDd(p=>p==="cat"?null:"cat")}         options={CATEGORIES} onSelect={v=>{setCategory(v);setOpenDd(null);}} minW={160}/>

          <button 
            onClick={()=>setShowConnectors(true)}
            style={{ 
              display:"flex", alignItems:"center", gap:6, height:32, padding:"0 14px", 
              background:"rgba(52,211,153,.15)", border:"1px solid rgba(52,211,153,.3)", 
              borderRadius:8, color:"#34d399", fontSize:12, fontWeight:600, cursor:"pointer" 
            }}
          >
            <Plug style={{width:12,height:12}}/>Connectors
          </button>

          {!anyRunning
            ? <button onClick={()=>net.startAll(`${city}, ${country}`,150,category)} style={{ display:"flex", alignItems:"center", gap:6, height:32, padding:"0 14px", background:"#059669", border:"none", borderRadius:8, color:"#fff", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                <Play style={{width:12,height:12}}/>Start All Agents
              </button>
            : <button onClick={()=>net.stopAll()} style={{ display:"flex", alignItems:"center", gap:6, height:32, padding:"0 14px", background:"transparent", border:"1px solid rgba(239,68,68,.4)", borderRadius:8, color:"#f87171", fontSize:12, fontWeight:600, cursor:"pointer" }}>
                <Square style={{width:12,height:12}}/>Stop All
              </button>
          }
          <button onClick={()=>net.refresh()} style={{ width:32, height:32, background:"rgba(255,255,255,.06)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, color:"#6b7280", display:"flex", alignItems:"center", justifyContent:"center", cursor:"pointer" }}>
            <RefreshCw style={{width:14,height:14}}/>
          </button>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex:1, display:"flex", overflow:"hidden", minHeight:0 }}>
        {/* Galaxy SVG */}
        <div style={{ flex:1, display:"flex", flexDirection:"column", alignItems:"center", justifyContent:"center", position:"relative", overflow:"hidden" }}>
          {net.loading
            ? <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:14, color:"#4b5563" }}>
                <div style={{ width:40, height:40, borderRadius:"50%", border:"2px solid #6366f1", borderTopColor:"transparent", animation:"spin .8s linear infinite" }}/>
                <span style={{ fontSize:12, letterSpacing:"0.15em", textTransform:"uppercase" }}>Connecting to agents…</span>
                <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
              </div>
            : <svg viewBox={`0 0 ${W} ${H}`} style={{ width:"100%", maxHeight:"calc(100% - 44px)" }} preserveAspectRatio="xMidYMid meet">
                <defs>
                  <radialGradient id="bg" cx="50%" cy="50%" r="70%">
                    <stop offset="0%" stopColor="#0d0d2b"/><stop offset="60%" stopColor="#070714"/><stop offset="100%" stopColor="#03030a"/>
                  </radialGradient>
                  {AGENT_IDS.map(id=>{const c=AGENT_CFG[id]; return(
                    <filter key={`gf-${id}`} id={`gf-${id}`} x="-80%" y="-80%" width="260%" height="260%">
                      <feGaussianBlur stdDeviation="10" result="b"/>
                      <feFlood floodColor={c.color} floodOpacity=".6" result="fc"/>
                      <feComposite in="fc" in2="b" operator="in" result="cb"/>
                      <feMerge><feMergeNode in="cb"/><feMergeNode in="SourceGraphic"/></feMerge>
                    </filter>
                  );})}
                  <filter id="gf-hub" x="-80%" y="-80%" width="260%" height="260%">
                    <feGaussianBlur stdDeviation="14" result="b"/><feFlood floodColor="#fbbf24" floodOpacity=".6" result="fc"/>
                    <feComposite in="fc" in2="b" operator="in" result="cb"/>
                    <feMerge><feMergeNode in="cb"/><feMergeNode in="SourceGraphic"/></feMerge>
                  </filter>
                  <filter id="gfp" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="3"/></filter>
                </defs>
                <rect width={W} height={H} fill="url(#bg)"/>
                {STARS.map(s=>(
                  <motion.circle key={s.id} cx={s.x} cy={s.y} r={s.r} fill="#fff"
                    animate={{opacity:[s.op,s.op*.15,s.op]}} transition={{duration:s.dur,repeat:Infinity,ease:"easeInOut"}}/>
                ))}
                <circle cx={CX} cy={CY} r={ORBIT_R+88} fill="none" stroke="#fbbf24" strokeWidth={1.2} opacity={.15}/>
                <circle cx={CX} cy={CY} r={ORBIT_R} fill="none" stroke="#fbbf24" strokeWidth={.8} strokeDasharray="6 10" opacity={.25}/>
                {AGENT_IDS.map(id=>{
                  const pos=POS[id]; const a=net.agents.find(x=>x.id===id); const cfg=AGENT_CFG[id];
                  const run=a?.status==="running", err=a?.status==="error";
                  return (<g key={`ln-${id}`}>
                    <line x1={pos.x} y1={pos.y} x2={CX} y2={CY} stroke={err?"#ef4444":run?cfg.color:"rgba(148,163,184,.2)"} strokeWidth={run?1.5:.8} strokeDasharray={run?"none":"5 8"} opacity={run?.4:.3}/>
                    {run&&<motion.line x1={pos.x} y1={pos.y} x2={CX} y2={CY} stroke={cfg.color} strokeWidth={2} strokeDasharray="10 24" opacity={.55} animate={{strokeDashoffset:[0,-34]}} transition={{duration:1.4,repeat:Infinity,ease:"linear"}}/>}
                  </g>);
                })}
                {particles.map(p=>{const pos=pPos(p);const fade=p.t<.12?p.t/.12:p.t>.82?(1-p.t)/.18:1;return(
                  <g key={p.id} opacity={fade}>
                    <circle cx={pos.x} cy={pos.y} r={9}   fill={p.color} opacity={.15} filter="url(#gfp)"/>
                    <circle cx={pos.x} cy={pos.y} r={4}   fill={p.color} opacity={.9}/>
                    <circle cx={pos.x} cy={pos.y} r={1.8} fill="#fff"    opacity={.95}/>
                  </g>
                );})}
                {AGENT_IDS.map(id=>{
                  const pos=POS[id]; const a=net.agents.find(x=>x.id===id);
                  return <AgentNode key={id} id={id} x={pos.x} y={pos.y} r={NODE_R} agent={a??null} status={a?.status??"idle"} onClick={()=>a&&setSelectedAgent(a)}/>;
                })}
                <HubNode cx={CX} cy={CY} r={HUB_R} coordinator={net.coordinator} receiving={particles.length>0} onClick={()=>net.coordinator&&setSelectedCoordinator(net.coordinator)}/>
              </svg>
          }
          {/* Stats bar */}
          <div style={{ position:"absolute", bottom:0, left:0, right:0, display:"flex", alignItems:"center", justifyContent:"center", gap:32, padding:"10px 0", borderTop:"1px solid rgba(255,255,255,.05)", background:"rgba(0,0,0,.45)", fontSize:11, backdropFilter:"blur(4px)" }}>
            <StatChip icon={<Users style={{width:12,height:12}}/>} label="Found"      value={totalFound}                             color="#818cf8"/>
            <StatChip icon={<CheckCircle2 style={{width:12,height:12}}/>} label="Verified"  value={net.coordinator?.total_verified??0}  color="#34d399"/>
            <StatChip icon={<AlertTriangle style={{width:12,height:12}}/>} label="Duplicates" value={net.coordinator?.total_duplicates??0} color="#fbbf24"/>
            <StatChip icon={<div style={{width:8,height:8,borderRadius:"50%",background:"#34d399"}}/>} label="Running" value={net.agents.filter(a=>a.status==="running").length} color="#34d399"/>
          </div>
        </div>

        {/* Right panel */}
        <div style={{ width:268, flexShrink:0, borderLeft:"1px solid rgba(255,255,255,.06)", background:"#07071a", display:"flex", flexDirection:"column", overflow:"hidden" }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, padding:"12px 16px", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
            <div style={{ width:6, height:6, borderRadius:"50%", background:"#34d399", animation:"pulse 2s ease infinite" }}/>
            <span style={{ fontSize:10, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.12em" }}>Live Events</span>
          </div>
          <div style={{ flex:1, overflowY:"auto", padding:"8px 12px" }}>
            <AnimatePresence mode="popLayout" initial={false}>
              {evLog.map((ev,i)=>(
                <motion.div key={`${ev.ts}-${i}`} initial={{opacity:0,x:14}} animate={{opacity:1,x:0}} exit={{opacity:0}} transition={{duration:.2}}
                  style={{ display:"flex", alignItems:"center", gap:8, padding:"6px 10px", marginBottom:4, borderRadius:8, background:"rgba(255,255,255,.03)" }}>
                  <div style={{ width:6, height:6, borderRadius:"50%", flexShrink:0, background:ev.color }}/>
                  <span style={{ fontSize:11, color:"#d1d5db", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{ev.text}</span>
                </motion.div>
              ))}
            </AnimatePresence>
            {evLog.length===0 && <p style={{ fontSize:11, color:"#374151", textAlign:"center", paddingTop:40 }}>Start agents to see live events…</p>}
          </div>
          <div style={{ borderTop:"1px solid rgba(255,255,255,.06)" }}>
            <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"10px 16px" }}>
              <span style={{ fontSize:10, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.12em" }}>Verified Leads</span>
              <span style={{ fontSize:11, color:"#34d399", fontWeight:700 }}>{net.leads.length}</span>
            </div>
            <div style={{ maxHeight:200, overflowY:"auto", padding:"0 12px 12px" }}>
              <AnimatePresence mode="popLayout" initial={false}>
                {net.leads.slice(0,18).map((lead,i)=><LeadCard key={`${lead.timestamp}-${i}`} lead={lead} onClick={async()=>{
                try { const full = await api.get<FullLead>(`/leads?q=${encodeURIComponent(lead.business_name)}&limit=1`).then((r:any)=>r.data?.[0] ?? null); if(full) setSelectedLead(full); } catch{/*ignore*/}
              }}/>)}
              </AnimatePresence>
              {net.leads.length===0 && <p style={{ fontSize:11, color:"#374151", textAlign:"center", paddingTop:16 }}>No leads yet…</p>}
            </div>
          </div>
        </div>
      </div>
      <AgentDetailModal agent={selectedAgent} onClose={()=>setSelectedAgent(null)} color={selectedAgent?AGENT_CFG[selectedAgent.id]?.color??"#6b7280":"#6b7280"} />
      <LeadDetailModal lead={selectedLead as any} onClose={()=>setSelectedLead(null)} />
      <CoordinatorDetailModal coordinator={selectedCoordinator as any} onClose={()=>setSelectedCoordinator(null)} />
      {showConnectors && <ConnectorPanel onClose={()=>setShowConnectors(false)} onConnectorChange={()=>net.refresh()} />}
      <style>{`@keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}`}</style>

      {/* Demo upgrade floating bar on dashboard */}
      {demo.demo_mode && (
        <div style={{
          position: "fixed", bottom: 24, left: "50%", transform: "translateX(-50%)",
          zIndex: 800, display: "flex", alignItems: "center", gap: 12,
          padding: "14px 22px", borderRadius: 16,
          background: "linear-gradient(135deg, #7c3aed, #4f46e5)",
          boxShadow: "0 8px 32px rgba(124,58,237,.6)",
          maxWidth: 520, width: "calc(100% - 48px)",
        }}>
          <span style={{ fontSize: 22, flexShrink: 0 }}>🔒</span>
          <div style={{ flex: 1, minWidth: 0 }}>
            <p style={{ fontSize: 13, fontWeight: 700, color: "#fff", margin: 0 }}>Demo Mode — Leads are real, contact details are hidden</p>
            <p style={{ fontSize: 11, color: "rgba(255,255,255,.7)", margin: "2px 0 0" }}>Buy the full system to see phone numbers, emails &amp; social media</p>
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
