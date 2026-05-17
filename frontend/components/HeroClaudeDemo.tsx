"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import {
  Menu,
  ChevronDown,
  ChevronRight,
  Check,
  Globe,
  Search,
  MessageSquare,
  MessageCircle,
  Briefcase,
  Code2,
  FolderClosed,
  Palette,
} from "lucide-react"
import { DEMO_TEXTS, DEMO_TIMINGS } from "./hero-claude-demo-script"

/* ── Types ────────────────────────────────────────────────────── */

type ChipState = "hidden" | "active" | "complete"

interface DemoState {
  userVisible: boolean
  prose1Chars: number
  chip1: ChipState
  chip2: ChipState
  prose2Chars: number
  chip3: ChipState
  prose3Chars: number
  fading: boolean
}

const INITIAL: DemoState = {
  userVisible: false,
  prose1Chars: 0,
  chip1: "hidden",
  chip2: "hidden",
  prose2Chars: 0,
  chip3: "hidden",
  prose3Chars: 0,
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

/* ── CSS keyframes (injected once into the shadow DOM) ─────────── */

const CSS_KEYFRAMES = `
  @keyframes cc-spin {
    0%   { opacity: 1 }
    100% { opacity: 0.12 }
  }
  @keyframes cc-chip-pulse {
    0%,100% {
      box-shadow: 0 0 0 1px rgba(204,120,92,0.14),
                  0 0  8px rgba(204,120,92,0.07);
    }
    50% {
      box-shadow: 0 0 0 1px rgba(204,120,92,0.32),
                  0 0 18px rgba(204,120,92,0.15);
    }
  }
  @keyframes cc-fade-up {
    from { opacity: 0; transform: translateY(6px) }
    to   { opacity: 1; transform: translateY(0)   }
  }
  @keyframes cc-fade-in {
    from { opacity: 0 }
    to   { opacity: 1 }
  }
  @keyframes cc-blink {
    0%,100% { opacity: 1 }
    50%     { opacity: 0 }
  }
`

/* ── Peach dot loader ─────────────────────────────────────────── */

function PeachDotLoader() {
  const dots = Array.from({ length: 12 }, (_, i) => {
    const angle = (i / 12) * 2 * Math.PI - Math.PI / 2
    return {
      x: 16 + 12 * Math.cos(angle) - 1.5,
      y: 16 + 12 * Math.sin(angle) - 1.5,
      delay: `${-(i / 12) * 1.5}s`,
    }
  })

  return (
    <div
      aria-hidden="true"
      style={{
        position: "relative",
        width: 32,
        height: 32,
        margin: "6px 0 2px",
        filter: "drop-shadow(0 0 4px rgba(204,120,92,0.50))",
      }}
    >
      {dots.map((dot, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: dot.x,
            top: dot.y,
            width: 3,
            height: 3,
            borderRadius: "50%",
            background: "#cc785c",
            animation: `cc-spin 1.5s linear ${dot.delay} infinite`,
          }}
        />
      ))}
    </div>
  )
}

/* ── Tool call chip ───────────────────────────────────────────── */

function ToolChip({ label, state }: { label: string; state: ChipState }) {
  if (state === "hidden") return null
  const isActive = state === "active"

  return (
    <div style={{ animation: "cc-fade-up 0.28s ease both" }}>
      <div
        style={{
          height: 36,
          padding: "0 12px",
          background: "rgba(255,255,255,0.02)",
          border: "1px solid rgba(255,255,255,0.06)",
          borderRadius: 8,
          display: "flex",
          alignItems: "center",
          gap: 10,
          animation: isActive ? "cc-chip-pulse 2.5s ease-in-out infinite" : "none",
          transition: "box-shadow 0.4s ease",
        }}
      >
        <Globe size={14} color="#8a8275" strokeWidth={1.5} />

        <span
          style={{
            flex: 1,
            color: "#f0ebe2",
            fontSize: 13,
            fontWeight: 400,
            letterSpacing: "-0.005em",
          }}
        >
          {label}
        </span>

        {/* Request badge */}
        <span
          style={{
            fontSize: 10,
            color: "#cc785c",
            border: "1px solid rgba(204,120,92,0.28)",
            background: "rgba(204,120,92,0.08)",
            borderRadius: 4,
            padding: "1px 6px",
            fontWeight: 500,
            letterSpacing: "0.01em",
            flexShrink: 0,
          }}
        >
          Request
        </span>

        {isActive ? (
          <ChevronRight size={13} color="#524d44" strokeWidth={1.5} />
        ) : (
          <Check
            size={13}
            color="#cc785c"
            strokeWidth={2}
            style={{ animation: "cc-fade-in 0.2s ease both" }}
          />
        )}
      </div>

      {isActive && <PeachDotLoader />}
    </div>
  )
}

