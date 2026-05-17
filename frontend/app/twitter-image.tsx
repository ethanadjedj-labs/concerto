import { ImageResponse } from "next/og"

export const runtime = "nodejs"
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
          background: "#faf9f5",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          fontFamily: "Georgia, 'Times New Roman', serif",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Editorial peach line */}
        <div
          style={{
            position: "absolute",
            top: 52,
            left: "50%",
            transform: "translateX(-50%)",
            width: 72,
            height: 1,
            background: "#cc785c",
            opacity: 0.7,
          }}
        />

        {/* Logo mark */}
        <svg
          width="88"
          height="88"
          viewBox="0 0 200 200"
          xmlns="http://www.w3.org/2000/svg"
          style={{ marginBottom: 26 }}
        >
          <path
            d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69"
            fill="none"
            stroke="#cc785c"
            strokeWidth={13}
            strokeLinecap="round"
          />
          <path
            d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"
            fill="none"
            stroke="#2a2925"
            strokeWidth={13}
            strokeLinecap="round"
            opacity={0.55}
          />
          <path
            d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50"
            fill="none"
            stroke="#2a2925"
            strokeWidth={13}
            strokeLinecap="round"
            opacity={0.35}
          />
          <circle cx="115.56" cy="115.56" r={14} fill="#cc785c" />
          <circle cx="61.36"  cy="89.65"  r={14} fill="#2a2925" opacity={0.55} />
          <circle cx="150.23" cy="71.00"  r={14} fill="#2a2925" opacity={0.35} />
          <circle cx="100"    cy="100"    r={20} fill="#191919" />
        </svg>

        {/* Wordmark */}
        <div
          style={{
            fontSize: 88,
            fontWeight: 500,
            color: "#191919",
            letterSpacing: "-2px",
            lineHeight: 1,
            marginBottom: 18,
          }}
        >
          Concerto
        </div>

        {/* Tagline */}
        <div
          style={{
            fontSize: 24,
            color: "#555049",
            letterSpacing: "0.01em",
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
            color: "#cc785c",
            fontSize: 16,
            letterSpacing: "0.04em",
            fontFamily: "system-ui, sans-serif",
          }}
        >
          <span style={{ display: "block", width: 5, height: 5, borderRadius: "50%", background: "#cc785c" }} />
          <span>concerto.run</span>
        </div>
      </div>
    ),
    size,
  )
}
