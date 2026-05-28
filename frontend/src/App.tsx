import { HealthBadge } from "./components/HealthBadge";
import { PilotMap } from "./components/PilotMap";

export default function App() {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100vh",
        fontFamily: "system-ui, sans-serif",
      }}
    >
      <header
        style={{
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          padding: "10px 16px",
          borderBottom: "1px solid #eee",
        }}
      >
        <strong>TerraBean — Arabica Suitability (Nepal mid-hills pilot)</strong>
        <HealthBadge />
      </header>
      <main style={{ flex: 1 }}>
        <PilotMap />
      </main>
    </div>
  );
}
