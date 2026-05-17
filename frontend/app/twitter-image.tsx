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
          background: "#0a0a0b",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "monospace",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Concentric arc background pattern */}
        <svg
          width="1200"
          height="600"
          style={{ position: "absolute", top: 0, left: 0 }}
        >
          {[80, 160, 240, 320, 400, 480].map((r) => (
            <ellipse
              key={r}
              cx="600"
              cy="650"
              rx={r * 2.2}
              ry={r}
              fill="none"
              stroke="rgba(124,58,237,0.12)"
              strokeWidth="1"
            />
          ))}
          <ellipse
            cx="600"
            cy="650"
            rx={160 * 2.2}
            ry={160}
            fill="none"
            stroke="rgba(124,58,237,0.3)"
            strokeWidth="1.5"
          />
        </svg>

        {/* Logo mark */}
        <div
          style={{
            width: 64,
            height: 64,
            borderRadius: 16,
            background: "linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 24,
            boxShadow: "0 0 40px rgba(124,58,237,0.5)",
          }}
        >
          <span style={{ color: "white", fontSize: 38, fontWeight: 700, lineHeight: 1 }}>
            C
          </span>
        </div>

        {/* Wordmark */}
        <div
          style={{
            fontSize: 76,
            fontWeight: 700,
            color: "white",
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
            color: "rgba(255,255,255,0.55)",
            letterSpacing: "0.04em",
            textTransform: "uppercase",
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
            gap: 12,
            color: "rgba(124,58,237,0.8)",
            fontSize: 16,
            letterSpacing: "0.08em",
          }}
        >
          <span style={{ color: "rgba(124,58,237,0.6)", fontSize: 12 }}>▶</span>
          <span>concerto.run</span>
        </div>
      </div>
    ),
    size,
  )
}
