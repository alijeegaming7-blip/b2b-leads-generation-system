import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { ensureAuth } from "./lib/auth";
import Layout from "./components/layout/Layout";
import DashboardPage from "./pages/Dashboard";
import LeadsPage      from "./pages/Leads";
import WhatsAppPage   from "./pages/WhatsApp";
import EmailPage      from "./pages/Email";
import SettingsPage   from "./pages/Settings";
import CampaignsPage  from "./pages/Campaigns";
import DemoBanner     from "./components/DemoBanner";

function Spinner() {
  return (
    <div style={{ display:"flex", height:"100vh", alignItems:"center", justifyContent:"center", background:"#05050f" }}>
      <div style={{ display:"flex", flexDirection:"column", alignItems:"center", gap:16 }}>
        <div style={{ position:"relative", width:56, height:56 }}>
          <div style={{ position:"absolute", inset:0, borderRadius:"50%", border:"2px solid rgba(99,102,241,.2)", animation:"ping 1.5s ease infinite" }} />
          <div style={{ position:"absolute", inset:8, borderRadius:"50%", border:"2px solid #6366f1", borderTopColor:"transparent", animation:"spin 0.8s linear infinite" }} />
        </div>
        <p style={{ color:"#6b7280", fontSize:11, letterSpacing:"0.15em", textTransform:"uppercase" }}>Initialising…</p>
      </div>
      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
        @keyframes ping { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.4;transform:scale(1.15)} }
      `}</style>
    </div>
  );
}

export default function App() {
  const [ready, setReady] = useState(false);

  useEffect(() => {
    ensureAuth().finally(() => setReady(true));
  }, []);

  if (!ready) return <Spinner />;

  return (
    <>
      <DemoBanner />
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/dashboard" replace />} />
          <Route path="dashboard"  element={<DashboardPage />} />
          <Route path="leads"      element={<LeadsPage />} />
          <Route path="whatsapp"   element={<WhatsAppPage />} />
          <Route path="email"      element={<EmailPage />} />
          <Route path="settings"   element={<SettingsPage />} />
          <Route path="campaigns"  element={<CampaignsPage />} />
          <Route path="*"          element={<Navigate to="/dashboard" replace />} />
        </Route>
      </Routes>
    </>
  );
}
