import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Bot, Mail, MessageCircle, Globe, Key, Eye, EyeOff, Save, CheckCircle2, Loader2, Plug } from "lucide-react";
import { api } from "../lib/api";

type Tab = "ai"|"gmail"|"whatsapp"|"workspace"|"apikeys"|"connectors";

export default function SettingsPage() {
  const [tab, setTab] = useState<Tab>("ai");
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState<string|null>(null);
  const [loading, setLoading] = useState(true);
  // AI
  const [aiKey, setAiKey] = useState(""); const [aiModel, setAiModel] = useState("gpt-4o-mini"); const [aiBase, setAiBase] = useState(""); const [showAi, setShowAi] = useState(false);
  // Gmail
  const [gmailUser, setGmailUser] = useState(""); const [gmailPass, setGmailPass] = useState(""); const [showGmail, setShowGmail] = useState(false); const [testResult, setTestResult] = useState<{ok:boolean;msg:string}|null>(null); const [testing, setTesting] = useState(false);
  // WhatsApp
  const [waToken, setWaToken] = useState(""); const [waPhone, setWaPhone] = useState(""); const [showWa, setShowWa] = useState(false);
  // Workspace
  const [wsName, setWsName] = useState("My Workspace"); const [wsSlug, setWsSlug] = useState("");
  // API Keys
  const [apiKeys, setApiKeys] = useState<{id:string;name:string;createdAt:string}[]>([]);
  const [newKeyName, setNewKeyName] = useState(""); const [newKey, setNewKey] = useState<string|null>(null); const [creatingKey, setCreatingKey] = useState(false);
  // Connectors
  const [connectors, setConnectors] = useState<{name:string;display_name:string;requires_api_key:boolean;is_enabled:boolean;is_configured:boolean}[]>([]);
  const [connectorKeys, setConnectorKeys] = useState<Record<string,string>>({});
  const [showConnectorKey, setShowConnectorKey] = useState<Record<string,boolean>>({});
  const [updatingConnector, setUpdatingConnector] = useState<string|null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [ints, ws, keys, conns] = await Promise.all([
        api.get<any[]>("/settings/integrations").catch(()=>[]),
        api.get<any>("/workspace").catch(()=>null),
        api.get<any[]>("/settings/api-keys").catch(()=>[]),
        api.get<any[]>("/connectors").catch(()=>[]),
      ]);
      const openai = ints.find((i:any)=>i.type==="openai"); if (openai) { setAiKey(openai.config.apiKey??""); setAiModel(openai.config.model??"gpt-4o-mini"); setAiBase(openai.config.baseURL??""); }
      const gmail  = ints.find((i:any)=>i.type==="gmail");  if (gmail)  { setGmailUser(gmail.config.user??""); setGmailPass(gmail.config.appPassword??""); }
      const wa     = ints.find((i:any)=>i.type==="whatsapp"); if (wa)   { setWaToken(wa.config.token??""); setWaPhone(wa.config.phoneId??""); }
      if (ws) { setWsName(ws.name??""); setWsSlug(ws.slug??""); }
      setApiKeys(keys??[]);
      setConnectors(conns??[]);
    } catch {} finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function saveInt(type:string, name:string, config:Record<string,string>) {
    setSaving(true);
    try { await api.post("/settings/integrations", { type, name, config }); setSaved(type); setTimeout(()=>setSaved(null),2500); await load(); }
    catch {} finally { setSaving(false); }
  }

  async function testGmail() {
    setTesting(true); setTestResult(null);
    try { const r = await api.get<any>("/email/stats"); setTestResult({ ok:true, msg:`✅ Gmail connected · ${r.remaining} emails remaining today` }); }
    catch { setTestResult({ ok:false, msg:"❌ Gmail not configured or connection failed. Save credentials first." }); }
    finally { setTesting(false); }
  }

  async function createKey() {
    if (!newKeyName.trim()) return;
    setCreatingKey(true);
    try { const r = await api.post<any>("/settings/api-keys",{name:newKeyName}); setNewKey(r.key??null); setNewKeyName(""); await load(); }
    catch {} finally { setCreatingKey(false); }
  }

  async function toggleConnector(name:string, enabled:boolean) {
    setUpdatingConnector(name);
    try {
      await api.put(`/connectors/${name}/config`, {
        enabled,
        api_key: connectorKeys[name] || null,
      });
      await load();
    } catch {} finally { setUpdatingConnector(null); }
  }

  async function saveConnectorKey(name:string) {
    setUpdatingConnector(name);
    try {
      await api.put(`/connectors/${name}/config`, {
        enabled: connectors.find(c=>c.name===name)?.is_enabled ?? false,
        api_key: connectorKeys[name] || null,
      });
      await load();
    } catch {} finally { setUpdatingConnector(null); }
  }

  const TABS: {id:Tab;label:string;icon:React.ReactNode}[] = [
    {id:"ai",       label:"AI Config",    icon:<Bot style={{width:14,height:14}}/>},
    {id:"gmail",    label:"Gmail",        icon:<Mail style={{width:14,height:14}}/>},
    {id:"whatsapp", label:"WhatsApp",     icon:<MessageCircle style={{width:14,height:14}}/>},
    {id:"connectors",label:"Connectors",  icon:<Plug style={{width:14,height:14}}/>},
    {id:"workspace",label:"Workspace",    icon:<Globe style={{width:14,height:14}}/>},
    {id:"apikeys",  label:"API Keys",     icon:<Key style={{width:14,height:14}}/>},
  ];

  return (
    <div style={{ flex:1, overflowY:"auto", background:"#05050f", padding:"28px 32px" }}>
      <div style={{ maxWidth:680 }}>
        <h1 style={{ fontSize:22, fontWeight:700, color:"#fff", letterSpacing:"-.01em", marginBottom:4 }}>Settings</h1>
        <p style={{ fontSize:13, color:"#6b7280", marginBottom:24 }}>Configure AI providers, email, WhatsApp, and integrations</p>

        {/* Tab bar */}
        <div style={{ display:"flex", gap:4, padding:4, background:"rgba(255,255,255,.03)", border:"1px solid rgba(255,255,255,.07)", borderRadius:14, marginBottom:24 }}>
          {TABS.map(t=>(
            <button key={t.id} onClick={()=>setTab(t.id)} style={{
              flex:1, display:"flex", alignItems:"center", justifyContent:"center", gap:6, padding:"8px 10px", borderRadius:10,
              border:"none", cursor:"pointer", fontSize:12, fontWeight:tab===t.id?600:400,
              background:tab===t.id?"#4f46e5":"transparent", color:tab===t.id?"#fff":"#9ca3af", transition:"all .15s",
            }}>{t.icon} <span style={{ display:"inline" }}>{t.label}</span></button>
          ))}
        </div>

        {loading ? <p style={{ color:"#6b7280", fontSize:13 }}>Loading settings…</p> : <>
          {/* AI */}
          {tab==="ai" && <Card icon={<Bot style={{width:18,height:18,color:"#818cf8"}}/>} title="AI Configuration" desc="Connect an AI provider. Leave blank to use free built-in templates.">
            <Field label="API Key">
              <Row>
                <input type={showAi?"text":"password"} value={aiKey} onChange={e=>setAiKey(e.target.value)} placeholder="sk-… (OpenAI / OpenRouter / Groq / Grok)"
                  style={{ flex:1, height:36, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, padding:"0 10px", fontSize:13, color:"#fff", outline:"none" }}/>
                <Btn onClick={()=>setShowAi(s=>!s)}>{showAi?<EyeOff style={{width:14,height:14}}/>:<Eye style={{width:14,height:14}}/>}</Btn>
              </Row>
              <p style={{ fontSize:11, color:"#4b5563", marginTop:4 }}>Leave empty to use free built-in templates — no key needed</p>
            </Field>
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
              <Field label="Model"><input value={aiModel} onChange={e=>setAiModel(e.target.value)} placeholder="gpt-4o-mini" style={iStyle}/></Field>
              <Field label="Base URL (optional)"><input value={aiBase} onChange={e=>setAiBase(e.target.value)} placeholder="https://openrouter.ai/api/v1" style={iStyle}/></Field>
            </div>
            <div style={{ padding:12, background:"rgba(255,255,255,.02)", border:"1px solid rgba(255,255,255,.06)", borderRadius:10, fontSize:12, color:"#6b7280" }}>
              <p style={{ fontWeight:600, color:"#9ca3af", marginBottom:6 }}>Compatible providers:</p>
              {[["OpenAI","leave Base URL empty"],["OpenRouter","https://openrouter.ai/api/v1"],["Groq (fast)","https://api.groq.com/openai/v1"],["Ollama (local)","http://localhost:11434/v1"],["Grok (xAI)","https://api.x.ai/v1"]].map(([p,u])=>(
                <p key={p} style={{ marginBottom:3 }}>• <span style={{ color:"#d1d5db" }}>{p}:</span> {u}</p>
              ))}
            </div>
            <SaveBtn label="Save AI Config" type="openai" saved={saved==="openai"} saving={saving} onClick={()=>saveInt("openai","OpenAI / Compatible",{apiKey:aiKey,model:aiModel,baseURL:aiBase})}/>
          </Card>}

          {/* Gmail */}
          {tab==="gmail" && <Card icon={<Mail style={{width:18,height:18,color:"#60a5fa"}}/>} title="Gmail SMTP" desc="Send cold emails via your Gmail account.">
            <div style={{ padding:12, background:"rgba(96,165,250,.06)", border:"1px solid rgba(96,165,250,.2)", borderRadius:10, fontSize:12, color:"#93c5fd", marginBottom:4 }}>
              <p style={{ fontWeight:600, marginBottom:4 }}>How to get Gmail App Password:</p>
              <p>1. Google Account → Security → Enable 2-Step Verification</p>
              <p>2. Search "App passwords" → Create one for "Mail"</p>
              <p>3. Copy the 16-character password below</p>
            </div>
            <Field label="Gmail Address"><input type="email" value={gmailUser} onChange={e=>setGmailUser(e.target.value)} placeholder="yourname@gmail.com" style={iStyle}/></Field>
            <Field label="App Password">
              <Row>
                <input type={showGmail?"text":"password"} value={gmailPass} onChange={e=>setGmailPass(e.target.value)} placeholder="xxxx xxxx xxxx xxxx" style={{...iStyle,flex:1}}/>
                <Btn onClick={()=>setShowGmail(s=>!s)}>{showGmail?<EyeOff style={{width:14,height:14}}/>:<Eye style={{width:14,height:14}}/>}</Btn>
              </Row>
              <p style={{ fontSize:11, color:"#4b5563", marginTop:4 }}>Safe limit: 50 emails/day · 90s delay between sends</p>
            </Field>
            {testResult && <div style={{ padding:10, borderRadius:8, fontSize:12, background:testResult.ok?"rgba(52,211,153,.1)":"rgba(248,113,113,.1)", border:`1px solid ${testResult.ok?"rgba(52,211,153,.2)":"rgba(248,113,113,.2)"}`, color:testResult.ok?"#6ee7b7":"#fca5a5" }}>{testResult.msg}</div>}
            <div style={{ display:"flex", gap:10 }}>
              <SaveBtn label="Save Gmail" type="gmail" saved={saved==="gmail"} saving={saving} onClick={()=>saveInt("gmail","Gmail SMTP",{user:gmailUser,appPassword:gmailPass})}/>
              <Btn onClick={testGmail} disabled={testing}>{testing?"Testing…":"Test Connection"}</Btn>
            </div>
          </Card>}

          {/* WhatsApp */}
          {tab==="whatsapp" && <Card icon={<MessageCircle style={{width:18,height:18,color:"#34d399"}}/>} title="WhatsApp Business API" desc="Connect Meta WhatsApp Business API. Manual wa.me links work without any API key.">
            <div style={{ padding:12, background:"rgba(52,211,153,.06)", border:"1px solid rgba(52,211,153,.2)", borderRadius:10, fontSize:12, color:"#6ee7b7", marginBottom:4 }}>
              <p style={{ fontWeight:600, marginBottom:4 }}>WhatsApp Integration Options:</p>
              <p>• <strong>Manual (works now):</strong> Use wa.me links in the WhatsApp page</p>
              <p>• <strong>Business API (advanced):</strong> Requires Meta Business Account</p>
            </div>
            <Field label="Business API Token">
              <Row>
                <input type={showWa?"text":"password"} value={waToken} onChange={e=>setWaToken(e.target.value)} placeholder="EAAxxxxxxx…" style={{...iStyle,flex:1}}/>
                <Btn onClick={()=>setShowWa(s=>!s)}>{showWa?<EyeOff style={{width:14,height:14}}/>:<Eye style={{width:14,height:14}}/>}</Btn>
              </Row>
            </Field>
            <Field label="Phone Number ID"><input value={waPhone} onChange={e=>setWaPhone(e.target.value)} placeholder="1234567890" style={iStyle}/></Field>
            <SaveBtn label="Save WhatsApp" type="whatsapp" saved={saved==="whatsapp"} saving={saving} onClick={()=>saveInt("whatsapp","WhatsApp Business API",{token:waToken,phoneId:waPhone})}/>
          </Card>}

          {/* Workspace */}
          {tab==="workspace" && <Card icon={<Globe style={{width:18,height:18,color:"#c084fc"}}/>} title="Workspace" desc="Manage your workspace settings.">
            <div style={{ display:"grid", gridTemplateColumns:"1fr 1fr", gap:14 }}>
              <Field label="Name"><input value={wsName} onChange={e=>setWsName(e.target.value)} style={iStyle}/></Field>
              <Field label="Slug"><input value={wsSlug} onChange={e=>setWsSlug(e.target.value)} style={iStyle}/></Field>
            </div>
            <button onClick={async()=>{setSaving(true);try{await api.patch("/workspace",{name:wsName,slug:wsSlug});setSaved("ws");setTimeout(()=>setSaved(null),2500);}catch{}finally{setSaving(false);}}}
              style={{ display:"flex", alignItems:"center", gap:6, padding:"9px 18px", background:"#7c3aed", border:"none", borderRadius:8, fontSize:13, color:"#fff", fontWeight:600, cursor:"pointer" }}>
              {saved==="ws"?<CheckCircle2 style={{width:14,height:14}}/>:<Save style={{width:14,height:14}}/>}
              {saved==="ws"?"Saved!":"Save Workspace"}
            </button>
          </Card>}

          {/* API Keys */}
          {tab==="apikeys" && <Card icon={<Key style={{width:18,height:18,color:"#fbbf24"}}/>} title="API Keys" desc="Generate keys to access the Prospex API from external tools.">
            {newKey && (
              <div style={{ padding:12, background:"rgba(52,211,153,.1)", border:"1px solid rgba(52,211,153,.3)", borderRadius:10, marginBottom:8 }}>
                <p style={{ fontSize:12, fontWeight:600, color:"#6ee7b7", marginBottom:8 }}>✅ Key created — copy it now, it won't be shown again</p>
                <div style={{ display:"flex", gap:8 }}>
                  <input value={newKey} readOnly style={{ flex:1, height:32, background:"rgba(0,0,0,.3)", border:"1px solid rgba(255,255,255,.1)", borderRadius:6, padding:"0 8px", fontSize:11, color:"#fff", fontFamily:"monospace", outline:"none" }}/>
                  <Btn onClick={()=>navigator.clipboard.writeText(newKey!)}>Copy</Btn>
                </div>
                <button onClick={()=>setNewKey(null)} style={{ fontSize:11, color:"#6b7280", background:"none", border:"none", cursor:"pointer", marginTop:6 }}>Dismiss</button>
              </div>
            )}
            <div style={{ display:"flex", gap:8, marginBottom:12 }}>
              <input value={newKeyName} onChange={e=>setNewKeyName(e.target.value)} onKeyDown={e=>e.key==="Enter"&&createKey()} placeholder="Key name (e.g. Production, Zapier)"
                style={{ flex:1, height:36, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, padding:"0 10px", fontSize:13, color:"#fff", outline:"none" }}/>
              <button onClick={createKey} disabled={creatingKey||!newKeyName.trim()}
                style={{ padding:"0 16px", height:36, background:"#b45309", border:"none", borderRadius:8, fontSize:13, color:"#fff", fontWeight:600, cursor:creatingKey||!newKeyName.trim()?"not-allowed":"pointer", opacity:!newKeyName.trim()?.5:1 }}>
                {creatingKey?"…":"Create Key"}
              </button>
            </div>
            {apiKeys.length>0 ? apiKeys.map(k=>(
              <div key={k.id} style={{ display:"flex", alignItems:"center", justifyContent:"space-between", padding:"10px 12px", background:"rgba(255,255,255,.03)", border:"1px solid rgba(255,255,255,.06)", borderRadius:10, marginBottom:6 }}>
                <div><p style={{ fontSize:13, fontWeight:500, color:"#fff" }}>{k.name}</p><p style={{ fontSize:11, color:"#6b7280" }}>Created {new Date(k.createdAt).toLocaleDateString()}</p></div>
                <button onClick={async()=>{await api.delete(`/settings/api-keys/${k.id}`);await load();}} style={{ fontSize:12, color:"#f87171", background:"none", border:"none", cursor:"pointer" }}>Delete</button>
              </div>
            )) : <p style={{ fontSize:13, color:"#4b5563", textAlign:"center", padding:"20px 0" }}>No API keys yet</p>}
          </Card>}

          {/* Connectors */}
          {tab==="connectors" && <Card icon={<Plug style={{width:18,height:18,color:"#34d399"}}/>} title="Data Connectors" desc="Connect multiple lead sources — Google Maps, Yelp, Yellow Pages, Facebook.">
            <div style={{ padding:12, background:"rgba(52,211,153,.06)", border:"1px solid rgba(52,211,153,.2)", borderRadius:10, fontSize:12, color:"#6ee7b7", marginBottom:8 }}>
              <p style={{ fontWeight:600, marginBottom:4 }}>✨ Multi-Source Lead Discovery</p>
              <p>Enable multiple connectors to scrape leads from different platforms simultaneously. All agents will use enabled connectors.</p>
            </div>
            
            {connectors.map(conn=>(
              <div key={conn.name} style={{ padding:16, background:"rgba(255,255,255,.03)", border:"1px solid rgba(255,255,255,.07)", borderRadius:12, display:"flex", flexDirection:"column", gap:12 }}>
                <div style={{ display:"flex", alignItems:"center", justifyContent:"space-between" }}>
                  <div style={{ display:"flex", alignItems:"center", gap:12 }}>
                    <div style={{ width:10, height:10, borderRadius:"50%", background:conn.is_enabled?(conn.is_configured?"#34d399":"#fbbf24"):"#4b5563" }}/>
                    <div>
                      <h3 style={{ fontSize:14, fontWeight:600, color:"#fff", marginBottom:2 }}>{conn.display_name}</h3>
                      <p style={{ fontSize:11, color:"#6b7280" }}>
                        {!conn.is_enabled ? "Disabled" : conn.is_configured ? "✅ Ready" : "⚠️ API key required"}
                      </p>
                    </div>
                  </div>
                  <button
                    onClick={()=>toggleConnector(conn.name,!conn.is_enabled)}
                    disabled={updatingConnector===conn.name}
                    style={{
                      padding:"6px 14px", borderRadius:8, fontSize:12, fontWeight:600, border:"none", cursor:updatingConnector===conn.name?"wait":"pointer",
                      background:conn.is_enabled?"rgba(248,113,113,.2)":"rgba(52,211,153,.2)",
                      color:conn.is_enabled?"#f87171":"#34d399",
                    }}
                  >
                    {updatingConnector===conn.name?"...":conn.is_enabled?"Disable":"Enable"}
                  </button>
                </div>
                
                {conn.requires_api_key && (
                  <div>
                    <Field label={`${conn.display_name} API Key`}>
                      <Row>
                        <input
                          type={showConnectorKey[conn.name]?"text":"password"}
                          value={connectorKeys[conn.name]??""}
                          onChange={e=>setConnectorKeys(prev=>({...prev,[conn.name]:e.target.value}))}
                          placeholder={conn.name==="yelp"?"Yelp Fusion API key":"API key"}
                          style={{...iStyle,flex:1}}
                        />
                        <Btn onClick={()=>setShowConnectorKey(prev=>({...prev,[conn.name]:!prev[conn.name]}))}>
                          {showConnectorKey[conn.name]?<EyeOff style={{width:14,height:14}}/>:<Eye style={{width:14,height:14}}/>}
                        </Btn>
                        <button
                          onClick={()=>saveConnectorKey(conn.name)}
                          disabled={updatingConnector===conn.name}
                          style={{
                            padding:"0 14px", height:36, background:"#4f46e5", border:"none", borderRadius:8,
                            fontSize:12, color:"#fff", fontWeight:600, cursor:updatingConnector===conn.name?"wait":"pointer"
                          }}
                        >
                          {updatingConnector===conn.name?"...":"Save"}
                        </button>
                      </Row>
                      {conn.name==="yelp" && (
                        <p style={{ fontSize:11, color:"#4b5563", marginTop:4 }}>
                          Get API key: <a href="https://www.yelp.com/developers" target="_blank" rel="noopener" style={{ color:"#818cf8" }}>yelp.com/developers</a>
                        </p>
                      )}
                    </Field>
                  </div>
                )}
                
                {conn.name==="google_maps" && (
                  <p style={{ fontSize:11, color:"#6b7280", padding:"8px 10px", background:"rgba(255,255,255,.02)", borderRadius:6 }}>
                    💡 Uses Playwright web scraping — no API key needed
                  </p>
                )}
                {conn.name==="yellowpages" && (
                  <p style={{ fontSize:11, color:"#6b7280", padding:"8px 10px", background:"rgba(255,255,255,.02)", borderRadius:6 }}>
                    🗽 US-focused business directory — no API key needed
                  </p>
                )}
                {conn.name==="facebook" && (
                  <p style={{ fontSize:11, color:"#fbbf24", padding:"8px 10px", background:"rgba(251,191,36,.06)", border:"1px solid rgba(251,191,36,.2)", borderRadius:6 }}>
                    ⚠️ Experimental — Facebook has aggressive anti-scraping. May be unreliable.
                  </p>
                )}
              </div>
            ))}
            
            {connectors.length===0 && <p style={{ fontSize:13, color:"#4b5563", textAlign:"center", padding:"20px 0" }}>Loading connectors…</p>}
          </Card>}
        </>}
      </div>
    </div>
  );
}

