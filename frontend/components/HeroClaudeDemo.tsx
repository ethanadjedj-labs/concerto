"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import {
  DEMO_TEXTS,
  DEMO_TIMINGS,
  CURSOR_WAYPOINTS,
  type CursorWaypoint,
} from "./hero-claude-demo-script"

/* ── Types ────────────────────────────────────────────────────── */

interface DemoState {
  userChars: number        // chars of user message visible in input
  messageSent: boolean     // message moved from input to chat history
  showThinking: boolean    // Claude thinking dots
  showIntro: boolean       // Claude's decompose intro text
  sessionCount: number     // 0..3 session cards visible
  session1Done: boolean
  session2Done: boolean
  session3Done: boolean
  showReport: boolean      // Claude's final summary
  fading: boolean
}

interface CursorState {
  x: number
  y: number
  clicking: boolean
}

const INITIAL: DemoState = {
  userChars: 0,
  messageSent: false,
  showThinking: false,
  showIntro: false,
  sessionCount: 0,
  session1Done: false,
  session2Done: false,
  session3Done: false,
  showReport: false,
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

/* ── CSS keyframes ────────────────────────────────────────────── */

const CSS_KEYFRAMES = `
  @keyframes cc-fade-in {
    from { opacity: 0 } to { opacity: 1 }
  }
  @keyframes cc-fade-up {
    from { opacity: 0; transform: translateY(8px) }
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
  @keyframes cc-dot-pulse {
    0%, 80%, 100% { transform: scale(0.5); opacity: 0.4 }
    40%           { transform: scale(1);   opacity: 1   }
  }
  @keyframes cc-session-in {
    from { opacity: 0; transform: translateX(-8px) }
    to   { opacity: 1; transform: translateX(0)    }
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

/* ── Cursor animation engine ────────────────────────────────────── */

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

/* ── Claude avatar circle ───────────────────────────────────────── */

function ClaudeAvatar({ size = 26 }: { size?: number }) {
  return (
    <div
      aria-hidden="true"
      style={{
        width: size,
        height: size,
        borderRadius: "50%",
        background: "linear-gradient(135deg, #cc785c 0%, #a05a42 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        flexShrink: 0,
        fontSize: Math.round(size * 0.44),
        color: "#ffffff",
        fontWeight: 700,
        letterSpacing: "-0.02em",
      }}
    >
      C
    </div>
  )
}

/* ── Thinking dots (Claude is reasoning) ───────────────────────── */

function ThinkingDots() {
  return (
    <div
      style={{
        display: "flex",
        gap: 5,
        alignItems: "center",
        padding: "10px 14px",
        borderRadius: 12,
        borderBottomLeftRadius: 3,
        background: "#ffffff",
        border: "1px solid rgba(25,25,25,0.08)",
        animation: "cc-fade-in 0.25s ease both",
        width: "fit-content",
      }}
    >
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          style={{
            display: "block",
            width: 6,
            height: 6,
            borderRadius: "50%",
            background: "#8a847b",
            animation: "cc-dot-pulse 1.2s ease-in-out infinite",
            animationDelay: `${i * 0.2}s`,
          }}
        />
      ))}
    </div>
  )
}

/* ── Session status badge ───────────────────────────────────────── */

function SessionStatusBadge({ done }: { done: boolean }) {
  if (done) {
    return (
      <span
        style={{
          display: "inline-flex",
          alignItems: "center",
          gap: 3,
          borderRadius: 4,
          padding: "2px 7px",
          fontSize: 11,
          fontWeight: 500,
          background: "rgba(204,120,92,0.10)",
          color: "#cc785c",
          flexShrink: 0,
          animation: "cc-fade-in 0.3s ease both",
        }}
      >
        <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
          <path
            d="M2 5l2.5 2.5L8 3"
            stroke="#cc785c"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        done
      </span>
    )
  }
  return (
    <span
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: 4,
        borderRadius: 4,
        padding: "2px 7px",
        fontSize: 11,
        fontWeight: 500,
        background: "rgba(204,120,92,0.10)",
        color: "#cc785c",
        flexShrink: 0,
      }}
    >
      <span
        style={{
          display: "inline-block",
          width: 6,
          height: 6,
          borderRadius: "50%",
          background: "#cc785c",
          animation: "cc-blink 1.1s step-end infinite",
          flexShrink: 0,
        }}
      />
      running
    </span>
  )
}

/* ── Individual session card ────────────────────────────────────── */

function SessionCard({
  session,
  done,
  index,
}: {
  session: { id: string; label: string; task: string }
  done: boolean
  index: number
}) {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 8,
        padding: "7px 10px",
        borderRadius: 8,
        border: "1px solid rgba(25,25,25,0.08)",
        background: "#faf9f5",
        animation: "cc-session-in 0.35s cubic-bezier(0.22,1,0.36,1) both",
        animationDelay: `${index * 0.05}s`,
      }}
    >
      <div style={{ minWidth: 0 }}>
        <span
          style={{
            fontFamily: "'SF Mono', 'JetBrains Mono', Consolas, monospace",
            fontSize: 12,
            fontWeight: 500,
            color: "#191919",
            display: "block",
          }}
        >
          {session.label}
        </span>
        <span
          style={{
            fontSize: 11,
            color: "#8a847b",
            display: "block",
            marginTop: 1,
            whiteSpace: "nowrap",
            overflow: "hidden",
            textOverflow: "ellipsis",
          }}
        >
          {session.task}
        </span>
      </div>
      <SessionStatusBadge done={done} />
    </div>
  )
}

/* ── Chat header ────────────────────────────────────────────────── */

function ChatHeader() {
  return (
    <div
      style={{
        padding: "9px 14px",
        borderBottom: "1px solid rgba(25,25,25,0.07)",
        display: "flex",
        alignItems: "center",
        gap: 8,
        background: "rgba(250,249,245,0.96)",
        backdropFilter: "blur(10px)",
        flexShrink: 0,
      }}
    >
      <ClaudeAvatar size={22} />
      <span
        style={{
          fontSize: 14,
          fontWeight: 500,
          color: "#191919",
          letterSpacing: "-0.01em",
        }}
      >
        Claude
      </span>
      <span
        style={{
          marginLeft: "auto",
          fontSize: 10,
          fontWeight: 700,
          letterSpacing: "0.06em",
          color: "#cc785c",
          background: "rgba(204,120,92,0.10)",
          borderRadius: 4,
          padding: "2px 6px",
        }}
      >
        CONCERTO
      </span>
    </div>
  )
}

/* ── Chat input area ────────────────────────────────────────────── */

function ChatInput({ state }: { state: DemoState }) {
  const userMsg = DEMO_TEXTS.userMessage
  const visibleText = userMsg.slice(0, state.userChars)
  const isTyping = !state.messageSent && state.userChars > 0 && state.userChars < userMsg.length
  const showCaret = !state.messageSent && state.userChars > 0

  return (
    <div
      style={{
        padding: "8px 12px",
        borderTop: "1px solid rgba(25,25,25,0.07)",
        background: "#ffffff",
        flexShrink: 0,
        display: "flex",
        alignItems: "center",
        gap: 8,
      }}
    >
      {/* Input field */}
      <div
        style={{
          flex: 1,
          minHeight: 36,
          borderRadius: 10,
          border: "1px solid rgba(25,25,25,0.12)",
          background: "#faf9f5",
          padding: "8px 12px",
          fontSize: 13,
          color: "#191919",
          display: "flex",
          alignItems: "center",
          boxShadow:
            state.userChars > 0 && !state.messageSent
              ? "0 0 0 2px rgba(204,120,92,0.18)"
              : "none",
          transition: "box-shadow 0.2s ease",
          overflow: "hidden",
        }}
      >
        {state.userChars === 0 || state.messageSent ? (
          <span style={{ color: "#a59f97" }}>Ask Claude to build something…</span>
        ) : (
          <>
            <span>{visibleText}</span>
            {showCaret && (
              <span
                style={{
                  display: "inline-block",
                  width: 1.5,
                  height: "1.1em",
                  background: "#cc785c",
                  verticalAlign: "text-bottom",
                  marginLeft: 1,
                  borderRadius: 1,
                  animation: isTyping ? "none" : "cc-blink 0.7s step-end infinite",
                }}
              />
            )}
          </>
        )}
      </div>

      {/* Send button */}
      <div
        style={{
          width: 34,
          height: 34,
          borderRadius: 9,
          background:
            state.userChars > 0 && !state.messageSent
              ? "#cc785c"
              : "rgba(25,25,25,0.08)",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          transition: "background 0.2s ease",
        }}
      >
        <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden="true">
          <path
            d="M1 7h11M8 3l4 4-4 4"
            stroke={
              state.userChars > 0 && !state.messageSent ? "#ffffff" : "#8a847b"
            }
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </div>
    </div>
  )
}

/* ── Chat messages area ─────────────────────────────────────────── */

function ChatMessages({ state }: { state: DemoState }) {
  const sessions = DEMO_TEXTS.sessions

  return (
    <div
      style={{
        flex: 1,
        padding: "14px 12px 10px",
        display: "flex",
        flexDirection: "column",
        gap: 10,
        overflow: "hidden",
      }}
    >
      {/* User message bubble (appears after send) */}
      {state.messageSent && (
        <div
          style={{
            display: "flex",
            justifyContent: "flex-end",
            animation: "cc-fade-up 0.28s cubic-bezier(0.22,1,0.36,1) both",
          }}
        >
          <div
            style={{
              background: "#cc785c",
              color: "#ffffff",
              borderRadius: 12,
              borderBottomRightRadius: 3,
              padding: "9px 13px",
              fontSize: 13,
              fontWeight: 500,
              maxWidth: "78%",
              lineHeight: 1.45,
            }}
          >
            {DEMO_TEXTS.userMessage}
          </div>
        </div>
      )}

      {/* Claude thinking */}
      {state.showThinking && !state.showIntro && (
        <div style={{ display: "flex", gap: 8, alignItems: "flex-end" }}>
          <ClaudeAvatar size={24} />
          <ThinkingDots />
        </div>
      )}

      {/* Claude intro + session cards */}
      {state.showIntro && (
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "flex-start",
            animation: "cc-fade-up 0.28s cubic-bezier(0.22,1,0.36,1) both",
          }}
        >
          <ClaudeAvatar size={24} />
          <div style={{ flex: 1, minWidth: 0 }}>
            {/* Claude intro text */}
            <div
              style={{
                background: "#ffffff",
                border: "1px solid rgba(25,25,25,0.08)",
                borderRadius: 12,
                borderBottomLeftRadius: 3,
                padding: "9px 13px",
                fontSize: 13,
                color: "#191919",
                lineHeight: 1.5,
                marginBottom: 7,
              }}
            >
              {DEMO_TEXTS.claudeIntro}
            </div>

            {/* Session cards */}
            {state.sessionCount > 0 && (
              <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                {(sessions.slice(0, state.sessionCount) as ReadonlyArray<typeof sessions[number]>).map(
                  (session, i) => (
                    <SessionCard
                      key={session.id}
                      session={session}
                      done={
                        (i === 0 && state.session1Done) ||
                        (i === 1 && state.session2Done) ||
                        (i === 2 && state.session3Done)
                      }
                      index={i}
                    />
                  )
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Claude final report */}
      {state.showReport && (
        <div
          style={{
            display: "flex",
            gap: 8,
            alignItems: "flex-start",
            animation: "cc-fade-up 0.28s cubic-bezier(0.22,1,0.36,1) both",
          }}
        >
          <ClaudeAvatar size={24} />
          <div
            style={{
              flex: 1,
              background: "#ffffff",
              border: "1px solid rgba(204,120,92,0.22)",
              borderRadius: 12,
              borderBottomLeftRadius: 3,
              padding: "9px 13px",
              fontSize: 13,
              color: "#191919",
              lineHeight: 1.5,
            }}
          >
            {DEMO_TEXTS.claudeReport}
          </div>
        </div>
      )}
    </div>
  )
}

/* ── Full chat body ─────────────────────────────────────────────── */

function ChatBody({ state }: { state: DemoState }) {
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        background: "#faf9f5",
      }}
    >
      <ChatHeader />
      <ChatMessages state={state} />
      <ChatInput state={state} />
    </div>
  )
}

/* ── Browser chrome shell ───────────────────────────────────────── */

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
      aria-label="Concerto demo: one conversation with Claude orchestrating parallel Claude Code sessions"
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
            claude.ai
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
    const msg = DEMO_TEXTS.userMessage

    // User types message character by character
    for (let c = 1; c <= msg.length; c++) {
      const cap = c
      add(
        () => setState((s) => ({ ...s, userChars: cap })),
        T.userTypeStartAt + (cap - 1) * T.streamMs,
      )
    }

    // User sends the message (input clears, message appears in chat)
    add(
      () => setState((s) => ({ ...s, messageSent: true, userChars: msg.length })),
      T.sendClickAt,
    )

    // Claude thinking dots appear
    add(
      () => setState((s) => ({ ...s, showThinking: true })),
      T.thinkingAt,
    )

    // Claude's intro replaces thinking dots
    add(
      () => setState((s) => ({ ...s, showThinking: false, showIntro: true })),
      T.claudeIntroAt,
    )

    // Session cards appear one by one
    add(() => setState((s) => ({ ...s, sessionCount: 1 })), T.session1At)
    add(() => setState((s) => ({ ...s, sessionCount: 2 })), T.session2At)
    add(() => setState((s) => ({ ...s, sessionCount: 3 })), T.session3At)

    // Sessions complete one by one
    add(() => setState((s) => ({ ...s, session1Done: true })), T.session1DoneAt)
    add(() => setState((s) => ({ ...s, session2Done: true })), T.session2DoneAt)
    add(() => setState((s) => ({ ...s, session3Done: true })), T.session3DoneAt)

    // Claude's final report
    add(() => setState((s) => ({ ...s, showReport: true })), T.claudeReportAt)

    // Fade out, then loop
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
        <ChatBody state={state} />
      </DemoShell>
    </>
  )
}

/* ── Static fallback (prefers-reduced-motion) ─────────────────────── */

function StaticFallback() {
  const finalState: DemoState = {
    userChars: DEMO_TEXTS.userMessage.length,
    messageSent: true,
    showThinking: false,
    showIntro: true,
    sessionCount: 3,
    session1Done: true,
    session2Done: true,
    session3Done: true,
    showReport: true,
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
        <ChatBody state={finalState} />
      </DemoShell>
    </>
  )
}

/* ── Export ──────────────────────────────────────────────────────── */

export function HeroClaudeDemo() {
  const reduced = usePrefersReducedMotion()
  return reduced ? <StaticFallback /> : <AnimatedDemo />
}
