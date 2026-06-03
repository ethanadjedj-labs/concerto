"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { Check, ExternalLink, RefreshCw, Github } from "lucide-react"
import {
  DEMO_TEXTS,
  DEMO_TIMINGS,
  CURSOR_WAYPOINTS,
  type CursorWaypoint,
} from "./hero-claude-demo-script"

/* ── Types ────────────────────────────────────────────────────── */

type Step = 1 | 2 | 3

type SignInPhase =
  | "idle"          // primary "Sign in with Claude" button
  | "starting"      // button shows "Preparing sign-in…"
  | "awaiting_code" // open-Anthropic link + paste field, empty
  | "code_typed"    // paste field filled, ready to submit
  | "finishing"     // submit clicked, spinner running
  | "success"       // green confirmation visible

interface DemoState {
  step: Step
  signIn: SignInPhase
  codeChars: number          // how many characters of the pasted code are visible
  connectPhase: "ready" | "waiting"
  fading: boolean
}

interface CursorState {
  x: number
  y: number
  clicking: boolean
}

const INITIAL: DemoState = {
  step: 1,
  signIn: "idle",
  codeChars: 0,
  connectPhase: "ready",
  fading: false,
}

/* ── Hooks ────────────────────────────────────────────────────── */

function usePrefersReducedMotion(): boolean {
  const [r, setR] = useState(false)
  useEffect(() => {
    const mq = window.matchMedia("(prefers-reduced-motion: reduce)")
    setR(mq.matches)
    const h = (e: MediaQueryListEvent) => setR(e.matches)
    mq.addEventListener("change", h)
    return () => mq.removeEventListener("change", h)
  }, [])
  return r
}

/* ── CSS keyframes (reused across the component) ────────────────── */

const CSS_KEYFRAMES = `
  @keyframes cc-fade-in {
    from { opacity: 0 } to { opacity: 1 }
  }
  @keyframes cc-fade-up {
    from { opacity: 0; transform: translateY(6px) }
    to   { opacity: 1; transform: translateY(0)   }
  }
  @keyframes cc-blink {
    0%,100% { opacity: 1 } 50% { opacity: 0 }
  }
  @keyframes cc-cursor-click {
    0%   { transform: scale(1)    }
    40%  { transform: scale(0.82) }
    100% { transform: scale(1)    }
  }
  @keyframes cc-ripple {
    0%   { transform: scale(0);   opacity: 0.45 }
    100% { transform: scale(2.8); opacity: 0    }
  }
  @keyframes cc-spin {
    to { transform: rotate(360deg) }
  }
`

/* ── Animated mouse cursor (macOS arrow) ───────────────────────── */

function MouseCursor({ x, y, clicking }: CursorState) {
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        left: x,
        top: y,
        pointerEvents: "none",
        zIndex: 100,
        transform: "translate(-2px, -2px)",
        transition:
          "left 0.40s cubic-bezier(0.25,0.46,0.45,0.94), top 0.40s cubic-bezier(0.25,0.46,0.45,0.94)",
        willChange: "left, top",
      }}
    >
      {clicking && (
        <div
          style={{
            position: "absolute",
            left: 4,
            top: 4,
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: "rgba(204,120,92,0.32)",
            animation: "cc-ripple 0.42s cubic-bezier(0.22,1,0.36,1) both",
          }}
        />
      )}
      <svg
        width="20"
        height="22"
        viewBox="0 0 20 22"
        fill="none"
        style={{
          filter:
            "drop-shadow(0 1px 2px rgba(25,25,25,0.35)) drop-shadow(0 0 1px rgba(25,25,25,0.6))",
          animation: clicking ? "cc-cursor-click 0.22s ease both" : "none",
        }}
      >
        <path
          d="M3 1L3 17.5L6.8 13.8L9.6 19.6L11.8 18.6L9.1 12.8L14 12.8L3 1Z"
          fill="#191919"
          stroke="#191919"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        <path
          d="M3 1L3 17.5L6.8 13.8L9.6 19.6L11.8 18.6L9.1 12.8L14 12.8L3 1Z"
          fill="#ffffff"
          strokeWidth="0"
        />
      </svg>
    </div>
  )
}

/* ── Cursor animation engine (identical math, different waypoints) ── */

