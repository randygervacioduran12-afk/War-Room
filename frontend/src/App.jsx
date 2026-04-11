import { useMemo } from "react";

export default function App() {
  const warRoomUrl = useMemo(() => {
    if (typeof window === "undefined") return "/";
    return `${window.location.origin}/`;
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background:
          "radial-gradient(circle at top, #0f172a 0%, #050816 55%, #020617 100%)",
        color: "#ffffff",
        fontFamily: "Inter, system-ui, sans-serif",
        padding: "24px",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: "720px",
          border: "1px solid rgba(255,255,255,0.12)",
          background: "rgba(255,255,255,0.04)",
          backdropFilter: "blur(14px)",
          borderRadius: "24px",
          padding: "32px",
          boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
        }}
      >
        <div
          style={{
            fontSize: "12px",
            letterSpacing: "0.14em",
            textTransform: "uppercase",
            opacity: 0.7,
            marginBottom: "12px",
          }}
        >
          War Room
        </div>

        <h1
          style={{
            margin: 0,
            fontSize: "32px",
            lineHeight: 1.1,
            marginBottom: "14px",
          }}
        >
          React placeholder detected
        </h1>

        <p
          style={{
            margin: 0,
            opacity: 0.82,
            fontSize: "16px",
            lineHeight: 1.6,
            marginBottom: "24px",
          }}
        >
          This project’s active interface is currently served by the FastAPI UI
          layer, not this React file. The main command surface lives at the app
          root.
        </p>

        <div
          style={{
            display: "flex",
            gap: "12px",
            flexWrap: "wrap",
            marginBottom: "22px",
          }}
        >
          <a
            href={warRoomUrl}
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              padding: "12px 18px",
              borderRadius: "14px",
              background: "#2563eb",
              color: "#ffffff",
              textDecoration: "none",
              fontWeight: 600,
            }}
          >
            Open War Room
          </a>

          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "12px 18px",
              borderRadius: "14px",
              border: "1px solid rgba(255,255,255,0.16)",
              background: "transparent",
              color: "#ffffff",
              cursor: "pointer",
              fontWeight: 600,
            }}
          >
            Refresh
          </button>
        </div>

        <div
          style={{
            padding: "16px",
            borderRadius: "16px",
            background: "rgba(255,255,255,0.05)",
            border: "1px solid rgba(255,255,255,0.08)",
            fontSize: "14px",
            lineHeight: 1.7,
            opacity: 0.88,
          }}
        >
          <div><strong>Current active UI:</strong> FastAPI + custom shell</div>
          <div><strong>Primary route owner:</strong> <code>/</code></div>
          <div><strong>React status:</strong> placeholder only</div>
        </div>
      </div>
    </div>
  );
}