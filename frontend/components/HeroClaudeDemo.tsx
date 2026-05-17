"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { HERO_SCRIPT } from "./hero-claude-demo-script"

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

type Phase =
  | "idle" | "typing" | "sent" | "streaming"
  | "tool-loading" | "tool-expanded" | "tool-result"
  | "followup" | "done" | "fading"

const AFTER_SENT = new Set<Phase>([
  "sent","streaming","tool-loading","tool-expanded","tool-result","followup","done","fading",
])
const SHOW_RESPONSE = new Set<Phase>([
  "streaming","tool-loading","tool-expanded","tool-result","followup","done","fading",
])
const SHOW_TOOL = new Set<Phase>([
  "tool-loading","tool-expanded","tool-result","followup","done","fading",
])

// Geometric C mark — open arc + centre dot. NOT the Anthropic logo (three asymmetric arcs).
// This is a single symmetric open circle letterform; a different visual motif entirely.
function BrandMark() {
  return (
    <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <circle
        cx="10" cy="10" r="7"
        stroke="#d97757" strokeWidth="1.8"
        strokeDasharray="33" strokeDashoffset="11"
        strokeLinecap="round"
        transform="rotate(-20 10 10)"
      />
      <circle cx="10" cy="10" r="2.2" fill="#d97757" opacity="0.9" />
    </svg>
  )
}

function ConcertoIcon({ size = 10 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 10 10" fill="none" aria-hidden="true">
      <circle cx="5" cy="5" r="4" stroke="#d97757" strokeWidth="1.1" opacity="0.8" />
      <path d="M5.7 1.8L4 5H5.3L4.3 8.2L6.3 5H5L5.7 1.8Z" fill="#d97757" />
    </svg>
  )
}