function useCursorAnimation(
  waypoints: CursorWaypoint[],
  loopDuration: number,
  containerRef: { current: HTMLDivElement | null },
): CursorState {
  const [cursor, setCursor] = useState<CursorState>({ x: 0, y: 0, clicking: false })
  const rafRef = useRef<number | null>(null)
  const startTimeRef = useRef<number | null>(null)

  useEffect(() => {
    let cancelled = false

    function getContainerSize() {
      if (!containerRef.current) return { w: 600, h: 468 }
      const r = containerRef.current.getBoundingClientRect()
      return { w: r.width, h: r.height }
    }

    const lerp = (a: number, b: number, t: number) => a + (b - a) * t
    const easeOut = (t: number) => 1 - Math.pow(1 - t, 3)

    function tick(now: number) {
      if (cancelled) return
      if (!startTimeRef.current) startTimeRef.current = now

      const elapsed = (now - startTimeRef.current) % loopDuration
      const { w, h } = getContainerSize()

      let prev = waypoints[0]
      let next = waypoints[waypoints.length - 1]
      for (let i = 0; i < waypoints.length - 1; i++) {
        if (elapsed >= waypoints[i].t && elapsed < waypoints[i + 1].t) {
          prev = waypoints[i]
          next = waypoints[i + 1]
          break
        }
      }

      const segDuration = next.t - prev.t
      const segElapsed  = elapsed - prev.t
      const rawT = segDuration > 0 ? Math.min(segElapsed / segDuration, 1) : 1
      const t = easeOut(rawT)

      const px = lerp(prev.x * w, next.x * w, t)
      const py = lerp(prev.y * h, next.y * h, t)

      const isClicking = waypoints.some(
        (wp) => wp.action === "click" && Math.abs(elapsed - wp.t) < 140
      )

      setCursor({ x: px, y: py, clicking: isClicking })
      rafRef.current = requestAnimationFrame(tick)
    }

    rafRef.current = requestAnimationFrame(tick)
    return () => {
      cancelled = true
      if (rafRef.current) cancelAnimationFrame(rafRef.current)
    }
  }, [waypoints, loopDuration, containerRef])

  return cursor
}

/* ── Concerto logo mark (matches /brand/logo-mark.png at small size) ── */

function LogoMark({ size = 28 }: { size?: number }) {
  // Same image the real dashboard uses for header branding.
  // eslint-disable-next-line @next/next/no-img-element
  return (
    <img
      src="/brand/logo-mark.png?v=3"
      alt=""
      width={size}
      height={size}
      style={{ display: "block", width: size, height: size }}
    />
  )
}

/* ── Concerto top header (matches dashboard sticky header) ──────── */

function DashHeader() {
  return (
    <header
      style={{
        position: "sticky",
        top: 0,
        zIndex: 5,
        borderBottom: "1px solid rgba(25,25,25,0.07)",
        background: "rgba(250,249,245,0.90)",
        backdropFilter: "blur(12px)",
      }}
    >
      <div
        style={{
          maxWidth: 560,
          margin: "0 auto",
          padding: "10px 18px",
          display: "flex",
          alignItems: "center",
          gap: 10,
        }}
      >
        <LogoMark size={24} />
        <span
          style={{
            fontSize: 16,
            fontWeight: 500,
            letterSpacing: "-0.01em",
            color: "#191919",
            lineHeight: 1,
          }}
        >
          Concerto
        </span>
      </div>
    </header>
  )
}

/* ── 3-step progress bar (matches ProgressBar in dashboard) ──────── */

