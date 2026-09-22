import { useDemo } from "../hooks/useDemo";
import { Lock, ShoppingCart } from "lucide-react";

interface Props {
  children: React.ReactNode;
  field?: string;
  inline?: boolean;
}

// ── Inline blur for phone/email text ─────────────────────────────────────────
export default function DemoBlur({ children, inline = false }: Props) {
  const demo = useDemo();
  if (!demo.demo_mode) return <>{children}</>;

  const Tag = inline ? "span" : "div" as any;

  return (
    <Tag style={{ position: "relative", display: inline ? "inline-flex" : "flex", alignItems: "center", gap: 4 }}>
      <Tag style={{ filter: "blur(5px)", userSelect: "none", pointerEvents: "none", opacity: 0.5 }}>
        {children}
      </Tag>
      <Tag style={{ position: "absolute", inset: 0, display: "flex", alignItems: "center", justifyContent: "center", gap: 3 }}>
        <Lock style={{ width: 10, height: 10, color: "#fbbf24" }} />
        {!inline && <span style={{ fontSize: 10, color: "#fbbf24", fontWeight: 700, whiteSpace: "nowrap" }}>Buy to unlock</span>}
      </Tag>
    </Tag>
  );
}

// ── Full upgrade box shown in lead detail modal ───────────────────────────────
export function DemoUpgradeBox({ buyLink, price: _price }: { buyLink: string; price: string }) {
  const demo = useDemo();
  if (!demo.demo_mode) return null;

  return (
    <div style={{
      margin: "8px 0",
      padding: "24px 20px",
      background: "linear-gradient(135deg, rgba(124,58,237,.2) 0%, rgba(79,70,229,.15) 100%)",
      border: "2px solid rgba(124,58,237,.5)",
      borderRadius: 16,
      textAlign: "center",
    }}>
      <div style={{ fontSize: 44, marginBottom: 12 }}>🔒</div>
      <h3 style={{ fontSize: 17, fontWeight: 800, color: "#fff", margin: "0 0 10px" }}>
        Contact Details Hidden
      </h3>
      <p style={{ fontSize: 13, color: "#9ca3af", margin: "0 0 8px", lineHeight: 1.7 }}>
        This is a <strong style={{ color: "#fbbf24" }}>DEMO</strong> version.
      </p>
      <p style={{ fontSize: 13, color: "#9ca3af", margin: "0 0 20px", lineHeight: 1.7 }}>
        Buy the full system to unlock:
      </p>
      <div style={{ display: "flex", flexDirection: "column", gap: 8, marginBottom: 20, textAlign: "left", padding: "0 10px" }}>
        {["📞 Real phone numbers", "📧 Email addresses", "📱 Facebook, Instagram, TikTok profiles", "🔗 LinkedIn & WhatsApp links", "📥 Export full CSV with all data"].map(item => (
          <div key={item} style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "#d1d5db" }}>
            <span>{item}</span>
          </div>
        ))}
      </div>
      <a
        href={buyLink || "#"}
        target="_blank"
        rel="noreferrer"
        style={{
          display: "inline-flex", alignItems: "center", gap: 8,
          padding: "13px 32px", borderRadius: 12,
          background: "linear-gradient(135deg, #7c3aed, #4f46e5)",
          color: "#fff", fontWeight: 800, fontSize: 15, textDecoration: "none",
          boxShadow: "0 4px 24px rgba(124,58,237,.5)",
        }}
      >
        <ShoppingCart style={{ width: 16, height: 16 }} />
        Buy Full System
      </a>
      <p style={{ fontSize: 11, color: "#4b5563", marginTop: 12 }}>
        One-time payment · Full source code · All features
      </p>
    </div>
  );
}
