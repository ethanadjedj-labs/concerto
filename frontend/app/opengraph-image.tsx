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
          fontFamily: "Georgia, 'Times New Roman', serif",
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
          <ellipse
            cx="600"
            cy="680"
            rx={200 * 2.1}
            ry={200}
            fill="none"
            stroke="rgba(217,119,87,0.28)"
            strokeWidth="1.5"
          />
          <ellipse
            cx="600"
            cy="680"
            rx={310 * 2.1}
            ry={310}
            fill="none"
            stroke="rgba(139,127,255,0.22)"
            strokeWidth="1"
          />
          <radialGradient id="og-glow" cx="50%" cy="108%" r="40%">
            <stop offset="0%"   stopColor="#d97757" stopOpacity="0.18" />
            <stop offset="60%"  stopColor="#8b7fff" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#0f0d10" stopOpacity="0" />
          </radialGradient>
          <rect width="1200" height="630" fill="url(#og-glow)" />
        </svg>

        {/* Orbital mark — the real logomark */}
        <svg
          width="148"
          height="148"
          viewBox="0 0 200 200"
          xmlns="http://www.w3.org/2000/svg"
          style={{ marginBottom: 28 }}
        >
          <path
            d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69"
            fill="none"
            stroke="#d97757"
            strokeWidth={3.5}
            strokeLinecap="round"
          />
          <path
            d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"
            fill="none"
            stroke="#b483ff"
            strokeWidth={3.5}
            strokeLinecap="round"
          />
          <path
            d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50"
            fill="none"
            stroke="#8b7fff"
            strokeWidth={3.5}
            strokeLinecap="round"
          />
          <circle cx="115.56" cy="115.56" r={5.5} fill="#d97757" />
          <circle cx="61.36"  cy="89.65"  r={5.5} fill="#b483ff" />
          <circle cx="150.23" cy="71.00"  r={5.5} fill="#8b7fff" />
          <circle cx="100"    cy="100"    r={7}   fill="#f5f0e9" />
        </svg>

        {/* Wordmark */}
        <div
          style={{
            fontSize: 96,
            fontWeight: 600,
            color: "#f5f0e9",
            letterSpacing: "-2px",
            lineHeight: 1,
            marginBottom: 20,
          }}
        >
          Concerto
        </div>

        {/* Tagline */}
        <div
          style={{
            fontSize: 27,
            color: "#c4b8aa",
            letterSpacing: "0.03em",
            fontWeight: 400,
            fontFamily: "system-ui, sans-serif",
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
            fontFamily: "system-ui, sans-serif",
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
