import { ImageResponse } from "next/og"

export const runtime = "edge"
export const alt = "Concerto — Remote Workshop for Claude Code Agents"
export const size = { width: 1200, height: 630 }
export const contentType = "image/png"

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: 1200,
          height: 630,
          background: "#0f0d10",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "system-ui, sans-serif",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Orbital ring background — warm + violet palette */}
        <svg
          width="1200"
          height="630"
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          {/* Warm orbital rings */}
          {[100, 200, 310, 430, 560, 700].map((r, i) => (
            <ellipse
              key={`w${r}`}
              cx="600"
              cy="680"
              rx={r * 2.1}
              ry={r}
              fill="none"
              stroke={i % 2 === 0 ? "rgba(217,119,87,0.09)" : "rgba(139,127,255,0.07)"}
              strokeWidth="1"
            />
          ))}
          {/* Warm accent glow ring */}
          <ellipse
            cx="600"
            cy="680"
            rx={200 * 2.1}
            ry={200}
            fill="none"
            stroke="rgba(217,119,87,0.28)"
            strokeWidth="1.5"
          />
          {/* Violet accent ring */}
          <ellipse
            cx="600"
            cy="680"
            rx={310 * 2.1}
            ry={310}
            fill="none"
            stroke="rgba(139,127,255,0.22)"
            strokeWidth="1"
          />
          {/* Center glow */}
          <radialGradient id="og-glow" cx="50%" cy="108%" r="40%">
            <stop offset="0%" stopColor="#d97757" stopOpacity="0.18" />
            <stop offset="60%" stopColor="#8b7fff" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#0f0d10" stopOpacity="0" />
          </radialGradient>
          <rect width="1200" height="630" fill="url(#og-glow)" />
        </svg>

        {/* Logo mark — warm gradient */}
        <div
          style={{
            width: 72,
            height: 72,
            borderRadius: 18,
            background: "linear-gradient(135deg, #d97757 0%, #8b7fff 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 28,
            boxShadow: "0 0 48px rgba(217,119,87,0.40)",
          }}
        >
          <span style={{ color: "#f5f0e9", fontSize: 42, fontWeight: 600, lineHeight: 1 }}>
            C
          </span>
        </div>

        {/* Wordmark */}
        <div
          style={{
            fontSize: 80,
            fontWeight: 600,
            color: "#f5f0e9",
            letterSpacing: "-0.02em",
            marginBottom: 20,
          }}
        >
          CONCERTO
        </div>

        {/* Tagline */}
        <div
          style={{
            fontSize: 28,
            color: "#c4b8aa",
            letterSpacing: "0.03em",
            fontWeight: 400,
          }}
        >
          Remote Workshop for Claude Code Agents
        </div>

        {/* Bottom accent */}
        <div
          style={{
            position: "absolute",
            bottom: 40,
            display: "flex",
            alignItems: "center",
            gap: 10,
            color: "#d97757",
            fontSize: 18,
            letterSpacing: "0.06em",
            opacity: 0.85,
          }}
        >
          <span style={{ color: "#8b7fff", fontSize: 12 }}>●</span>
          <span>concerto.run</span>
        </div>
      </div>
    ),
    size,
  )
}
