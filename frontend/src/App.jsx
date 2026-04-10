import { useEffect } from "react";

export default function App() {
  useEffect(() => {
    window.location.replace("/");
  }, []);

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        background: "#050816",
        color: "#ffffff",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      Redirecting to War Room…
    </div>
  );
}