/* ── Assistant prose (with peach glow) ───────────────────────── */

function AssistantProse({ chars, text }: { chars: number; text: string }) {
  if (chars === 0) return null
  const displayed = text.slice(0, chars)
  const streaming = chars < text.length

  return (
    <div
      style={{
        fontSize: 13,
        lineHeight: 1.68,
        color: "#f0ebe2",
        textShadow: "0 0 8px rgba(204,120,92,0.15)",
        animation: "cc-fade-up 0.3s ease both",
      }}
    >
      {displayed}
      {streaming && (
        <span
          style={{
            display: "inline-block",
            width: 2,
            height: "1em",
            background: "#f0ebe2",
            verticalAlign: "middle",
            marginLeft: 2,
            opacity: 0.55,
            animation: "cc-blink 0.8s step-end infinite",
          }}
        />
      )}
    </div>
  )
}

/* ── User message bubble ──────────────────────────────────────── */

function UserMessage({ visible }: { visible: boolean }) {
  if (!visible) return null
  return (
    <div
      style={{ display: "flex", justifyContent: "flex-end", animation: "cc-fade-up 0.28s ease both" }}
    >
      <div
        style={{
          maxWidth: "82%",
          background: "#2d2927",
          border: "1px solid rgba(255,255,255,0.07)",
          borderRadius: "18px 18px 4px 18px",
          padding: "9px 14px",
          fontSize: 13,
          lineHeight: 1.55,
          color: "#f0ebe2",
        }}
      >
        {DEMO_TEXTS.userMessage}
      </div>
    </div>
  )
}

/* ── Sidebar (64px, icon strip) ────────────────────────────────── */

const SIDEBAR_ICONS = [
  Search,
  MessageSquare,
  MessageCircle,
  Briefcase,
  Code2,
  FolderClosed,
  Palette,
] as const

function Sidebar() {
  return (
    <div
      style={{
        width: 64,
        flexShrink: 0,
        background: "#1a1917",
        borderRight: "1px solid rgba(255,255,255,0.06)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "12px 0 10px",
        overflow: "hidden",
      }}
    >
      {/* Hamburger */}
      <Menu size={18} color="#524d44" strokeWidth={1.5} />

      <div style={{ height: 18 }} />

      {/* Project header strip */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 3,
          padding: "5px 8px",
          borderRadius: 6,
          background: "rgba(255,255,255,0.03)",
          cursor: "default",
        }}
      >
        <span
          style={{
            fontSize: 9.5,
            color: "#8a8275",
            fontWeight: 500,
            letterSpacing: "0.01em",
            whiteSpace: "nowrap",
          }}
        >
          Concerto
        </span>
        <ChevronDown size={8} color="#524d44" strokeWidth={1.5} />
      </div>

      <div style={{ height: 18 }} />

      {/* Icon strip */}
      <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
        {SIDEBAR_ICONS.map((Icon, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: 36,
              height: 30,
              borderRadius: 6,
              cursor: "default",
            }}
          >
            <Icon
              size={16}
              color={i === 0 ? "#f0ebe2" : "#524d44"}
              strokeWidth={1.5}
            />
          </div>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {/* Avatar */}
      <div
        style={{
          width: 28,
          height: 28,
          borderRadius: "50%",
          background: "#cc785c",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 11,
          fontWeight: 600,
          color: "#1f1e1c",
          cursor: "default",
        }}
      >
        E
      </div>
    </div>
  )
}