function ProgressBar({ step }: { step: Step }) {
  const labels = DEMO_TEXTS.progressLabels
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
      <div style={{ display: "flex", alignItems: "center" }}>
        {([1, 2, 3] as const).map((s, i) => (
          <div key={s} style={{ display: "flex", alignItems: "center" }}>
            <div
              style={{
                display: "flex",
                flexDirection: "column",
                alignItems: "center",
                gap: 6,
                width: 64,
              }}
            >
              <div
                style={{
                  display: "flex",
                  width: 22,
                  height: 22,
                  alignItems: "center",
                  justifyContent: "center",
                  borderRadius: "50%",
                  fontSize: 11,
                  fontWeight: 600,
                  backgroundColor:
                    s < step
                      ? "#cc785c"
                      : s === step
                        ? "#cc785c"
                        : "rgba(25,25,25,0.08)",
                  color: s <= step ? "#ffffff" : "#8a847b",
                  transition: "background-color 0.35s ease, color 0.35s ease",
                }}
              >
                {s < step ? <Check size={12} strokeWidth={3} /> : s}
              </div>
              <span
                style={{
                  fontSize: 11,
                  fontWeight: 500,
                  color: s === step ? "#191919" : "#8a847b",
                  transition: "color 0.35s ease",
                }}
              >
                {labels[i]}
              </span>
            </div>
            {i < 2 && (
              <div
                style={{
                  height: 2,
                  width: 28,
                  marginBottom: 18,
                  background: s < step ? "#cc785c" : "rgba(25,25,25,0.12)",
                  transition: "background 0.35s ease",
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* ── Card primitive (matches dashboard rounded-2xl card) ─────────── */

function Card({ children, style }: { children: React.ReactNode; style?: React.CSSProperties }) {
  return (
    <div
      style={{
        borderRadius: 16,
        background: "#ffffff",
        border: "1px solid #f3efe5",
        animation: "cc-fade-up 0.32s cubic-bezier(0.22,1,0.36,1) both",
        ...style,
      }}
    >
      {children}
    </div>
  )
}

/* ── Step 1: Sign in to Claude ───────────────────────────────────── */

function Step1Card({
  phase,
  codeChars,
}: {
  phase: SignInPhase
  codeChars: number
}) {
  const t = DEMO_TEXTS.step1
  const codeText = t.codeTyped.slice(0, codeChars)
  const typing = phase === "awaiting_code" && codeChars < t.codeTyped.length
  const showSuccess = phase === "success"
  const showInitialButton = phase === "idle" || phase === "starting"
  const showCodeFlow =
    phase === "awaiting_code" ||
    phase === "code_typed" ||
    phase === "finishing"

  return (
    <Card style={{ padding: "20px 22px" }}>
      <div style={{ marginBottom: 16 }}>
        <h2
          style={{
            margin: 0,
            fontSize: 19,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            color: "#191919",
          }}
        >
          {t.title}
        </h2>
        <p
          style={{
            marginTop: 6,
            marginBottom: 0,
            fontSize: 13,
            lineHeight: 1.55,
            color: "#8a847b",
          }}
        >
          {t.blurb}
        </p>
      </div>

      {showInitialButton && !showSuccess && (
        <button
          type="button"
          style={{
            width: "100%",
            borderRadius: 12,
            background: "#cc785c",
            color: "#ffffff",
            fontSize: 14,
            fontWeight: 500,
            minHeight: 44,
            border: "none",
            cursor: "default",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            transition: "background 0.25s ease",
          }}
        >
          {phase === "starting" ? (
            <>
              <RefreshCw
                size={14}
                style={{
                  transformOrigin: "center",
                  animation: "cc-spin 1.2s linear infinite",
                }}
              />
              {t.primaryStarting}
            </>
          ) : (
            t.primaryIdle
          )}
        </button>
      )}

      {showCodeFlow && !showSuccess && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              width: "100%",
              minHeight: 42,
              borderRadius: 12,
              background: "#191919",
              color: "#ffffff",
              fontSize: 13.5,
              fontWeight: 600,
            }}
          >
            {t.openAnthropic}
            <ExternalLink size={14} />
          </div>

          <div>
            <label
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: "#191919",
                marginBottom: 6,
              }}
            >
              {t.codeLabel}
            </label>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                width: "100%",
                minHeight: 40,
                padding: "8px 12px",
                borderRadius: 12,
                border: "2px solid #cc785c",
                background: "#ffffff",
                fontSize: 13,
                fontFamily:
                  "'SF Mono', 'JetBrains Mono', 'Fira Code', Consolas, monospace",
                color: codeChars === 0 ? "#a59f97" : "#191919",
                boxShadow:
                  phase === "awaiting_code" || phase === "code_typed"
                    ? "0 0 0 3px rgba(204,120,92,0.15)"
                    : "none",
                letterSpacing: "0.01em",
              }}
            >
              {codeChars === 0 ? t.codePlaceholder : codeText}
              {typing && (
                <span
                  style={{
                    display: "inline-block",
                    width: 1.4,
                    height: "1.1em",
                    background: "#cc785c",
                    verticalAlign: "text-bottom",
                    marginLeft: 1,
                    animation: "cc-blink 0.7s step-end infinite",
                    borderRadius: 1,
                  }}
                />
              )}
            </div>

            <button
              type="button"
              style={{
                marginTop: 10,
                width: "100%",
                borderRadius: 12,
                background:
                  phase === "code_typed" || phase === "finishing"
                    ? "#cc785c"
                    : "rgba(204,120,92,0.5)",
                color: "#ffffff",
                fontSize: 14,
                fontWeight: 500,
                minHeight: 44,
                border: "none",
                cursor: "default",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                gap: 8,
                transition: "background 0.25s ease",
              }}
            >
              {phase === "finishing" ? (
                <>
                  <RefreshCw
                    size={14}
                    style={{
                      transformOrigin: "center",
                      animation: "cc-spin 1.2s linear infinite",
                    }}
                  />
                  {t.finishing}
                </>
              ) : (
                t.primaryComplete
              )}
            </button>

            <p
              style={{
                marginTop: 8,
                marginBottom: 0,
                fontSize: 11,
                lineHeight: 1.5,
                color: "#8a847b",
              }}
            >
              {t.helpHint}
            </p>
          </div>
        </div>
      )}

      {showSuccess && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            borderRadius: 12,
            padding: "12px 14px",
            background: "rgba(34,197,94,0.08)",
            color: "#16a34a",
            border: "1px solid rgba(34,197,94,0.2)",
            fontSize: 14,
            fontWeight: 500,
            animation: "cc-fade-in 0.3s ease both",
          }}
        >
          <Check size={16} strokeWidth={2.5} />
          {DEMO_TEXTS.step1.success}
        </div>
      )}
    </Card>
  )
}

