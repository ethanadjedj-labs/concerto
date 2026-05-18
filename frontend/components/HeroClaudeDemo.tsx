"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import {
  Menu,
  ChevronDown,
  ChevronRight,
  Check,
  Search,
  MessageSquare,
  BookOpen,
  Briefcase,
  Code2,
  Star,
  Clock,
} from "lucide-react"
import { DEMO_TEXTS, DEMO_TIMINGS, CURSOR_WAYPOINTS, type CursorWaypoint } from "./hero-claude-demo-script"

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

interface CursorState {
  x: number      // px from left of container
  y: number      // px from top of container
  clicking: boolean
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

/* ── CSS keyframes ─────────────────────────────────────────────── */

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
    from { opacity: 0; transform: translateY(5px) }
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
  @keyframes cc-cursor-click {
    0%   { transform: scale(1)    }
    40%  { transform: scale(0.82) }
    100% { transform: scale(1)    }
  }
  @keyframes cc-ripple {
    0%   { transform: scale(0); opacity: 0.45 }
    100% { transform: scale(2.8); opacity: 0  }
  }
  @keyframes cc-thinking-dot {
    0%, 60%, 100% { opacity: 0.18; transform: scale(0.85) }
    30%           { opacity: 1;    transform: scale(1)    }
  }
`

/* ── Animated mouse cursor ─────────────────────────────────────── */

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
        // Smooth movement with realistic ease — no linear snapping
        transition: "left 0.38s cubic-bezier(0.25,0.46,0.45,0.94), top 0.38s cubic-bezier(0.25,0.46,0.45,0.94)",
        willChange: "left, top",
      }}
    >
      {/* Click ripple */}
      {clicking && (
        <div
          style={{
            position: "absolute",
            left: 4,
            top: 4,
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: "rgba(255,255,255,0.22)",
            animation: "cc-ripple 0.42s cubic-bezier(0.22,1,0.36,1) both",
          }}
        />
      )}
      {/* macOS arrow cursor SVG */}
      <svg
        width="20"
        height="22"
        viewBox="0 0 20 22"
        fill="none"
        style={{
          filter: "drop-shadow(0 1px 3px rgba(0,0,0,0.55)) drop-shadow(0 0 1px rgba(0,0,0,0.8))",
          animation: clicking ? "cc-cursor-click 0.22s ease both" : "none",
        }}
      >
        {/* Outer black stroke */}
        <path
          d="M3 1L3 17.5L6.8 13.8L9.6 19.6L11.8 18.6L9.1 12.8L14 12.8L3 1Z"
          fill="#111"
          stroke="#111"
          strokeWidth="2"
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {/* White fill */}
        <path
          d="M3 1L3 17.5L6.8 13.8L9.6 19.6L11.8 18.6L9.1 12.8L14 12.8L3 1Z"
          fill="white"
          strokeWidth="0"
        />
      </svg>
    </div>
  )
}

/* ── Claude avatar ─────────────────────────────────────────────── */

function ClaudeAvatar() {
  return (
    <div
      style={{
        width: 24,
        height: 24,
        borderRadius: "50%",
        background: "linear-gradient(135deg, #cc785c 0%, #b8604a 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        marginTop: 1,
      }}
    >
      {/* Anthropic logo-ish shape: simplified A */}
      <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
        <path
          d="M6 2L9.5 9.5H8L6.8 7H5.2L4 9.5H2.5L6 2ZM6 4.2L5.6 6H6.4L6 4.2Z"
          fill="white"
          fillRule="evenodd"
        />
      </svg>
    </div>
  )
}

/* ── Spinner matching real Claude tool call spinner ─────────────── */

function ToolSpinner() {
  const dots = Array.from({ length: 8 }, (_, i) => {
    const angle = (i / 8) * 2 * Math.PI - Math.PI / 2
    const delay = `${(i / 8) * 0.9}s`
    return { x: 8 + 5.5 * Math.cos(angle), y: 8 + 5.5 * Math.sin(angle), delay }
  })
  return (
    <div style={{ position: "relative", width: 16, height: 16, flexShrink: 0 }}>
      {dots.map((d, i) => (
        <div
          key={i}
          style={{
            position: "absolute",
            left: d.x - 1.2,
            top:  d.y - 1.2,
            width: 2.4,
            height: 2.4,
            borderRadius: "50%",
            background: "#cc785c",
            animation: `cc-spin 0.9s linear ${d.delay} infinite`,
          }}
        />
      ))}
    </div>
  )
}

/* ── Tool call chip — real Claude collapsible block style ────────── */

function ToolChip({ label, state }: { label: string; state: ChipState }) {
  if (state === "hidden") return null
  const isActive = state === "active"

  return (
    <div
      style={{
        animation: "cc-fade-up 0.22s cubic-bezier(0.22,1,0.36,1) both",
        marginLeft: 32, // indent under avatar
      }}
    >
      <div
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 7,
          padding: "4px 10px 4px 8px",
          background: isActive ? "rgba(204,120,92,0.07)" : "rgba(255,255,255,0.03)",
          border: `1px solid ${isActive ? "rgba(204,120,92,0.22)" : "rgba(255,255,255,0.08)"}`,
          borderRadius: 6,
          cursor: "default",
          maxWidth: "100%",
          transition: "background 0.35s ease, border-color 0.35s ease",
          animation: isActive ? "cc-chip-pulse 2.8s ease-in-out infinite" : "none",
        }}
      >
        {isActive ? <ToolSpinner /> : (
          <div
            style={{
              width: 16,
              height: 16,
              borderRadius: "50%",
              background: "rgba(204,120,92,0.15)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              flexShrink: 0,
              animation: "cc-fade-in 0.18s ease both",
            }}
          >
            <Check size={9} color="#cc785c" strokeWidth={2.5} />
          </div>
        )}

        <span
          style={{
            fontFamily: "'SF Mono', 'Fira Code', 'Cascadia Code', 'Consolas', monospace",
            fontSize: 11.5,
            color: isActive ? "#d4a088" : "#8a8275",
            letterSpacing: "0.01em",
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
            maxWidth: 260,
          }}
        >
          {label}
        </span>

        <ChevronRight
          size={11}
          color="#524d44"
          strokeWidth={1.8}
          style={{ flexShrink: 0, marginLeft: 2 }}
        />
      </div>
    </div>
  )
}

/* ── Thinking dots (shown briefly before prose 1 starts) ─────────── */

function ThinkingDots({ visible }: { visible: boolean }) {
  if (!visible) return null
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 4,
        marginLeft: 32,
        paddingTop: 2,
        animation: "cc-fade-in 0.2s ease both",
      }}
    >
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#524d44",
            animation: `cc-thinking-dot 1.2s ease-in-out ${i * 0.18}s infinite`,
          }}
        />
      ))}
    </div>
  )
}

/* ── Assistant prose — no fake glow, correct real Claude styling ──── */

function AssistantProse({ chars, text }: { chars: number; text: string }) {
  if (chars === 0) return null
  const displayed = text.slice(0, chars)
  const streaming = chars < text.length

  return (
    <div style={{ display: "flex", gap: 8, alignItems: "flex-start" }}>
      <ClaudeAvatar />
      <div
        style={{
          fontSize: 13.5,
          lineHeight: 1.65,
          color: "#ece8e1",
          letterSpacing: "-0.003em",
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          animation: "cc-fade-in 0.18s ease both",
          flex: 1,
          minWidth: 0,
        }}
      >
        {displayed}
        {streaming && (
          <span
            style={{
              display: "inline-block",
              width: 1.5,
              height: "1.1em",
              background: "#cc785c",
              verticalAlign: "text-bottom",
              marginLeft: 1,
              animation: "cc-blink 0.75s step-end infinite",
              borderRadius: 1,
            }}
          />
        )}
      </div>
    </div>
  )
}

/* ── User message bubble ──────────────────────────────────────────── */

function UserMessage({ visible }: { visible: boolean }) {
  if (!visible) return null
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "flex-end",
        animation: "cc-fade-up 0.22s cubic-bezier(0.22,1,0.36,1) both",
        paddingRight: 2,
      }}
    >
      <div
        style={{
          maxWidth: "78%",
          background: "#2c2a27",
          border: "1px solid rgba(255,255,255,0.08)",
          borderRadius: "18px 18px 4px 18px",
          padding: "8px 13px",
          fontSize: 13.5,
          lineHeight: 1.55,
          color: "#ece8e1",
          letterSpacing: "-0.003em",
          fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        }}
      >
        {DEMO_TEXTS.userMessage}
      </div>
    </div>
  )
}

/* ── Sidebar ──────────────────────────────────────────────────────── */

const SIDEBAR_ICONS = [
  { Icon: Search,       active: false },
  { Icon: MessageSquare,active: true  },  // active conversation indicator
  { Icon: BookOpen,     active: false },
  { Icon: Briefcase,    active: false },
  { Icon: Code2,        active: false },
  { Icon: Star,         active: false },
  { Icon: Clock,        active: false },
] as const

function Sidebar() {
  return (
    <div
      style={{
        width: 56,
        flexShrink: 0,
        background: "#1a1917",
        borderRight: "1px solid rgba(255,255,255,0.05)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "10px 0 10px",
        gap: 0,
      }}
    >
      <Menu size={17} color="#4d4840" strokeWidth={1.5} style={{ marginBottom: 18 }} />

      <div style={{ display: "flex", flexDirection: "column", gap: 1, width: "100%", padding: "0 8px" }}>
        {SIDEBAR_ICONS.map(({ Icon, active }, i) => (
          <div
            key={i}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              width: "100%",
              height: 34,
              borderRadius: 7,
              background: active ? "rgba(255,255,255,0.07)" : "transparent",
              cursor: "default",
            }}
          >
            <Icon
              size={16}
              color={active ? "#ece8e1" : "#4d4840"}
              strokeWidth={active ? 1.8 : 1.5}
            />
          </div>
        ))}
      </div>

      <div style={{ flex: 1 }} />

      {/* User avatar */}
      <div
        style={{
          width: 26,
          height: 26,
          borderRadius: "50%",
          background: "#cc785c",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          fontSize: 10.5,
          fontWeight: 600,
          color: "#1f1e1c",
          letterSpacing: "-0.02em",
          cursor: "default",
        }}
      >
        E
      </div>
    </div>
  )
}

/* ── Top bar ───────────────────────────────────────────────────────── */

function TopBar() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "6px 14px",
        borderBottom: "1px solid rgba(255,255,255,0.05)",
        flexShrink: 0,
        minHeight: 38,
      }}
    >
      {/* Model selector pill */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 5,
          padding: "3px 9px",
          borderRadius: 7,
          border: "1px solid rgba(255,255,255,0.07)",
          cursor: "default",
          background: "transparent",
        }}
      >
        {/* Claude logomark (simplified) */}
        <div
          style={{
            width: 14,
            height: 14,
            borderRadius: "50%",
            background: "linear-gradient(135deg, #cc785c 0%, #b8604a 100%)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexShrink: 0,
          }}
        >
          <svg width="8" height="8" viewBox="0 0 8 8" fill="none">
            <path d="M4 1L6.5 6.5H5.2L4.6 5H3.4L2.8 6.5H1.5L4 1ZM4 2.8L3.7 4H4.3L4 2.8Z"
              fill="white" fillRule="evenodd" />
          </svg>
        </div>
        <span style={{ color: "#ece8e1", fontSize: 12, fontWeight: 500, letterSpacing: "-0.01em" }}>
          Claude
        </span>
        <span style={{ color: "#6b6560", fontSize: 12 }}>Opus 4.7</span>
        <ChevronDown size={10} color="#4d4840" strokeWidth={1.8} />
      </div>

      {/* Right icons */}
      <div style={{ display: "flex", gap: 12, alignItems: "center" }}>
        {/* Share icon */}
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" opacity={0.3}>
          <path d="M7.5 2L11.5 5.5M7.5 2L3.5 5.5M7.5 2V10.5M1.5 11V13.5H13.5V11"
            stroke="#8a8275" strokeWidth="1.3" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        {/* More/ellipsis */}
        <svg width="15" height="15" viewBox="0 0 15 15" fill="none" opacity={0.3}>
          <circle cx="3.5"  cy="7.5" r="1.2" fill="#8a8275" />
          <circle cx="7.5"  cy="7.5" r="1.2" fill="#8a8275" />
          <circle cx="11.5" cy="7.5" r="1.2" fill="#8a8275" />
        </svg>
      </div>
    </div>
  )
}

/* ── Input area ─────────────────────────────────────────────────────── */

function InputArea({ phase }: { phase: "pre-send" | "post-send" | "ready" }) {
  // phase: pre-send = cursor blinking in box (user about to type)
  //        post-send = empty + placeholder (message sent)
  //        ready = cursor in input again (end of loop, ready for next)
  const showTypingCursor = phase === "pre-send" || phase === "ready"
  const showPlaceholder  = phase === "post-send"

  return (
    <div style={{ padding: "4px 12px 12px", flexShrink: 0 }}>
      {/* Attachment / style pills row above input */}
      <div style={{ display: "flex", gap: 6, marginBottom: 6, paddingLeft: 2 }}>
        {["No file", "Default style"].map((label) => (
          <div
            key={label}
            style={{
              display: "flex",
              alignItems: "center",
              gap: 4,
              padding: "2px 8px",
              borderRadius: 99,
              border: "1px solid rgba(255,255,255,0.07)",
              fontSize: 11,
              color: "#524d44",
              cursor: "default",
            }}
          >
            {label}
            <ChevronDown size={9} color="#3d3830" strokeWidth={1.5} />
          </div>
        ))}
      </div>

      <div
        style={{
          borderRadius: 12,
          background: "#252320",
          border: "1px solid rgba(255,255,255,0.07)",
          padding: "10px 12px 10px",
          display: "flex",
          flexDirection: "column",
          gap: 8,
          boxShadow: "inset 0 1px 2px rgba(0,0,0,0.12)",
        }}
      >
        {/* Text area */}
        <div
          style={{
            fontSize: 13.5,
            color: showPlaceholder ? "#524d44" : "#ece8e1",
            lineHeight: 1.55,
            minHeight: 36,
            letterSpacing: "-0.003em",
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
          }}
        >
          {showPlaceholder ? (
            "How can Claude help you today?"
          ) : showTypingCursor ? (
            <span>
              {phase === "ready" ? "Run end-to-end tests" : "Build and deploy this landing page."}
              <span
                style={{
                  display: "inline-block",
                  width: 1.5,
                  height: "1.1em",
                  background: "#cc785c",
                  verticalAlign: "text-bottom",
                  marginLeft: 1,
                  animation: "cc-blink 1.05s step-end infinite",
                  borderRadius: 1,
                }}
              />
            </span>
          ) : null}
        </div>

        {/* Bottom toolbar */}
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            {/* + button */}
            <div
              style={{
                width: 26,
                height: 26,
                borderRadius: 6,
                border: "1px solid rgba(255,255,255,0.07)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#524d44",
                fontSize: 16,
                fontWeight: 300,
                cursor: "default",
                lineHeight: 1,
              }}
            >
              +
            </div>
            {/* Search web */}
            <div style={{ display: "flex", alignItems: "center", gap: 3, cursor: "default", opacity: 0.5 }}>
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none">
                <circle cx="5.5" cy="5.5" r="4" stroke="#524d44" strokeWidth="1.2" />
                <path d="M9 9L11.5 11.5" stroke="#524d44" strokeWidth="1.2" strokeLinecap="round" />
              </svg>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            {/* Mic */}
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" opacity={0.35}>
              <rect x="4.5" y="1" width="5" height="7" rx="2.5" stroke="#8a8275" strokeWidth="1.1" />
              <path d="M2.5 7c0 2.48 2.02 4.5 4.5 4.5S11.5 9.48 11.5 7M7 11.5V13M5 13h4"
                stroke="#8a8275" strokeWidth="1.1" strokeLinecap="round" />
            </svg>
            {/* Send button */}
            <div
              style={{
                width: 26,
                height: 26,
                borderRadius: 7,
                background: phase === "pre-send" ? "rgba(204,120,92,0.18)" : "rgba(255,255,255,0.05)",
                border: phase === "pre-send" ? "1px solid rgba(204,120,92,0.3)" : "1px solid rgba(255,255,255,0.06)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                cursor: "default",
                transition: "background 0.3s ease, border-color 0.3s ease",
              }}
            >
              <svg width="11" height="11" viewBox="0 0 11 11" fill="none">
                <path d="M5.5 9.5V1.5M5.5 1.5L2.5 4.5M5.5 1.5L8.5 4.5"
                  stroke={phase === "pre-send" ? "#cc785c" : "#524d44"}
                  strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

/* ── Browser chrome shell ─────────────────────────────────────────── */

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
      aria-label="Concerto demo: Claude spawning parallel sessions via MCP"
      className="relative w-full select-none"
      style={{
        opacity: fading ? 0 : 1,
        transition: "opacity 0.7s ease",
      }}
    >
      <div
        style={{
          borderRadius: 12,
          overflow: "hidden",
          border: "1px solid rgba(255,255,255,0.07)",
          boxShadow:
            "0 0 0 1px rgba(0,0,0,0.18), 0 8px 32px rgba(0,0,0,0.32), 0 32px 64px rgba(0,0,0,0.18)",
        }}
      >
        {/* macOS title bar */}
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
          {/* Traffic lights */}
          <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
            {["#ff5f57", "#ffbd2e", "#28c840"].map((c) => (
              <span
                key={c}
                style={{ display: "block", width: 10, height: 10, borderRadius: "50%", background: c }}
              />
            ))}
          </div>
          {/* URL bar */}
          <div
            style={{
              flex: 1,
              margin: "0 8px",
              borderRadius: 5,
              background: "#1c1b19",
              color: "#524d44",
              fontSize: 10.5,
              padding: "2.5px 10px",
              textAlign: "center",
              letterSpacing: "0.01em",
            }}
          >
            claude.ai/chat
          </div>
          <div style={{ width: 44, flexShrink: 0 }} />
        </div>

        {/* Content + cursor layer */}
        <div
          ref={containerRef}
          style={{
            display: "flex",
            height: 468,
            background: "#1f1e1c",
            position: "relative",
          }}
        >
          {children}
          <MouseCursor x={cursor.x} y={cursor.y} clicking={cursor.clicking} />
        </div>
      </div>
    </div>
  )
}

/* ── Cursor animation engine ──────────────────────────────────────── */

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

    function lerp(a: number, b: number, t: number) {
      return a + (b - a) * t
    }

    // Cubic-bezier ease-out approximation for smooth deceleration
    function easeOut(t: number) {
      return 1 - Math.pow(1 - t, 3)
    }

    function tick(now: number) {
      if (cancelled) return
      if (!startTimeRef.current) startTimeRef.current = now

      const elapsed = (now - startTimeRef.current) % loopDuration
      const { w, h } = getContainerSize()

      // Find surrounding waypoints
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

      // Click: show clicking state within 120ms window around click waypoints
      const isClicking = waypoints.some(
        (wp) => wp.action === "click" && Math.abs(elapsed - wp.t) < 120
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

/* ── Animated demo ─────────────────────────────────────────────────── */

function AnimatedDemo() {
  const [state, setState] = useState<DemoState>(INITIAL)
  const [inputPhase, setInputPhase] = useState<"pre-send" | "post-send" | "ready">("pre-send")
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const runLoopRef = useRef<() => void>(() => {})

  const cursor = useCursorAnimation(CURSOR_WAYPOINTS, DEMO_TIMINGS.loopDuration, containerRef)

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
    setInputPhase("pre-send")

    const T = DEMO_TIMINGS
    const texts = DEMO_TEXTS

    // T=0: send — input clears, user message appears
    add(() => {
      setState((s) => ({ ...s, userVisible: true }))
      setInputPhase("post-send")
    }, T.userMessageAt)

    // T=1s: stream prose 1
    for (let c = 1; c <= texts.assistantProse1.length; c++) {
      const cap = c
      add(() => {
        setState((s) => ({ ...s, prose1Chars: cap }))
        if (cap === texts.assistantProse1.length) scrollBottom()
      }, T.prose1At + cap * T.streamMs)
    }

    // T=4s: chip 1
    add(() => {
      setState((s) => ({ ...s, chip1: "active" }))
      scrollBottom()
    }, T.chip1At)

    // T=6s: chip 2 — parallel WOW moment
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

    // T=13s: chip 3
    add(() => {
      setState((s) => ({ ...s, chip3: "active" }))
      scrollBottom()
    }, T.chip3At)

    // T=14.5s: chip 3 complete
    add(() => setState((s) => ({ ...s, chip3: "complete" })), T.chip3CompleteAt)

    // T=15s: stream prose 3
    for (let c = 1; c <= texts.assistantProse3.length; c++) {
      const cap = c
      add(() => {
        setState((s) => ({ ...s, prose3Chars: cap }))
        if (cap === texts.assistantProse3.length) {
          scrollBottom()
          setInputPhase("ready")
        }
      }, T.prose3At + cap * T.streamMs)
    }

    // T=17s: fade out
    add(() => setState((s) => ({ ...s, fading: true })), T.fadeOutAt)

    // T=18s: loop restart
    add(() => runLoopRef.current(), T.loopDuration)
  }, [clearTimers, add, scrollBottom])

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

  // Show thinking dots between user message and prose starting
  const showThinking = userVisible && prose1Chars === 0

  return (
    <>
      <style>{CSS_KEYFRAMES}</style>
      <DemoShell fading={fading} cursor={cursor} containerRef={containerRef}>
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
              padding: "16px 18px 8px",
              display: "flex",
              flexDirection: "column",
              gap: 12,
              scrollbarWidth: "none",
            }}
          >
            <UserMessage visible={userVisible} />
            <ThinkingDots visible={showThinking} />
            <AssistantProse chars={prose1Chars} text={DEMO_TEXTS.assistantProse1} />
            <ToolChip label="concerto__start_claude_session" state={chip1} />
            <ToolChip label="concerto__start_claude_session" state={chip2} />
            <AssistantProse chars={prose2Chars} text={DEMO_TEXTS.assistantProse2} />
            <ToolChip label="concerto__get_claude_session" state={chip3} />
            <AssistantProse chars={prose3Chars} text={DEMO_TEXTS.assistantProse3} />
          </div>
          <InputArea phase={inputPhase} />
        </div>
      </DemoShell>
    </>
  )
}

/* ── Static fallback (prefers-reduced-motion) ─────────────────────── */

function StaticFallback() {
  const texts = DEMO_TEXTS
  return (
    <>
      <style>{CSS_KEYFRAMES}</style>
      <DemoShell
        fading={false}
        cursor={{ x: 0, y: 0, clicking: false }}
        containerRef={{ current: null }}
      >
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
              padding: "16px 18px 8px",
              display: "flex",
              flexDirection: "column",
              gap: 12,
              scrollbarWidth: "none",
            }}
          >
            <UserMessage visible={true} />
            <AssistantProse chars={texts.assistantProse1.length} text={texts.assistantProse1} />
            <ToolChip label="concerto__start_claude_session" state="complete" />
            <ToolChip label="concerto__start_claude_session" state="complete" />
            <AssistantProse chars={texts.assistantProse2.length} text={texts.assistantProse2} />
            <ToolChip label="concerto__get_claude_session" state="complete" />
            <AssistantProse chars={texts.assistantProse3.length} text={texts.assistantProse3} />
          </div>
          <InputArea phase="ready" />
        </div>
      </DemoShell>
    </>
  )
}

/* ── Export ────────────────────────────────────────────────────────── */

export function HeroClaudeDemo() {
  const reduced = usePrefersReducedMotion()
  return reduced ? <StaticFallback /> : <AnimatedDemo />
}