const iStyle: React.CSSProperties = { width:"100%", height:36, background:"rgba(255,255,255,.05)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, padding:"0 10px", fontSize:13, color:"#fff", outline:"none" };

function Card({ icon, title, desc, children }: { icon:React.ReactNode; title:string; desc:string; children:React.ReactNode }) {
  return (
    <motion.div initial={{opacity:0,y:8}} animate={{opacity:1,y:0}}
      style={{ background:"rgba(255,255,255,.02)", border:"1px solid rgba(255,255,255,.07)", borderRadius:18, padding:24, display:"flex", flexDirection:"column", gap:16 }}>
      <div style={{ display:"flex", alignItems:"center", gap:12 }}>
        <div style={{ width:36, height:36, background:"rgba(255,255,255,.04)", borderRadius:12, display:"flex", alignItems:"center", justifyContent:"center" }}>{icon}</div>
        <div><h2 style={{ fontSize:14, fontWeight:600, color:"#fff" }}>{title}</h2><p style={{ fontSize:12, color:"#6b7280" }}>{desc}</p></div>
      </div>
      {children}
    </motion.div>
  );
}

function Field({ label, children }: { label:string; children:React.ReactNode }) {
  return <div style={{ display:"flex", flexDirection:"column", gap:6 }}><label style={{ fontSize:11, fontWeight:600, color:"#6b7280", textTransform:"uppercase", letterSpacing:"0.1em" }}>{label}</label>{children}</div>;
}

function Row({ children }: { children:React.ReactNode }) {
  return <div style={{ display:"flex", gap:8 }}>{children}</div>;
}

function Btn({ onClick, children, disabled }: { onClick:()=>void; children:React.ReactNode; disabled?:boolean }) {
  return <button onClick={onClick} disabled={disabled} style={{ padding:"0 12px", height:36, background:"rgba(255,255,255,.06)", border:"1px solid rgba(255,255,255,.1)", borderRadius:8, fontSize:12, color:disabled?"#4b5563":"#d1d5db", cursor:disabled?"not-allowed":"pointer" }}>{children}</button>;
}

function SaveBtn({ label, type, saved, saving, onClick }: { label:string; type:string; saved:boolean; saving:boolean; onClick:()=>void }) {
  return (
    <button onClick={onClick} disabled={saving}
      style={{ display:"flex", alignItems:"center", gap:6, padding:"9px 18px", background:saving?"#374151":"#4f46e5", border:"none", borderRadius:8, fontSize:13, color:"#fff", fontWeight:600, cursor:saving?"not-allowed":"pointer" }}>
      {saving?<div style={{ width:14, height:14, borderRadius:"50%", border:"2px solid #fff", borderTopColor:"transparent", animation:"spin .8s linear infinite" }}/>:saved?<CheckCircle2 style={{width:14,height:14}}/>:<Save style={{width:14,height:14}}/>}
      {saved?"Saved!":label}
      <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
    </button>
  );
}