function Sidebar() {
  const { sidebarProjects, sidebarRecents } = HERO_SCRIPT
  return (
    <div
      className="hidden md:flex flex-col shrink-0 overflow-hidden"
      style={{ width: 210, background: "#130f16", borderRight: "1px solid rgba(245,240,233,0.06)" }}
    >
      <div className="flex items-center gap-2 px-4 py-3">
        <BrandMark />
        <span style={{ color: "#f5f0e9", fontSize: 13, fontWeight: 500, letterSpacing: "-0.01em" }}>
          Concerto
        </span>
      </div>
      <div className="px-3 pb-2">
        <div
          className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-md"
          style={{ border: "1px solid rgba(245,240,233,0.09)", color: "#877c70", fontSize: 12, cursor: "default" }}
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
            <path d="M6 2V10M2 6H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round"/>
          </svg>
          New chat
        </div>
      </div>
      <div className="px-3 mt-1">
        <div style={{ color: "#877c70", fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", paddingBottom: 5, paddingLeft: 8 }}>
          Projects
        </div>
        {sidebarProjects.map((p) => (
          <div
            key={p.name}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-md mb-px truncate"
            style={{
              background: p.active ? "rgba(217,119,87,0.13)" : "transparent",
              border: p.active ? "1px solid rgba(217,119,87,0.2)" : "1px solid transparent",
              color: p.active ? "#e48a62" : "#877c70",
              fontSize: 12,
            }}
          >
            <svg width="11" height="11" viewBox="0 0 12 12" fill="none" opacity={p.active ? 1 : 0.6}>
              <path d="M1 3.5C1 3 1.5 2.5 2 2.5H5L6.5 4H10C10.5 4 11 4.5 11 5V9.5C11 10 10.5 10.5 10 10.5H2C1.5 10.5 1 10 1 9.5V3.5Z" stroke="currentColor" strokeWidth="1.1"/>
            </svg>
            <span className="truncate">{p.name}</span>
          </div>
        ))}
      </div>
      <div className="px-3 mt-4">
        <div style={{ color: "#877c70", fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", paddingBottom: 5, paddingLeft: 8 }}>
          Recents
        </div>
        {sidebarRecents.map((title) => (
          <div
            key={title}
            className="flex items-center gap-2 px-2.5 py-1.5 rounded-md mb-px"
            style={{ color: "#877c70", fontSize: 12 }}
          >
            <svg width="10" height="10" viewBox="0 0 12 12" fill="none" opacity="0.55" className="shrink-0">
              <path d="M1.5 2C1.5 1.5 2 1 2.5 1H9.5C10 1 10.5 1.5 10.5 2V7.5C10.5 8 10 8.5 9.5 8.5H4L1.5 11V2Z" stroke="currentColor" strokeWidth="1.1"/>
            </svg>
            <span className="truncate">{title}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function TopBar() {
  return (
    <div
      className="flex items-center justify-between px-4 py-2 shrink-0"
      style={{ borderBottom: "1px solid rgba(245,240,233,0.06)" }}
    >
      <div
        className="flex items-center gap-1.5 px-2.5 py-1 rounded-md"
        style={{ border: "1px solid rgba(245,240,233,0.09)", color: "#c4b8aa", fontSize: 12, cursor: "default" }}
      >
        <span style={{ color: "#f5f0e9", fontWeight: 500 }}>Claude</span>
        <span style={{ color: "#877c70", marginLeft: 2 }}>Opus 4.7</span>
        <svg width="9" height="9" viewBox="0 0 10 10" fill="none" style={{ opacity: 0.45, marginLeft: 1 }}>
          <path d="M2 3.5L5 6.5L8 3.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
      </div>
      <div className="flex items-center gap-3" style={{ color: "#877c70" }}>
        <button className="flex items-center gap-1 text-[11px]" style={{ cursor: "default" }}>
          <svg width="12" height="12" viewBox="0 0 13 13" fill="none">
            <path d="M6.5 1L9.5 4M6.5 1L3.5 4M6.5 1V8.5M2 9V12H11V9" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Share
        </button>
        <button style={{ cursor: "default" }}>
          <svg width="13" height="13" viewBox="0 0 14 14" fill="none">
            <circle cx="7" cy="7" r="2.5" stroke="currentColor" strokeWidth="1.2"/>
            <path d="M7 1.5V2.5M7 11.5V12.5M1.5 7H2.5M11.5 7H12.5M3.2 3.2L3.9 3.9M10.1 10.1L10.8 10.8M3.2 10.8L3.9 10.1M10.1 3.9L10.8 3.2" stroke="currentColor" strokeWidth="1.2" strokeLinecap="round"/>
          </svg>
        </button>
      </div>
    </div>
  )
}

function ToolCallWidget({ loading, expanded, resultCount }: { loading: boolean; expanded: boolean; resultCount: number }) {
  const params = HERO_SCRIPT.toolParams
  const results = HERO_SCRIPT.resultLines.slice(0, resultCount)
  const paramStr = `{\n  "project": "${params.project}",\n  "prompt": "${params.prompt}",\n  "timeout_seconds": ${params.timeout_seconds}\n}`

  return (
    <div
      className="mt-3 rounded-lg overflow-hidden"
      style={{ border: "1px solid rgba(245,240,233,0.1)", background: "#130f16", animation: "cc-fade-up 0.3s ease both" }}
    >
      <div
        className="flex items-center gap-2 px-3 py-2"
        style={{ borderBottom: expanded ? "1px solid rgba(245,240,233,0.07)" : "none" }}
      >
        <ConcertoIcon size={12} />
        <span style={{ color: "#c4b8aa", fontSize: 12, fontWeight: 500 }}>Using Concerto</span>
        <span style={{ color: "#877c70", fontSize: 12 }}>·</span>
        <span style={{ color: "#877c70", fontSize: 11, fontFamily: "'JetBrains Mono', ui-monospace, monospace" }}>
          spawn_claude_code_session
        </span>
        <div className="ml-auto flex items-center gap-2">
          {loading && !expanded && (
            <span style={{ color: "#877c70", fontSize: 11, animation: "cc-pulse 1.4s ease-in-out infinite" }}>
              Working…
            </span>
          )}
          <svg
            width="11" height="11" viewBox="0 0 12 12" fill="none"
            style={{ color: "#877c70", transform: expanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.3s ease" }}
          >
            <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
      {expanded && (
        <div className="px-3 py-2.5" style={{ animation: "cc-fade-down 0.25s ease both" }}>
          <div style={{ color: "#877c70", fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 5 }}>
            Parameters
          </div>
          <pre
            className="rounded px-3 py-2 text-[11px] overflow-x-auto"
            style={{ background: "rgba(0,0,0,0.35)", color: "#c4b8aa", fontFamily: "'JetBrains Mono', ui-monospace, monospace", lineHeight: 1.65, margin: 0 }}
          >
            {paramStr}
          </pre>
          {results.length > 0 && (
            <div className="mt-3">
              <div style={{ color: "#877c70", fontSize: 10, fontWeight: 600, letterSpacing: "0.07em", textTransform: "uppercase", marginBottom: 5 }}>
                Output
              </div>
              <div className="rounded px-3 py-2 space-y-1" style={{ background: "rgba(0,0,0,0.35)" }}>
                {results.map((line, i) => (
                  <div
                    key={i}
                    className="flex items-start gap-2 text-[11px]"
                    style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", color: "#c4b8aa", animation: "cc-fade-left 0.2s ease both" }}
                  >
                    <span style={{ color: "#4ade80", flexShrink: 0 }}>{line.icon}</span>
                    <span>{line.text}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

function InputArea({ phase, displayedPrompt }: { phase: Phase; displayedPrompt: string }) {
  const isTyping = phase === "typing"
  const hasConversation = AFTER_SENT.has(phase)
  const sendActive = isTyping && displayedPrompt.length > 0

  return (
    <div className="px-3 pt-2 pb-3 shrink-0" style={{ borderTop: "1px solid rgba(245,240,233,0.06)" }}>
      <div
        className="flex items-end gap-2 rounded-xl px-3 py-2"
        style={{ background: "#1a161c", border: "1px solid rgba(245,240,233,0.09)", minHeight: 44 }}
      >
        <button className="shrink-0 mb-0.5" style={{ color: "#877c70", cursor: "default" }}>
          <svg width="15" height="15" viewBox="0 0 16 16" fill="none">
            <path d="M13 7.5L7.5 13C6 14.5 3.5 14.5 2 13C0.5 11.5 0.5 9 2 7.5L7.5 2C8.5 1 10 1 11 2C12 3 12 4.5 11 5.5L5.5 11C5 11.5 4 11.5 3.5 11C3 10.5 3 9.5 3.5 9L9 3.5" stroke="currentColor" strokeWidth="1.3" strokeLinecap="round"/>
          </svg>
        </button>
        <div className="flex-1" style={{ minHeight: 22, display: "flex", alignItems: "center" }}>
          {isTyping ? (
            <span style={{ color: "#f5f0e9", fontSize: 13, lineHeight: "22px" }}>
              {displayedPrompt}
              <span
                className="inline-block ml-px"
                style={{ width: 2, height: "1em", background: "#d97757", verticalAlign: "middle", animation: "cc-blink 1s step-end infinite" }}
              />
            </span>
          ) : (
            <span style={{ color: "#877c70", fontSize: 13, lineHeight: "22px" }}>
              {hasConversation ? "Reply to Claude…" : "Message Claude…"}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 mb-0.5 shrink-0">
          <div
            className="flex items-center gap-1 px-2 py-0.5 rounded-full"
            style={{ border: "1px solid rgba(217,119,87,0.28)", background: "rgba(217,119,87,0.08)", fontSize: 11, color: "#d97757", fontWeight: 500 }}
          >
            <ConcertoIcon size={9} />
            Concerto
          </div>
          <button
            className="flex items-center justify-center rounded-md"
            style={{
              width: 26, height: 26, cursor: "default",
              background: sendActive ? "#d97757" : "rgba(245,240,233,0.07)",
              color: sendActive ? "#fff" : "#877c70",
              transition: "background 0.2s ease",
            }}
          >
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M6 10V2M6 2L3 5M6 2L9 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </div>
      <p className="text-center mt-1" style={{ color: "#877c70", fontSize: 10 }}>
        Claude Opus 4.7 &middot; Concerto active
      </p>
    </div>
  )
}

function MessageThread({
  phase,
  displayedResponse,
  showUserMsg,
  showResponse,
  showToolCall,
  resultCount,
  showFollowup,
  scrollRef,
}: {
  phase: Phase
  displayedResponse: string
  showUserMsg: boolean
  showResponse: boolean
  showToolCall: boolean
  resultCount: number
  showFollowup: boolean
  scrollRef: React.RefObject<HTMLDivElement>
}) {
  const toolLoading = phase === "tool-loading"
  const toolExpanded = ["tool-expanded","tool-result","followup","done","fading"].includes(phase)

  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-4 py-5 space-y-5"
      style={{ scrollbarWidth: "none" }}
    >
      <div className="text-sm leading-relaxed" style={{ color: "#c4b8aa" }}>
        {HERO_SCRIPT.existingMessage}
      </div>
      {showUserMsg && (
        <div className="flex justify-end" style={{ animation: "cc-fade-up 0.25s ease both" }}>
          <div
            className="rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed max-w-[82%]"
            style={{ background: "#2d2520", color: "#f5f0e9", border: "1px solid rgba(245,240,233,0.07)" }}
          >
            {HERO_SCRIPT.userPrompt}
          </div>
        </div>
      )}
      {showResponse && (
        <div style={{ animation: "cc-fade-up 0.3s ease both" }}>
          <div className="text-sm leading-relaxed" style={{ color: "#f5f0e9" }}>
            {displayedResponse}
            {phase === "streaming" && displayedResponse.length < HERO_SCRIPT.claudeResponse.length && (
              <span
                className="inline-block ml-px"
                style={{ width: 2, height: "1em", background: "#f5f0e9", verticalAlign: "middle", opacity: 0.5, animation: "cc-blink 0.8s step-end infinite" }}
              />
            )}
          </div>
          {showToolCall && (
            <ToolCallWidget loading={toolLoading} expanded={toolExpanded} resultCount={resultCount} />
          )}
        </div>
      )}
      {showFollowup && (
        <div className="text-sm leading-relaxed" style={{ color: "#f5f0e9", animation: "cc-fade-up 0.3s ease both" }}>
          {HERO_SCRIPT.claudeFollowup}
        </div>
      )}
    </div>
  )
}

function DemoShell({ children, fading }: { children: React.ReactNode; fading: boolean }) {
  return (
    <div
      role="img"
      aria-label="Concerto demo: Claude Code session running inside claude.ai"
      className="relative mx-auto w-full max-w-3xl select-none"
      style={{ opacity: fading ? 0 : 1, transition: "opacity 0.65s ease" }}
    >
      <div
        className="rounded-xl overflow-hidden"
        style={{
          border: "1px solid rgba(25,25,25,0.12)",
          boxShadow: "0 0 0 1px rgba(25,25,25,0.04), 0 8px 32px rgba(25,25,25,0.12), 0 24px 48px rgba(25,25,25,0.08)",
        }}
      >
        <div
          className="flex items-center gap-2 px-3 py-2"
          style={{ background: "#0c0a0e", borderBottom: "1px solid rgba(245,240,233,0.05)" }}
        >
          <div className="flex gap-1.5 shrink-0">
            <span className="block w-2.5 h-2.5 rounded-full" style={{ background: "#ff5f57" }} />
            <span className="block w-2.5 h-2.5 rounded-full" style={{ background: "#ffbd2e" }} />
            <span className="block w-2.5 h-2.5 rounded-full" style={{ background: "#28c840" }} />
          </div>
          <div
            className="flex-1 mx-2 rounded py-0.5 px-3 text-center text-[11px] truncate"
            style={{ background: "#1a161c", color: "#877c70" }}
          >
            claude.ai
          </div>
          <div style={{ width: 40 }} />
        </div>
        <div className="flex" style={{ height: 460, background: "#0f0d10" }}>
          {children}
        </div>
      </div>
    </div>
  )
}

function AnimatedDemo() {
  const [phase, setPhase] = useState<Phase>("idle")
  const [typedCount, setTypedCount] = useState(0)
  const [streamedCount, setStreamedCount] = useState(0)
  const [resultCount, setResultCount] = useState(0)
  const [showFollowup, setShowFollowup] = useState(false)
  const [fading, setFading] = useState(false)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  const clearTimers = useCallback(() => { timers.current.forEach(clearTimeout); timers.current = [] }, [])
  const add = useCallback((fn: () => void, ms: number) => { timers.current.push(setTimeout(fn, ms)) }, [])
  const scrollBottom = useCallback(() => {
    requestAnimationFrame(() => { if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight })
  }, [])

  const runSequence = useCallback(() => {
    const { timings, userPrompt, claudeResponse, resultLines } = HERO_SCRIPT
    setPhase("idle"); setTypedCount(0); setStreamedCount(0)
    setResultCount(0); setShowFollowup(false); setFading(false)
    add(() => setPhase("typing"), timings.typingStartMs)
    for (let i = 1; i <= userPrompt.length; i++) {
      add(() => setTypedCount(i), timings.typingStartMs + i * timings.typingSpeedMs)
    }
    add(() => { setPhase("sent"); setTypedCount(0) }, timings.sentMs)
    add(() => setPhase("streaming"), timings.streamingStartMs)
    for (let i = 1; i <= claudeResponse.length; i++) {
      add(() => setStreamedCount(i), timings.streamingStartMs + i * timings.streamingSpeedMs)
    }
    add(scrollBottom, timings.streamingStartMs + 700)
    add(() => { setPhase("tool-loading"); scrollBottom() }, timings.toolLoadingMs)
    add(() => { setPhase("tool-expanded"); scrollBottom() }, timings.toolExpandedMs)
    add(() => setPhase("tool-result"), timings.toolResultStartMs)
    resultLines.forEach((line, idx) => {
      add(() => { setResultCount(idx + 1); scrollBottom() }, timings.toolResultStartMs + line.delayMs)
    })
    add(() => { setShowFollowup(true); setPhase("followup"); scrollBottom() }, timings.followupMs)
    add(() => setPhase("done"), timings.followupMs + 1200)
    add(() => setFading(true), timings.loopMs - 700)
    add(() => { setStreamedCount(0); runSequence() }, timings.loopMs)
  }, [add, scrollBottom])

  useEffect(() => {
    const t = setTimeout(() => runSequence(), 500)
    return () => { clearTimeout(t); clearTimers() }
  }, [runSequence, clearTimers])

  const displayedPrompt = HERO_SCRIPT.userPrompt.slice(0, typedCount)
  const displayedResponse = HERO_SCRIPT.claudeResponse.slice(0, streamedCount)

  return (
    <DemoShell fading={fading}>
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <MessageThread
          phase={phase}
          displayedResponse={displayedResponse}
          showUserMsg={AFTER_SENT.has(phase)}
          showResponse={SHOW_RESPONSE.has(phase)}
          showToolCall={SHOW_TOOL.has(phase)}
          resultCount={resultCount}
          showFollowup={showFollowup}
          scrollRef={scrollRef}
        />
        <InputArea phase={phase} displayedPrompt={displayedPrompt} />
      </div>
      <style>{`
        @keyframes cc-blink { 0%,100%{opacity:1} 50%{opacity:0} }
        @keyframes cc-fade-up { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
        @keyframes cc-fade-down { from{opacity:0;transform:translateY(-4px)} to{opacity:1;transform:translateY(0)} }
        @keyframes cc-fade-left { from{opacity:0;transform:translateX(-4px)} to{opacity:1;transform:translateX(0)} }
        @keyframes cc-pulse { 0%,100%{opacity:1} 50%{opacity:0.35} }
      `}</style>
    </DemoShell>
  )
}

function StaticFallback() {
  const { resultLines, claudeFollowup, userPrompt } = HERO_SCRIPT
  return (
    <DemoShell fading={false}>
      <Sidebar />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <div className="flex-1 overflow-hidden px-4 py-5 space-y-5">
          <div className="text-sm leading-relaxed" style={{ color: "#c4b8aa" }}>
            {HERO_SCRIPT.existingMessage}
          </div>
          <div className="flex justify-end">
            <div className="rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-[82%]"
              style={{ background: "#2d2520", color: "#f5f0e9", border: "1px solid rgba(245,240,233,0.07)" }}>
              {userPrompt}
            </div>
          </div>
          <div>
            <div className="text-sm leading-relaxed" style={{ color: "#f5f0e9" }}>
              {HERO_SCRIPT.claudeResponse}
            </div>
            <div className="mt-3 rounded-lg overflow-hidden"
              style={{ border: "1px solid rgba(245,240,233,0.1)", background: "#130f16" }}>
              <div className="flex items-center gap-2 px-3 py-2"
                style={{ borderBottom: "1px solid rgba(245,240,233,0.07)" }}>
                <ConcertoIcon size={12} />
                <span style={{ color: "#c4b8aa", fontSize: 12, fontWeight: 500 }}>Using Concerto</span>
                <span style={{ color: "#877c70", fontSize: 12 }}>&nbsp;&middot;&nbsp;</span>
                <span style={{ color: "#877c70", fontSize: 11, fontFamily: "'JetBrains Mono', ui-monospace, monospace" }}>
                  spawn_claude_code_session
                </span>
              </div>
              <div className="px-3 py-2.5">
                <div className="rounded px-3 py-2 space-y-1" style={{ background: "rgba(0,0,0,0.35)" }}>
                  {resultLines.map((l, i) => (
                    <div key={i} className="flex items-start gap-2 text-[11px]"
                      style={{ fontFamily: "'JetBrains Mono', ui-monospace, monospace", color: "#c4b8aa" }}>
                      <span style={{ color: "#4ade80" }}>{l.icon}</span>
                      <span>{l.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
          <div className="text-sm leading-relaxed" style={{ color: "#f5f0e9" }}>
            {claudeFollowup}
          </div>
        </div>
        <InputArea phase="done" displayedPrompt="" />
      </div>
    </DemoShell>
  )
}

export function HeroClaudeDemo() {
  const reduced = usePrefersReducedMotion()
  return reduced ? <StaticFallback /> : <AnimatedDemo />
}
