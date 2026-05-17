import { ImageResponse } from "next/og"

export const runtime = "edge"
export const size = { width: 32, height: 32 }
export const contentType = "image/png"

export default function Icon() {
  return new ImageResponse(
    (
      <svg
        width="32"
        height="32"
        viewBox="0 0 200 200"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect width="200" height="200" rx="42" fill="#0f0d10" />
        <path
          d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69"
          fill="none"
          stroke="#d97757"
          strokeWidth={10}
          strokeLinecap="round"
        />
        <path
          d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"
          fill="none"
          stroke="#b483ff"
          strokeWidth={10}
          strokeLinecap="round"
        />
        <path
          d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50"
          fill="none"
          stroke="#8b7fff"
          strokeWidth={10}
          strokeLinecap="round"
        />
        <circle cx="115.56" cy="115.56" r={12} fill="#d97757" />
        <circle cx="61.36"  cy="89.65"  r={12} fill="#b483ff" />
        <circle cx="150.23" cy="71.00"  r={12} fill="#8b7fff" />
        <circle cx="100"    cy="100"    r={16} fill="#f5f0e9" />
      </svg>
    ),
    size,
  )
}