/* ── Top bar ──────────────────────────────────────────────────── */

function TopBar() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "7px 14px",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        flexShrink: 0,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          padding: "3px 8px",
          borderRadius: 6,
          border: "1px solid rgba(255,255,255,0.07)",
          cursor: "default",
        }}
      >
        <span style={{ color: "#f0ebe2", fontSize: 12, fontWeight: 500 }}>
          Claude
        </span>
        <span style={{ color: "#8a8275", fontSize: 12 }}>Opus 4.7</span>
        <ChevronDown size={9} color="#524d44" strokeWidth={1.5} />
      </div>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        {/* Share */}
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" opacity={0.35}>
          <path
            d="M7 2L11 5.5M7 2L3 5.5M7 2V9.5M1.5 10.5V12.5H12.5V10.5"
            stroke="#8a8275"
            strokeWidth="1.3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {/* Settings */}
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" opacity={0.35}>
          <circle cx="7" cy="7" r="2.2" stroke="#8a8275" strokeWidth="1.2" />
          <path
            d="M7 2V3M7 11V12M2 7H3M11 7H12M3.2 3.2L3.9 3.9M10.1 10.1L10.8 10.8M3.2 10.8L3.9 10.1M10.1 3.9L10.8 3.2"
            stroke="#8a8275"
            strokeWidth="1.2"
            strokeLinecap="round"
          />
        </svg>
      </div>
    </div>
  )
}

/* ── Input area ───────────────────────────────────────────────── */

