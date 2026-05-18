"use client"

import { useState, useEffect, useRef } from "react"
import { MessageCircle, X, ExternalLink, Mail, BookOpen, WifiOff, Zap } from "lucide-react"

const SUPPORT_EMAIL = "support@concerto.run"
const FAQ_URL = "/help"

const QUICK_ISSUES = [
  {
    q: "Connector not showing in claude.ai",
    a: 'Go to claude.ai → Settings → Connectors. If it\'s missing, paste the config snippet again from your dashboard. Make sure you\'re signed into claude.ai on the same browser.',
  },
  {
    q: "OAuth step is stuck / spinning",
    a: "Open the embedded terminal on your dashboard and run: claude auth login. Follow the browser prompt. The step auto-advances once Claude CLI confirms authentication.",
  },
  {
    q: "Session disconnects after a few minutes",
    a: "The connection may have restarted. Check your dashboard — if the status shows 'reconnecting', wait 30 s and refresh. The connection recovers automatically.",
  },
]

export function SupportWidget() {
  const [open, setOpen] = useState(false)
  const [expanded, setExpanded] = useState<number | null>(null)
  const [isMobile, setIsMobile] = useState(false)
  const panelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const mq = window.matchMedia("(max-width: 640px)")
    setIsMobile(mq.matches)
    const handler = (e: MediaQueryListEvent) => setIsMobile(e.matches)
    mq.addEventListener("change", handler)
    return () => mq.removeEventListener("change", handler)
  }, [])

  useEffect(() => {
    if (!open || isMobile) return
    function handle(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener("mousedown", handle)
    return () => document.removeEventListener("mousedown", handle)
  }, [open, isMobile])

  useEffect(() => {
    if (isMobile) {
      document.body.style.overflow = open ? "hidden" : ""
    }
    return () => { document.body.style.overflow = "" }
  }, [open, isMobile])

  return (
    <>
      {isMobile && open && (
        <div
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        />
      )}

      <button
        onClick={() => setOpen((v) => !v)}
        aria-label={open ? "Close support" : "Open support"}
        className="fixed bottom-5 right-5 z-50 flex h-12 w-12 items-center justify-center rounded-full bg-violet-600 shadow-lg shadow-violet-900/40 transition-transform hover:scale-105 active:scale-95 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-violet-400"
      >
        {open ? (
          <X className="h-5 w-5 text-white" />
        ) : (
          <MessageCircle className="h-5 w-5 text-white" />
        )}
      </button>

      {open && (
        <div
          ref={panelRef}
          role="dialog"
          aria-label="Support"
          className={
            isMobile
              ? "fixed bottom-0 left-0 right-0 z-50 max-h-[85vh] overflow-y-auto rounded-t-2xl border-t border-white/10 bg-[#0d0d14] px-5 pb-8 pt-5 shadow-2xl"
              : "fixed bottom-20 right-5 z-50 w-80 rounded-2xl border border-white/10 bg-[#0d0d14] p-5 shadow-2xl"
          }
        >
          {isMobile && (
            <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-white/20" />
          )}

          <div className="mb-4 flex items-center gap-2">
            <Zap className="h-4 w-4 text-violet-400" />
            <span className="text-sm font-semibold text-white">Concerto Support</span>
          </div>

          {/* Quick links — email only */}
          <div className="mb-5 grid grid-cols-2 gap-2">
            <a
              href={`mailto:${SUPPORT_EMAIL}`}
              className="flex flex-col items-center gap-1.5 rounded-xl border border-white/8 bg-white/[0.03] p-3 text-center text-xs text-white/70 transition-colors hover:border-violet-500/40 hover:bg-violet-500/10 hover:text-white"
            >
              <Mail className="h-5 w-5 text-violet-400" />
              Email support
            </a>
            <a
              href={FAQ_URL}
              className="flex flex-col items-center gap-1.5 rounded-xl border border-white/8 bg-white/[0.03] p-3 text-center text-xs text-white/70 transition-colors hover:border-violet-500/40 hover:bg-violet-500/10 hover:text-white"
            >
              <BookOpen className="h-5 w-5 text-violet-400" />
              Help center
            </a>
          </div>

          <p className="mb-1 text-[11px] text-white/35 leading-relaxed">
            Human reply within 24 hours · support@concerto.run
          </p>

          <p className="mb-3 text-xs font-medium uppercase tracking-wider text-white/30 mt-3">
            Common issues
          </p>

          <div className="space-y-2">
            {QUICK_ISSUES.map((item, i) => (
              <div
                key={i}
                className="rounded-xl border border-white/8 bg-white/[0.02] overflow-hidden"
              >
                <button
                  onClick={() => setExpanded(expanded === i ? null : i)}
                  className="flex w-full items-center justify-between px-3 py-2.5 text-left text-xs font-medium text-white/70 hover:text-white"
                >
                  <span>{item.q}</span>
                  <span className="ml-2 shrink-0 text-white/30">{expanded === i ? "−" : "+"}</span>
                </button>
                {expanded === i && (
                  <p className="border-t border-white/6 px-3 py-2.5 text-xs leading-relaxed text-white/50">
                    {item.a}
                  </p>
                )}
              </div>
            ))}
          </div>

          <div className="mt-4 flex items-center justify-between">
            <a
              href="/status"
              className="flex items-center gap-1 text-xs text-white/30 hover:text-white/60"
            >
              <WifiOff className="h-3 w-3" />
              System status
            </a>
            <a
              href={FAQ_URL}
              className="flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300"
            >
              Full help center
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      )}
    </>
  )
}
