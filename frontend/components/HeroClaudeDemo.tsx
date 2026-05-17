"use client"

import { useEffect, useRef, useState, useCallback } from "react"
import { HERO_SCRIPTS, HERO_TIMINGS, type ScriptVariant } from "./hero-claude-demo-script"

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

// Geometric C mark — open arc + centre dot. NOT the Anthropic logo.
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

function Sidebar({ script }: { script: ScriptVariant }) {
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
        {script.sidebarProjects.map((p) => (
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
        {script.sidebarRecents.map((title) => (
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

function ToolChip({
  toolName,
  params,
  expanded,
}: {
  toolName: string
  params: Record<string, unknown>
  expanded: boolean
}) {
  const hasParams = Object.keys(params).length > 0
  const paramStr = hasParams
    ? JSON.stringify(params, null, 2)
    : ""

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
          {toolName}
        </span>
        <div className="ml-auto">
          <svg
            width="11" height="11" viewBox="0 0 12 12" fill="none"
            style={{ color: "#877c70", transform: expanded ? "rotate(180deg)" : "rotate(0deg)", transition: "transform 0.3s ease" }}
          >
            <path d="M3 4.5L6 7.5L9 4.5" stroke="currentColor" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </div>
      </div>
      {expanded && hasParams && (
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
        </div>
      )}
    </div>
  )
}

function InputArea({ isTyping, displayedPrompt, hasConversation }: { isTyping: boolean; displayedPrompt: string; hasConversation: boolean }) {
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

function DemoShell({ children, fading }: { children: React.ReactNode; fading: boolean }) {
  return (
    <div
      role="img"
      aria-label="Concerto demo: Claude orchestrating a project via Concerto workspace"
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

// Rendered conversation item
type ConvItem =
  | { type: "user"; text: string }
  | { type: "text"; text: string; streamedChars: number }
  | { type: "tool"; toolName: string; params: Record<string, unknown>; expanded: boolean }

function MessageThread({
  items,
  scrollRef,
}: {
  items: ConvItem[]
  scrollRef: React.RefObject<HTMLDivElement>
}) {
  return (
    <div
      ref={scrollRef}
      className="flex-1 overflow-y-auto px-4 py-5 space-y-4"
      style={{ scrollbarWidth: "none" }}
    >
      {items.map((item, i) => {
        if (item.type === "user") {
          return (
            <div key={i} className="flex justify-end" style={{ animation: "cc-fade-up 0.25s ease both" }}>
              <div
                className="rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm leading-relaxed max-w-[82%]"
                style={{ background: "#2d2520", color: "#f5f0e9", border: "1px solid rgba(245,240,233,0.07)" }}
              >
                {item.text}
              </div>
            </div>
          )
        }
        if (item.type === "text") {
          const displayed = item.text.slice(0, item.streamedChars)
          const streaming = item.streamedChars < item.text.length
          return (
            <div key={i} className="text-sm leading-relaxed" style={{ color: "#f5f0e9", animation: "cc-fade-up 0.3s ease both" }}>
              {displayed}
              {streaming && (
                <span
                  className="inline-block ml-px"
                  style={{ width: 2, height: "1em", background: "#f5f0e9", verticalAlign: "middle", opacity: 0.5, animation: "cc-blink 0.8s step-end infinite" }}
                />
              )}
            </div>
          )
        }
        if (item.type === "tool") {
          return (
            <ToolChip
              key={i}
              toolName={item.toolName}
              params={item.params}
              expanded={item.expanded}
            />
          )
        }
        return null
      })}
    </div>
  )
}

function AnimatedDemo({ script }: { script: ScriptVariant }) {
  const [isTyping, setIsTyping] = useState(false)
  const [typedChars, setTypedChars] = useState(0)
  const [items, setItems] = useState<ConvItem[]>([])
  const [fading, setFading] = useState(false)
  const timers = useRef<ReturnType<typeof setTimeout>[]>([])
  const scrollRef = useRef<HTMLDivElement>(null)

  const clearTimers = useCallback(() => {
    timers.current.forEach(clearTimeout)
    timers.current = []
  }, [])

  const add = useCallback((fn: () => void, ms: number) => {
    timers.current.push(setTimeout(fn, ms))
  }, [])

  const scrollBottom = useCallback(() => {
    requestAnimationFrame(() => {
      if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    })
  }, [])

  const runSequence = useCallback(() => {
    const T = HERO_TIMINGS
    setIsTyping(false)
    setTypedChars(0)
    setItems([])
    setFading(false)

    let t = T.typingStartMs

    add(() => setIsTyping(true), t)

    const prompt = script.userPrompt
    for (let c = 1; c <= prompt.length; c++) {
      const cap = c
      add(() => setTypedChars(cap), t + cap * T.typingSpeedMs)
    }
    t += prompt.length * T.typingSpeedMs + T.sentDelayMs

    add(() => {
      setIsTyping(false)
      setTypedChars(0)
      setItems([{ type: "user", text: prompt }])
    }, t)

    t += 500

    let toolCount = 0

    for (let segI = 0; segI < script.segments.length; segI++) {
      const seg = script.segments[segI]
      const itemIdx = segI + 1  // 0 = user message, 1+ = segments

      if (seg.kind === "text") {
        const capturedT = t
        const content = seg.content

        add(() => {
          setItems((prev) => [
            ...prev,
            { type: "text", text: content, streamedChars: 0 },
          ])
          scrollBottom()
        }, capturedT)

        for (let c = 1; c <= content.length; c++) {
          const cap = c
          add(() => {
            setItems((prev) =>
              prev.map((it, idx) =>
                idx === itemIdx && it.type === "text"
                  ? { ...it, streamedChars: cap }
                  : it
              )
            )
          }, capturedT + cap * T.streamingSpeedMs)
        }

        t = capturedT + content.length * T.streamingSpeedMs

      } else {
        // tool chip
        const tc = toolCount
        const capturedT = t + T.afterTextToToolMs
        const shouldExpand = seg.expand

        add(() => {
          setItems((prev) => [
            ...prev,
            { type: "tool", toolName: seg.toolName, params: seg.params, expanded: false },
          ])
          scrollBottom()
        }, capturedT)

        if (shouldExpand) {
          add(() => {
            setItems((prev) =>
              prev.map((it, idx) =>
                idx === itemIdx && it.type === "tool"
                  ? { ...it, expanded: true }
                  : it
              )
            )
            scrollBottom()
          }, capturedT + T.toolExpandDelayMs)
        }

        const afterDelay = tc === 0 ? T.afterTool1Ms : tc === 1 ? T.afterTool2Ms : T.afterTool3Ms
        t = capturedT + afterDelay
        toolCount++
      }
    }

    add(() => setFading(true), t + T.donePauseMs)
    add(() => { setItems([]); runSequence() }, t + T.donePauseMs + T.fadeMs + 500)
  }, [script, add, scrollBottom])

  useEffect(() => {
    const t = setTimeout(() => runSequence(), 500)
    return () => { clearTimeout(t); clearTimers() }
  }, [runSequence, clearTimers])

  const displayedPrompt = script.userPrompt.slice(0, typedChars)
  const hasConversation = items.some((it) => it.type === "user")

  return (
    <DemoShell fading={fading}>
      <Sidebar script={script} />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <MessageThread items={items} scrollRef={scrollRef} />
        <InputArea isTyping={isTyping} displayedPrompt={displayedPrompt} hasConversation={hasConversation} />
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

function StaticFallback({ script }: { script: ScriptVariant }) {
  const finalItems: ConvItem[] = [
    { type: "user", text: script.userPrompt },
    ...script.segments.map((seg): ConvItem => {
      if (seg.kind === "text") {
        return { type: "text", text: seg.content, streamedChars: seg.content.length }
      }
      return { type: "tool", toolName: seg.toolName, params: seg.params, expanded: seg.expand }
    }),
  ]

  return (
    <DemoShell fading={false}>
      <Sidebar script={script} />
      <div className="flex flex-col flex-1 min-w-0">
        <TopBar />
        <div className="flex-1 overflow-hidden px-4 py-5 space-y-4">
          {finalItems.map((item, i) => {
            if (item.type === "user") {
              return (
                <div key={i} className="flex justify-end">
                  <div className="rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm max-w-[82%]"
                    style={{ background: "#2d2520", color: "#f5f0e9", border: "1px solid rgba(245,240,233,0.07)" }}>
                    {item.text}
                  </div>
                </div>
              )
            }
            if (item.type === "text") {
              return (
                <div key={i} className="text-sm leading-relaxed" style={{ color: "#f5f0e9" }}>
                  {item.text}
                </div>
              )
            }
            if (item.type === "tool") {
              return (
                <ToolChip key={i} toolName={item.toolName} params={item.params} expanded={item.expanded} />
              )
            }
            return null
          })}
        </div>
        <InputArea isTyping={false} displayedPrompt="" hasConversation={true} />
      </div>
    </DemoShell>
  )
}

export function HeroClaudeDemo() {
  const scriptIdxRef = useRef(Math.floor(Math.random() * HERO_SCRIPTS.length))
  const script = HERO_SCRIPTS[scriptIdxRef.current]
  const reduced = usePrefersReducedMotion()
  return reduced ? <StaticFallback script={script} /> : <AnimatedDemo script={script} />
}