function InputArea({ showCursor }: { showCursor?: boolean }) {
  return (
    <div style={{ padding: "6px 12px 10px", flexShrink: 0 }}>
      <div
        style={{
          borderRadius: 16,
          background: "#2a2825",
          border: "1px solid rgba(255,255,255,0.07)",
          padding: "8px 10px",
          minHeight: 110,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Text surface */}
        <div
          style={{
            flex: 1,
            padding: "4px 4px 8px",
            fontSize: 13,
            color: "#8a8275",
            lineHeight: 1.55,
          }}
        >
          {showCursor ? (
            <span
              style={{
                display: "inline-block",
                width: 2,
                height: "1em",
                background: "#cc785c",
                verticalAlign: "middle",
                animation: "cc-blink 1s step-end infinite",
              }}
            />
          ) : (
            "Reply to Claude..."
          )}
        </div>

        {/* Bottom row: + button | Opus 4.7, mic, send */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <div
            style={{
              width: 27,
              height: 27,
              borderRadius: 6,
              border: "1px solid rgba(255,255,255,0.08)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#8a8275",
              fontSize: 17,
              fontWeight: 300,
              cursor: "default",
            }}
          >
            +
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                fontSize: 11,
                color: "#524d44",
                fontWeight: 500,
                letterSpacing: "0.01em",
              }}
            >
              Opus 4.7
            </span>
            {/* Microphone */}
            <svg width="15" height="15" viewBox="0 0 16 16" fill="none" opacity={0.38}>
              <rect x="5.5" y="1" width="5" height="8" rx="2.5" stroke="#8a8275" strokeWidth="1.2" />
              <path
                d="M3 8c0 2.76 2.24 5 5 5s5-2.24 5-5M8 13v2.5M5.5 15.5h5"
                stroke="#8a8275"
                strokeWidth="1.2"
                strokeLinecap="round"
              />
            </svg>
            {/* Send */}
            <div
              style={{
                width: 26,
                height: 26,
                borderRadius: 8,
                background: "rgba(255,255,255,0.06)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "default",
              }}
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                <path
                  d="M6 10V2M6 2L3 5M6 2L9 5"
                  stroke="#8a8275"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Browser chrome shell ─────────────────────────────────────── */

function DemoShell({
  fading,
  children,
}: {
  fading: boolean
  children: React.ReactNode
}) {
  return (
    <div
      role="img"
      aria-label="Concerto demo: Claude spawning parallel sessions via MCP"
      className="relative w-full select-none"
      style={{
        opacity: fading ? 0 : 1,
        transition: "opacity 0.65s ease",
      }}
    >
      <div
        style={{
          borderRadius: 12,
          overflow: "hidden",
          border: "1px solid rgba(255,255,255,0.08)",
          boxShadow:
            "0 0 0 1px rgba(0,0,0,0.12), 0 8px 32px rgba(0,0,0,0.28), 0 24px 48px rgba(0,0,0,0.14)",
        }}
      >
        {/* macOS chrome bar */}
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: 8,
            padding: "7px 12px",
            background: "#111110",
            borderBottom: "1px solid rgba(255,255,255,0.05)",
          }}
        >
          <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
            <span
              style={{
                display: "block",
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: "#ff5f57",
              }}
            />
            <span
              style={{
                display: "block",
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: "#ffbd2e",
              }}
            />
            <span
              style={{
                display: "block",
                width: 10,
                height: 10,
                borderRadius: "50%",
                background: "#28c840",
              }}
            />
          </div>
          <div
            style={{
              flex: 1,
              margin: "0 6px",
              borderRadius: 5,
              background: "#1c1b19",
              color: "#524d44",
              fontSize: 11,
              padding: "3px 10px",
              textAlign: "center",
            }}
          >
            claude.ai
          </div>
          <div style={{ width: 44 }} />
        </div>

        {/* Content area */}
        <div
          style={{
            display: "flex",
            height: 462,
            background: "#1f1e1c",
          }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}

/* ── Animated demo ─────────────────────────────────────────────── */

function AnimatedDemo() {
  const [state, setState] = useState<DemoState>(INITIAL)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  const runLoopRef = useRef<() => void>(() => {})

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])

  const add = useCallback((fn: () => void, ms: number) => {
    timers.current.push(setTimeout(fn, ms))
  }, [])

  const scrollBottom = useCallback(() => {
    requestAnimationFrame(() => {
      if (scrollRef.current)
        scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    })
  }, [])

  const runLoop = useCallback(() => {
    clearTimers()
    setState(INITIAL)

    const T = DEMO_TIMINGS
    const texts = DEMO_TEXTS

    // T=0: user message
    add(() => setState((s) => ({ ...s, userVisible: true })), T.userMessageAt)

    // T=1s: stream prose 1
    for (let c = 1; c <= texts.assistantProse1.length; c++) {
      const cap = c
      add(() => {
        setState((s) => ({ ...s, prose1Chars: cap }))
        if (cap === texts.assistantProse1.length) scrollBottom()
      }, T.prose1At + cap * T.streamMs)
    }

    // T=4s: chip 1 active
    add(() => {
      setState((s) => ({ ...s, chip1: "active" }))
      scrollBottom()
    }, T.chip1At)

    // T=6s: chip 2 active — parallel WOW moment
    add(() => {
      setState((s) => ({ ...s, chip2: "active" }))
      scrollBottom()
    }, T.chip2At)

    // T=9s: chip 1 complete
    add(() => setState((s) => ({ ...s, chip1: "complete" })), T.chip1CompleteAt)

    // T=10s: chip 2 complete
    add(() => setState((s) => ({ ...s, chip2: "complete" })), T.chip2CompleteAt)

    // T=11s: stream prose 2
    for (let c = 1; c <= texts.assistantProse2.length; c++) {
      const cap = c
      add(
        () => setState((s) => ({ ...s, prose2Chars: cap })),
        T.prose2At + cap * T.streamMs
      )
    }

    // T=13s: chip 3 active
    add(() => {
      setState((s) => ({ ...s, chip3: "active" }))
      scrollBottom()
    }, T.chip3At)

    // T=14.5s: chip 3 complete
    add(
      () => setState((s) => ({ ...s, chip3: "complete" })),
      T.chip3CompleteAt
    )

    // T=15s: stream prose 3
    for (let c = 1; c <= texts.assistantProse3.length; c++) {
      const cap = c
      add(() => {
        setState((s) => ({ ...s, prose3Chars: cap }))
        if (cap === texts.assistantProse3.length) scrollBottom()
      }, T.prose3At + cap * T.streamMs)
    }

    // T=17s: fade out
    add(() => setState((s) => ({ ...s, fading: true })), T.fadeOutAt)

    // T=18s: loop restart
    add(() => runLoopRef.current(), T.loopDuration)
  }, [clearTimers, add, scrollBottom])

  // Keep runLoopRef current so the scheduled restart always calls the latest version
  useEffect(() => {
    runLoopRef.current = runLoop
  }, [runLoop])

  useEffect(() => {
    const t = setTimeout(() => runLoop(), 300)
    return () => {
      clearTimeout(t)
      clearTimers()
    }
  }, [runLoop, clearTimers])

  const {
    userVisible,
    prose1Chars,
    chip1,
    chip2,
    prose2Chars,
    chip3,
    prose3Chars,
    fading,
  } = state

  const showCursor =
    prose3Chars > 0 && prose3Chars >= DEMO_TEXTS.assistantProse3.length

  return (
    <>
      <style>{CSS_KEYFRAMES}</style>
      <DemoShell fading={fading}>
        <Sidebar />
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            minWidth: 0,
          }}
        >
          <TopBar />
          <div
            ref={scrollRef}
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "14px 16px 6px",
              display: "flex",
              flexDirection: "column",
              gap: 11,
              scrollbarWidth: "none",
            }}
          >
            <UserMessage visible={userVisible} />
            <AssistantProse chars={prose1Chars} text={DEMO_TEXTS.assistantProse1} />
            <ToolChip label="Start claude session" state={chip1} />
            <ToolChip label="Start claude session" state={chip2} />
            <AssistantProse chars={prose2Chars} text={DEMO_TEXTS.assistantProse2} />
            <ToolChip label="Get claude session" state={chip3} />
            <AssistantProse chars={prose3Chars} text={DEMO_TEXTS.assistantProse3} />
          </div>
          <InputArea showCursor={showCursor} />
        </div>
      </DemoShell>
    </>
  )
}

