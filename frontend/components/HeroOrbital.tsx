"use client"

/* Concentric orbital animation for the Concerto hero section.
   Five independent circular paths rotate at different speeds and
   directions — evoking "multiple sessions in coordinated motion."

   Trademark note: this is NOT the Anthropic concentric-arc logo.
   Those arcs are asymmetric and artistically arranged; these are
   full, symmetrical, counter-rotating circular orbits viewed
   straight-on — a different motif entirely. */

const CX = 400
const CY = 400

const ORBITS: Array<{
  r: number
  dur: string
  stroke: string
  strokeOp: number
  dot: string
  dotR: number
  cw: boolean
  startAngle: number
}> = [
  { r:  52,  dur: "18s",  stroke: "#8b7fff", strokeOp: 0.22, dot: "#d97757", dotR: 4.5, cw: true,  startAngle:   0 },
  { r: 105,  dur: "32s",  stroke: "#d97757", strokeOp: 0.16, dot: "#8b7fff", dotR: 3.5, cw: false, startAngle:  72 },
  { r: 163,  dur: "52s",  stroke: "#8b7fff", strokeOp: 0.11, dot: "#d97757", dotR: 4,   cw: true,  startAngle: 144 },
  { r: 225,  dur: "76s",  stroke: "#d97757", strokeOp: 0.07, dot: "#8b7fff", dotR: 3,   cw: false, startAngle: 216 },
  { r: 290,  dur: "106s", stroke: "#8b7fff", strokeOp: 0.04, dot: "#d97757", dotR: 3.5, cw: true,  startAngle: 288 },
]

function dotPosition(r: number, angleDeg: number): { x: number; y: number } {
  const rad = (angleDeg * Math.PI) / 180
  return {
    x: CX + r * Math.cos(rad),
    y: CY + r * Math.sin(rad),
  }
}

export function HeroOrbital() {
  return (
    <svg
      viewBox="0 0 800 800"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
      className="hero-orbital absolute inset-0 h-full w-full"
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        {/* Radial vignette — fade orbits toward edges */}
        <radialGradient id="orbital-fade" cx="50%" cy="50%" r="50%">
          <stop offset="30%" stopColor="white" stopOpacity="1" />
          <stop offset="88%" stopColor="white" stopOpacity="0" />
        </radialGradient>
        <mask id="orbital-vignette">
          <rect width="800" height="800" fill="url(#orbital-fade)" />
        </mask>
      </defs>

      <g mask="url(#orbital-vignette)">
        {ORBITS.map(({ r, dur, stroke, strokeOp, dot, dotR, cw, startAngle }, i) => {
          const { x: dx, y: dy } = dotPosition(r, startAngle)
          return (
            <g key={i}>
              {/* Static circular path */}
              <circle
                cx={CX}
                cy={CY}
                r={r}
                stroke={stroke}
                strokeWidth="1"
                fill="none"
                opacity={strokeOp}
              />
              {/* Rotating satellite dot — GPU-accelerated via CSS transform */}
              <g
                style={{
                  transformBox: "view-box" as const,
                  transformOrigin: "50% 50%",
                  willChange: "transform",
                  animationName: cw ? "orbit-cw" : "orbit-ccw",
                  animationDuration: dur,
                  animationTimingFunction: "linear",
                  animationIterationCount: "infinite",
                }}
              >
                <circle cx={dx} cy={dy} r={dotR} fill={dot} opacity="0.9" />
              </g>
            </g>
          )
        })}

        {/* Center core — represents the active Claude session */}
        <circle cx={CX} cy={CY} r="32" fill="#d97757" opacity="0.05" />
        <circle cx={CX} cy={CY} r="16" fill="#d97757" opacity="0.10" />
        <circle cx={CX} cy={CY} r="5"  fill="#d97757" opacity="0.95" />
      </g>
    </svg>
  )
}