/* ── Step 2: Connect Concerto to Claude ──────────────────────────── */

function Step2Card({ phase }: { phase: "ready" | "waiting" }) {
  const t = DEMO_TEXTS.step2
  return (
    <Card style={{ padding: "20px 22px" }}>
      <div style={{ marginBottom: 16 }}>
        <h2
          style={{
            margin: 0,
            fontSize: 19,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            color: "#191919",
          }}
        >
          {t.title}
        </h2>
        <p
          style={{
            marginTop: 6,
            marginBottom: 0,
            fontSize: 13,
            lineHeight: 1.55,
            color: "#8a847b",
          }}
        >
          {t.blurb}
        </p>
      </div>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          gap: 8,
          width: "100%",
          minHeight: 46,
          borderRadius: 12,
          background: "#cc785c",
          color: "#ffffff",
          fontSize: 14,
          fontWeight: 600,
          boxShadow: "0 1px 2px rgba(204,120,92,0.25)",
        }}
      >
        {t.primary}
        <ExternalLink size={14} />
      </div>

      <div
        style={{
          marginTop: 12,
          fontSize: 12.5,
          lineHeight: 1.5,
          color: "#191919",
        }}
      >
        <span style={{ color: "#8a847b" }}>In Claude:</span>{" "}
        <strong style={{ fontWeight: 600 }}>Add</strong> · then{" "}
        <strong style={{ fontWeight: 600 }}>Connect</strong>
      </div>

      {phase === "waiting" && (
        <div
          style={{
            marginTop: 14,
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "10px 12px",
            borderRadius: 12,
            background: "#faf9f5",
            border: "1px solid #f3efe5",
            animation: "cc-fade-in 0.3s ease both",
          }}
        >
          <RefreshCw
            size={14}
            style={{
              flexShrink: 0,
              color: "#cc785c",
              animation: "cc-spin 1.2s linear infinite",
            }}
          />
          <p
            style={{
              margin: 0,
              fontSize: 12.5,
              fontWeight: 500,
              color: "#191919",
              lineHeight: 1.4,
            }}
          >
            {t.waiting}
          </p>
        </div>
      )}
    </Card>
  )
}

/* ── Step 3: You're all set ──────────────────────────────────────── */

