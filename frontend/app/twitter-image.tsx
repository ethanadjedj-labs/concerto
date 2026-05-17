import { ImageResponse } from "next/og"

export const runtime = "edge"
export const alt = "Concerto — Remote Workshop for Claude Code Agents"
export const size = { width: 1200, height: 600 }
export const contentType = "image/png"

export default function TwitterImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: 1200,
          height: 600,
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
        {/* Orbital ring background — warm + violet */}
        <svg
          width="1200"
          height="600"
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          {[90, 180, 275, 375, 490, 610].map((r, i) => (
            <ellipse
              key={r}
              cx="600"
              cy="650"
              rx={r * 2.1}
              ry={r}
              fill="none"
              stroke={i % 2 === 0 ? "rgba(217,119,87,0.09)" : "rgba(139,127,255,0.07)"}
              strokeWidth="1"
            />
          ))}
          <ellipse
            cx="600"
            cy="650"
            rx={180 * 2.1}
            ry={180}
            fill="none"
            stroke="rgba(217,119,87,0.26)"
            strokeWidth="1.5"
          />
          <ellipse
            cx="600"
            cy="650"
            rx={275 * 2.1}
            ry={275}
            fill="none"
            stroke="rgba(139,127,255,0.20)"
            strokeWidth="1"
          />
          <radialGradient id="tw-glow" cx="50%" cy="108%" r="40%">
            <stop offset="0%" stopColor="#d97757" stopOpacity="0.16" />
            <stop offset="100%" stopColor="#0f0d10" stopOpacity="0" />
          </radialGradient>
          <rect width="1200" height="600" fill="url(#tw-glow)" />
        </svg>

        {/* Logo mark — warm gradient */}
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: "linear-gradient(135deg, #d97757 0%, #8b7fff 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 24,
            boxShadow: "0 0 44px rgba(217,119,87,0.38)",
          }}
        >
          <span style={{ color: "#f5f0e9", fontSize: 38, fontWeight: 600, lineHeight: 1 }}>
            C
          </span>
        </div>

        {/* Wordmark */}
        <div
          style={{
            fontSize: 76,
            fontWeight: 600,
            color: "#f5f0e9",
            letterSpacing: "-0.02em",
            marginBottom: 18,
          }}
        >
          CONCERTO
        </div>

        {/* Tagline */}
        <div
          style={{
            fontSize: 26,
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
            bottom: 36,
            display: "flex",
            alignItems: "center",
            gap: 10,
            color: "#d97757",
            fontSize: 16,
            letterSpacing: "0.06em",
            opacity: 0.85,
          }}
        >
          <span style={{ color: "#8b7fff", fontSize: 10 }}>●</span>
          <span>concerto.run</span>
        </div>
      </div>
    ),
    size,
  )
}