/* ── Static fallback (prefers-reduced-motion) ─────────────────── */

function StaticFallback() {
  const texts = DEMO_TEXTS
  return (
    <>
      <style>{CSS_KEYFRAMES}</style>
      <DemoShell fading={false}>
        <Sidebar />
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            flex: 1,
            minWidth: 0,
          }}
        >
          <TopBar />
          <div
            style={{
              flex: 1,
              overflowY: "auto",
              padding: "14px 16px 6px",
              display: "flex",
              flexDirection: "column",
              gap: 11,
              scrollbarWidth: "none",
            }}
          >
            <UserMessage visible={true} />
            <AssistantProse
              chars={texts.assistantProse1.length}
              text={texts.assistantProse1}
            />
            <ToolChip label="Start claude session" state="complete" />
            <ToolChip label="Start claude session" state="complete" />
            <AssistantProse
              chars={texts.assistantProse2.length}
              text={texts.assistantProse2}
            />
            <ToolChip label="Get claude session" state="complete" />
            <AssistantProse
              chars={texts.assistantProse3.length}
              text={texts.assistantProse3}
            />
          </div>
          <InputArea showCursor={true} />
        </div>
      </DemoShell>
    </>
  )
}

/* ── Export ────────────────────────────────────────────────────── */

export function HeroClaudeDemo() {
  const reduced = usePrefersReducedMotion()
  return reduced ? <StaticFallback /> : <AnimatedDemo />
}
