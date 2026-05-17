import { ImageResponse } from "next/og"

export const runtime = "nodejs"
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
        <rect width="200" height="200" rx="42" fill="#faf9f5" />
        <path
          d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69"
          fill="none"
          stroke="#cc785c"
          strokeWidth={10}
          strokeLinecap="round"
        />
        <path
          d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"
          fill="none"
          stroke="#2a2925"
          strokeWidth={10}
          strokeLinecap="round"
          opacity={0.55}
        />
        <path
          d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50"
          fill="none"
          stroke="#2a2925"
          strokeWidth={10}
          strokeLinecap="round"
          opacity={0.35}
        />
        <circle cx="115.56" cy="115.56" r={12} fill="#cc785c" />
        <circle cx="61.36"  cy="89.65"  r={12} fill="#2a2925" opacity={0.55} />
        <circle cx="150.23" cy="71.00"  r={12} fill="#2a2925" opacity={0.35} />
        <circle cx="100"    cy="100"    r={16} fill="#191919" />
      </svg>
    ),
    size,
  )
}
