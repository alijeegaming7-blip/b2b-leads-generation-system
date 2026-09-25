import { Outlet, NavLink, useLocation } from "react-router-dom";
import { Bot, Megaphone, Users, MessageCircle, Mail, Settings, BarChart3, LogOut, ChevronDown } from "lucide-react";
import { getUser, getWorkspace, logout } from "../../lib/auth";
import { useNavigate } from "react-router-dom";
import { useDemo } from "../../hooks/useDemo";

const NAV = [
  { to: "/dashboard", icon: Bot,          label: "Agent Network", pulse: true },
  { to: "/campaigns", icon: Megaphone,     label: "Campaigns" },
  { to: "/leads",     icon: Users,         label: "Leads" },
  { to: "/whatsapp",  icon: MessageCircle, label: "WhatsApp Agent", badge: "AI" },
  { to: "/email",     icon: Mail,          label: "Email Agent",    badge: "AI" },
  { to: "/_analytics", icon: BarChart3,   label: "Analytics",      disabled: true },
];

const BOTTOM = [
  { to: "/settings", icon: Settings, label: "Settings & API Keys" },
];

export default function Layout() {
  const _navigate = useNavigate();
  const user      = getUser();
  const workspace = getWorkspace();
  const location  = useLocation();
  const demo      = useDemo();

  function handleLogout() { logout(); window.location.reload(); }

  function initials(name?: string | null) {
    if (!name) return "U";
    return name.split(" ").map(w => w[0]).join("").toUpperCase().slice(0, 2);
  }

  return (
    <div style={{ display:"flex", height:"100dvh", background:"#05050f", overflow:"hidden", paddingTop: demo.demo_mode ? 50 : 0 }}>

      {/* ── Sidebar ── */}
      <aside style={{
        width: 224, flexShrink: 0, display: "flex", flexDirection: "column",
        background: "#07071a", borderRight: "1px solid rgba(255,255,255,.06)",
      }}>

        {/* Logo */}
        <div style={{ display:"flex", alignItems:"center", gap:10, padding:"16px", borderBottom:"1px solid rgba(255,255,255,.06)", height:56 }}>
          <div style={{ width:32, height:32, borderRadius:10, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", fontWeight:800, fontSize:14, color:"#fff", flexShrink:0 }}>P</div>
          <span style={{ fontWeight:700, fontSize:14, color:"#fff", letterSpacing:"0.02em" }}>Prospex</span>
          <span style={{ marginLeft:"auto", fontSize:9, fontWeight:700, background:"rgba(99,102,241,.2)", color:"#a5b4fc", border:"1px solid rgba(99,102,241,.3)", borderRadius:6, padding:"2px 6px" }}>v2</span>
        </div>

        {/* Workspace */}
        <div style={{ padding:"10px 12px", borderBottom:"1px solid rgba(255,255,255,.06)" }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, padding:"6px 8px", borderRadius:8, background:"rgba(255,255,255,.03)" }}>
            <div style={{ width:22, height:22, borderRadius:6, background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
              <span style={{ fontSize:11, color:"#fff", fontWeight:700 }}>W</span>
            </div>
            <span style={{ fontSize:12, color:"#e5e7eb", flex:1, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>
              {workspace?.name ?? "My Workspace"}
            </span>
            <ChevronDown style={{ width:12, height:12, color:"#6b7280", flexShrink:0 }} />
          </div>
        </div>

        {/* Nav */}
        <nav style={{ flex:1, padding:"8px 12px", overflowY:"auto" }}>
          <p style={{ fontSize:10, fontWeight:600, color:"rgba(255,255,255,.3)", textTransform:"uppercase", letterSpacing:"0.12em", padding:"8px 6px 6px" }}>Main</p>
          {NAV.map(item => {
            if ((item as any).disabled) return (
              <div key={item.label} style={{ display:"flex", alignItems:"center", gap:10, padding:"8px 10px", borderRadius:8, color:"rgba(255,255,255,.2)", fontSize:13, cursor:"not-allowed", marginBottom:2 }}>
                <item.icon style={{ width:16, height:16 }} /><span style={{ flex:1 }}>{item.label}</span>
                <span style={{ fontSize:9, color:"rgba(255,255,255,.2)" }}>soon</span>
              </div>
            );
            const isActive = location.pathname === item.to || (item.to !== "/dashboard" && location.pathname.startsWith(item.to));
            return (
              <NavLink key={item.to} to={item.to} style={{ display:"block", marginBottom:2, textDecoration:"none" }}>
                <div style={{ display:"flex", alignItems:"center", gap:10, padding:"8px 10px", borderRadius:8, background: isActive?"rgba(99,102,241,.2)":"transparent", color: isActive?"#a5b4fc":"rgba(255,255,255,.6)", fontSize:13, fontWeight: isActive?600:400, transition:"all 0.15s" }}>
                  <item.icon style={{ width:16, height:16, flexShrink:0 }} />
                  <span style={{ flex:1 }}>{item.label}</span>
                  {(item as any).badge && <span style={{ fontSize:9, fontWeight:700, background:"rgba(99,102,241,.25)", color:"#a5b4fc", border:"1px solid rgba(99,102,241,.3)", borderRadius:6, padding:"1px 5px" }}>{(item as any).badge}</span>}
                  {(item as any).pulse && !isActive && (
                    <span style={{ position:"relative", width:8, height:8, display:"inline-flex" }}>
                      <span style={{ position:"absolute", inset:0, borderRadius:"50%", background:"#10b981", animation:"ping 1.5s ease infinite", opacity:0.75 }} />
                      <span style={{ borderRadius:"50%", width:8, height:8, background:"#10b981" }} />
                    </span>
                  )}
                </div>
              </NavLink>
            );
          })}

          <p style={{ fontSize:10, fontWeight:600, color:"rgba(255,255,255,.3)", textTransform:"uppercase", letterSpacing:"0.12em", padding:"16px 6px 6px" }}>Configuration</p>
          {BOTTOM.map(item => {
            const isActive = location.pathname.startsWith(item.to);
            return (
              <NavLink key={item.to} to={item.to} style={{ display:"block", marginBottom:2, textDecoration:"none" }}>
                <div style={{ display:"flex", alignItems:"center", gap:10, padding:"8px 10px", borderRadius:8, background: isActive?"rgba(99,102,241,.2)":"transparent", color: isActive?"#a5b4fc":"rgba(255,255,255,.6)", fontSize:13, fontWeight: isActive?600:400, transition:"all 0.15s" }}>
                  <item.icon style={{ width:16, height:16, flexShrink:0 }} />
                  <span style={{ flex:1 }}>{item.label}</span>
                </div>
              </NavLink>
            );
          })}
        </nav>

        {/* API Docs */}
        <div style={{ borderTop:"1px solid rgba(255,255,255,.06)", padding:"10px 12px" }}>
          <a href="/api/docs" target="_blank" rel="noreferrer"
            style={{ display:"flex", alignItems:"center", gap:10, padding:"7px 10px", borderRadius:8, color:"rgba(255,255,255,.4)", fontSize:12 }}>
            API Docs ↗
          </a>
        </div>

        {/* User */}
        <div style={{ borderTop:"1px solid rgba(255,255,255,.06)", padding:"10px 12px" }}>
          <div style={{ display:"flex", alignItems:"center", gap:8, padding:"6px 8px", borderRadius:8, cursor:"pointer" }} onClick={handleLogout} title="Click to logout">
            <div style={{ width:28, height:28, borderRadius:"50%", background:"linear-gradient(135deg,#6366f1,#8b5cf6)", display:"flex", alignItems:"center", justifyContent:"center", flexShrink:0 }}>
              <span style={{ fontSize:11, color:"#fff", fontWeight:700 }}>{initials(user?.name)}</span>
            </div>
            <div style={{ flex:1, minWidth:0 }}>
              <p style={{ fontSize:12, color:"#e5e7eb", fontWeight:500, overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{user?.name ?? "User"}</p>
              <p style={{ fontSize:10, color:"#6b7280", overflow:"hidden", textOverflow:"ellipsis", whiteSpace:"nowrap" }}>{user?.email ?? ""}</p>
            </div>
            <LogOut style={{ width:14, height:14, color:"#6b7280", flexShrink:0 }} />
          </div>
        </div>

      </aside>

      {/* ── Main content ── */}
      <div style={{ flex:1, display:"flex", flexDirection:"column", overflow:"hidden", minWidth:0 }}>
        <Outlet />
      </div>

      <style>{`
        @keyframes ping { 0%,100%{opacity:.75;transform:scale(1)} 50%{opacity:0;transform:scale(2)} }
        @keyframes spin  { to { transform: rotate(360deg); } }
        @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

        /* ── Mobile: hide sidebar, show bottom nav ── */
        @media (max-width: 768px) {
          aside { display: none !important; }
        }
      `}</style>
    </div>
  );
}
