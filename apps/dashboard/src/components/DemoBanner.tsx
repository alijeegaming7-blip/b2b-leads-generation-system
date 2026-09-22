import { useDemo } from "../hooks/useDemo";
import { Lock, ShoppingCart } from "lucide-react";

export default function DemoBanner() {
  const demo = useDemo();
  if (!demo.demo_mode) return null;

  return (
    <div style={{
      position: "fixed", top: 0, left: 0, right: 0, zIndex: 9999,
      background: "linear-gradient(90deg, #7c3aed 0%, #4f46e5 40%, #0ea5e9 100%)",
      padding: "0 20px",
      height: 52,
      display: "flex", alignItems: "center", justifyContent: "space-between",
      boxShadow: "0 2px 24px rgba(124,58,237,.7)",
      gap: 12,
    }}>
      {/* Left */}
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        <div style={{ width: 28, height: 28, borderRadius: 8, background: "rgba(255,255,255,.2)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Lock style={{ width: 14, height: 14, color: "#fbbf24" }} />
        </div>
        <div>
          <p style={{ fontSize: 13, fontWeight: 700, color: "#fff", margin: 0, lineHeight: 1.3 }}>
            🔒 <span style={{ color: "#fbbf24" }}>DEMO MODE</span> — Real leads shown, but contact details are hidden
          </p>
          <p style={{ fontSize: 11, color: "rgba(255,255,255,.7)", margin: 0 }}>
            Phone • Email • Social Media are blurred — buy to unlock everything
          </p>
        </div>
      </div>

      {/* Buy button */}
      <a
        href={demo.buy_link || "#"}
        target="_blank"
        rel="noreferrer"
        style={{
          flexShrink: 0,
          display: "flex", alignItems: "center", gap: 7,
          padding: "8px 18px", borderRadius: 10,
          background: "#fbbf24", color: "#1a1a1a",
          fontWeight: 800, fontSize: 13, textDecoration: "none",
          boxShadow: "0 2px 12px rgba(251,191,36,.6)",
          whiteSpace: "nowrap",
        }}
      >
        <ShoppingCart style={{ width: 14, height: 14 }} />
        Buy Full System
      </a>
    </div>
  );
}