function Step3Card() {
  const t = DEMO_TEXTS.step3
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "stretch",
        gap: 12,
        animation: "cc-fade-up 0.32s cubic-bezier(0.22,1,0.36,1) both",
      }}
    >
      {/* Headline + GitHub action */}
      <div>
        <h2
          style={{
            margin: 0,
            fontSize: 18,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            color: "#191919",
            lineHeight: 1.25,
          }}
        >
          {t.title}
        </h2>
        <p
          style={{
            marginTop: 4,
            marginBottom: 0,
            fontSize: 13,
            lineHeight: 1.5,
            color: "#8a847b",
          }}
        >
          {t.blurb}
        </p>

        <div
          style={{
            marginTop: 14,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 10,
            width: "100%",
            minHeight: 46,
            borderRadius: 12,
            background: "#24292f",
            color: "#ffffff",
            fontSize: 14,
            fontWeight: 600,
          }}
        >
          <Github size={16} />
          {t.githubButton}
        </div>
      </div>

      {/* You're all set callout */}
      <div
        style={{
          marginTop: 8,
          paddingTop: 14,
          borderTop: "1px solid #efeae0",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          textAlign: "center",
        }}
      >
        <div
          style={{
            width: 44,
            height: 44,
            borderRadius: "50%",
            background:
              "radial-gradient(circle at 50% 45%, rgba(204,120,92,0.18) 0%, rgba(204,120,92,0.06) 60%, transparent 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            marginBottom: 10,
          }}
        >
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: "50%",
              background: "#cc785c",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Check size={16} color="#ffffff" strokeWidth={3} />
          </div>
        </div>
        <h3
          style={{
            margin: 0,
            fontSize: 17,
            fontWeight: 600,
            letterSpacing: "-0.01em",
            color: "#191919",
          }}
        >
          {t.setHeadline}
        </h3>
        <p
          style={{
            marginTop: 4,
            marginBottom: 10,
            fontSize: 12.5,
            lineHeight: 1.5,
            color: "#8a847b",
            maxWidth: 320,
          }}
        >
          {t.setBlurb}
        </p>

        <div
          style={{
            width: "100%",
            borderRadius: 12,
            background: "#faf9f5",
            border: "1px solid #f3efe5",
            padding: "10px 12px",
            textAlign: "left",
          }}
        >
          <p
            style={{
              margin: 0,
              fontSize: 10.5,
              fontWeight: 600,
              letterSpacing: "0.07em",
              color: "#8a847b",
            }}
          >
            {t.promptLabel}
          </p>
          <p
            style={{
              marginTop: 4,
              marginBottom: 0,
              fontFamily:
                "'SF Mono', 'JetBrains Mono', 'Fira Code', Consolas, monospace",
              fontSize: 13,
              color: "#191919",
            }}
          >
            {t.promptText}
          </p>
        </div>
      </div>
    </div>
  )
}

/* ── Browser chrome shell (mac title bar + concerto URL) ─────────── */

function DemoShell({
  fading,
  cursor,
  containerRef,
  children,
}: {
  fading: boolean
  cursor: CursorState
  containerRef: { current: HTMLDivElement | null }
  children: React.ReactNode
}) {
  return (
    <div
      role="img"
      aria-label="Concerto demo: the real onboarding wizard"
      className="relative w-full select-none"
      style={{
        opacity: fading ? 0 : 1,
        transition: "opacity 0.6s ease",
      }}
    >
      <div
        style={{
          borderRadius: 12,
          overflow: "hidden",
          border: "1px solid rgba(25,25,25,0.10)",
          boxShadow:
            "0 0 0 1px rgba(25,25,25,0.04), 0 8px 32px rgba(25,25,25,0.10), 0 32px 64px rgba(25,25,25,0.06)",
          background: "#ffffff",
        }}
      >
        {/* macOS title bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "7px 12px",
            background: "#ece8e1",
            borderBottom: "1px solid rgba(25,25,25,0.08)",
          }}
        >
          <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
            {["#ff5f57", "#ffbd2e", "#28c840"].map((c) => (
              <span
                key={c}
                style={{
                  display: "block",
                  width: 10,
                  height: 10,
                  borderRadius: "50%",
                  background: c,
                }}
              />
            ))}
          </div>
          <div
            style={{
              flex: 1,
              margin: "0 8px",
              borderRadius: 5,
              background: "#faf9f5",
              color: "#8a847b",
              fontSize: 10.5,
              padding: "3px 10px",
              textAlign: "center",
              letterSpacing: "0.01em",
              border: "1px solid rgba(25,25,25,0.06)",
            }}
          >
            concerto.run/dashboard
          </div>
          <div style={{ width: 44, flexShrink: 0 }} />
        </div>

        {/* Content + cursor layer */}
        <div
          ref={containerRef}
          style={{
            position: "relative",
            background: "#faf9f5",
            height: 468,
            overflow: "hidden",
          }}
        >
          {children}
          <MouseCursor x={cursor.x} y={cursor.y} clicking={cursor.clicking} />
        </div>
      </div>
    </div>
  )
}

/* ── Inner wizard scroll area ────────────────────────────────────── */

function WizardBody({ state }: { state: DemoState }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
      }}
    >
      <DashHeader />
      <main
        style={{
          flex: 1,
          padding: "22px 18px 18px",
          maxWidth: 520,
          width: "100%",
          margin: "0 auto",
          overflow: "hidden",
        }}
      >
        <div style={{ marginBottom: 20 }}>
          <ProgressBar step={state.step} />
        </div>

        {state.step === 1 && (
          <Step1Card phase={state.signIn} codeChars={state.codeChars} />
        )}
        {state.step === 2 && <Step2Card phase={state.connectPhase} />}
        {state.step === 3 && <Step3Card />}
      </main>
    </div>
  )
}

