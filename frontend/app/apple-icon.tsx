import { ImageResponse } from "next/og"

export const runtime = "edge"
export const size = { width: 180, height: 180 }
export const contentType = "image/png"

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: 180,
          height: 180,
          borderRadius: 40,
          background: "#0f0d10",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <svg
          width="140"
          height="140"
          viewBox="0 0 200 200"
          xmlns="http://www.w3.org/2000/svg"
        >
          <path
            d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69"
            fill="none"
            stroke="#d97757"
            strokeWidth={6}
            strokeLinecap="round"
          />
          <path
            d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"
            fill="none"
            stroke="#b483ff"
            strokeWidth={6}
            strokeLinecap="round"
          />
          <path
            d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50"
            fill="none"
            stroke="#8b7fff"
            strokeWidth={6}
            strokeLinecap="round"
          />
          <circle cx="115.56" cy="115.56" r={6} fill="#d97757" />
          <circle cx="61.36"  cy="89.65"  r={6} fill="#b483ff" />
          <circle cx="150.23" cy="71.00"  r={6} fill="#8b7fff" />
          <circle cx="100"    cy="100"    r={9} fill="#f5f0e9" />
        </svg>
      </div>
    ),
    size,
  )
}