/* ── Animated demo (timed state transitions) ─────────────────────── */

function AnimatedDemo() {
  const [state, setState] = useState<DemoState>(INITIAL)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])
  const containerRef = useRef<HTMLDivElement>(null)
  const runLoopRef = useRef<() => void>(() => {})

  const cursor = useCursorAnimation(
    CURSOR_WAYPOINTS,
    DEMO_TIMINGS.loopDuration,
    containerRef,
  )

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])

  const add = useCallback((fn: () => void, ms: number) => {
    timers.current.push(setTimeout(fn, ms))
  }, [])

  const runLoop = useCallback(() => {
    clearTimers()
    setState(INITIAL)
    const T = DEMO_TIMINGS
    const code = DEMO_TEXTS.step1.codeTyped

    // ── Step 1: sign-in flow ────────────────────────────────────
    // Click "Sign in with Claude" → briefly show "Preparing…"
    add(() => setState((s) => ({ ...s, signIn: "starting" })), T.signInClickAt)

    // Card morphs to the OAuth code-paste form
    add(
      () => setState((s) => ({ ...s, signIn: "awaiting_code" })),
      T.awaitingCodeAt,
    )

    // Type the pasted code character by character
    for (let c = 1; c <= code.length; c++) {
      const cap = c
      add(
        () => setState((s) => ({ ...s, codeChars: cap })),
        T.codeTypeStartAt + cap * T.streamMs,
      )
    }
    // After typing finishes, mark the "code_typed" phase so the submit
    // button switches from disabled-look to active peach.
    add(
      () =>
        setState((s) => ({
          ...s,
          codeChars: code.length,
          signIn: "code_typed",
        })),
      T.codeTypeEndAt,
    )

    // Click "Complete sign-in" → finishing spinner
    add(
      () => setState((s) => ({ ...s, signIn: "finishing" })),
      T.finishingAt,
    )
    // Green confirmation
    add(() => setState((s) => ({ ...s, signIn: "success" })), T.successAt)

    // ── Step 2: connect flow ────────────────────────────────────
    add(
      () =>
        setState((s) => ({
          ...s,
          step: 2,
          signIn: "idle",
          codeChars: 0,
          connectPhase: "ready",
        })),
      T.step2AppearAt,
    )
    add(
      () => setState((s) => ({ ...s, connectPhase: "waiting" })),
      T.waitingAt,
    )

    // ── Step 3: you're all set ──────────────────────────────────
    add(
      () =>
        setState((s) => ({
          ...s,
          step: 3,
          connectPhase: "ready",
        })),
      T.step3AppearAt,
    )

    // Fade out, loop restart
    add(() => setState((s) => ({ ...s, fading: true })), T.fadeOutAt)
    add(() => runLoopRef.current(), T.loopDuration)
  }, [clearTimers, add])

  useEffect(() => {
    runLoopRef.current = runLoop
  }, [runLoop])

  useEffect(() => {
    const t = setTimeout(() => runLoop(), 250)
    return () => {
      clearTimeout(t)
      clearTimers()
    }
  }, [runLoop, clearTimers])

  return (
    <>
      <style>{CSS_KEYFRAMES}</style>
      <DemoShell
        fading={state.fading}
        cursor={cursor}
        containerRef={containerRef}
      >
        <WizardBody state={state} />
      </DemoShell>
    </>
  )
}

/* ── Static fallback (prefers-reduced-motion) ─────────────────────── */

function StaticFallback() {
  // Show the final, most reassuring frame: step 3 "You're all set".
  const finalState: DemoState = {
    step: 3,
    signIn: "idle",
    codeChars: 0,
    connectPhase: "ready",
    fading: false,
  }
  return (
    <>
      <style>{CSS_KEYFRAMES}</style>
      <DemoShell
        fading={false}
        cursor={{ x: -100, y: -100, clicking: false }}
        containerRef={{ current: null }}
      >
        <WizardBody state={finalState} />
      </DemoShell>
    </>
  )
}

/* ── Export ────────────────────────────────────────────────────────── */

export function HeroClaudeDemo() {
  const reduced = usePrefersReducedMotion()
  return reduced ? <StaticFallback /> : <AnimatedDemo />
}
