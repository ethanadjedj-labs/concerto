"use client"

import { useState, useEffect, useRef } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"

function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <img
      src="/brand/logo-mark.png?v=3"
      alt="Concerto"
      width={size}
      height={size}
      style={{ display: "block", width: size, height: size }}
    />
  )
}

type Phase = "form" | "waiting" | "error"

// ── Waiting experience ────────────────────────────────────────────
// One continuous screen: honest progress (calibrated to real measured
// timings — boot ~30s, install ~2.5min) driven by live backend status,
// with rotating English storytelling (a little dry humour) and a
// graceful "taking a bit longer" reassurance past the expected window.

const WAIT_STEPS: { key: string; label: string; pct: number }[] = [
  { key: "paid_unprovisioned", label: "Setting things up", pct: 8 },
  { key: "provisioning", label: "Preparing your space", pct: 30 },
  { key: "installing", label: "Getting Claude ready", pct: 78 },
  { key: "awaiting_oauth", label: "Almost there", pct: 100 },
]

const STORY: string[] = [
  "Good things take a moment. This is one of them.",
  "You're about to delegate the boring parts. All of them.",
  "Soon: you describe what you want, it gets built.",
  "Think of the most tedious thing on your list. That one's leaving.",
  "A short wait now for a very long shortcut later.",
  "Patience now. Leverage in a minute.",
  "The hard part is on us. The fun part is on you.",
  "You bring the ideas. Claude brings the hours back.",
  "Soon you'll wonder how you ever did it the old way.",
  "Setting things up so day one already feels like day one hundred.",
  "This is the longest you'll wait here. Genuinely.",
  "Quietly putting every piece where it belongs.",
  "Making sure the first run just works. No asterisks.",
  "Almost ready to hand over the keys.",
  "We're trading three minutes now for entire afternoons later.",
  "Tuning the last details so nothing trips you up.",
  "Your future self is already several tasks ahead.",
  "Built once, properly, so you never think about it again.",
  "The kind of wait that pays for itself by lunch.",
  "Getting it right beats getting it fast. You get both, mostly.",
  "Lining everything up so later, nothing breaks.",
  "A calm minute before a very productive month.",
  "Worth doing once. We're doing it once.",
  "You'll only see this screen a handful of times. Savour it.",
  "The boring setup so your work never has to be.",
  "Preparing the part you'll happily forget exists.",
  "Slow on purpose here so it's fast everywhere else.",
  "Everything you're about to stop doing manually: loading.",
  "One quiet moment, then you mostly just ask and receive.",
  "We're making the first impression count.",
  "Last stretch. This is where it starts getting good.",
  "Nearly set. Keep this tab open and breathe.",
  "Almost there, the honest kind of almost.",
  "Putting finishing touches exactly where you'll never notice them.",
  "Steady. The handoff is worth every second of this.",
  "Coming together nicely. Just a little longer.",
  "Soon this whole screen will be a distant memory.",
  "Doing the unglamorous work so yours can be the opposite.",
  "We could've shown a fake progress bar. We didn't. This is real.",
  "Yes, it's actually doing something. No, we won't say what.",
  "This bar is not lying to you. It would never. It can't, actually.",
  "Somewhere a tiny gremlin is installing things. Be kind to it.",
  "Bribing the electrons to move faster. They drive a hard bargain.",
  "Reticulating splines. Whatever those are.",
  "It's long, we know. But it always finishes. Always. We checked.",
  "Counting to a large number very, very carefully.",
  "If this were instant you wouldn't trust it. You're welcome.",
  "Teaching Claude your coffee order. Kidding. Mostly.",
  "Folding the laundry of the internet. Nearly done.",
  "We promise the wait is shrinking. The wait says hi.",
  "Doing important things in a serious order. Trust the order.",
  "This is the part where impatient people refresh. Don't be those people.",
  "Aligning the cosmic load-bearing yak. Standard procedure.",
  "Still here. Still working. Still not a fake bar.",
  "Almost done assembling the thing that assembles the things.",
  "Three minutes of magic tricks, zero actual rabbits.",
]

const EXPECTED_MS = 200_000 // ~3min 20s; past this we switch to reassurance

function WaitingExperience({
  status,
  startedAt,
}: {
  status: string | null
  startedAt: number
}) {
  const [now, setNow] = useState(Date.now())
  // Shuffle once so the sequence differs every visit and never repeats
  // a line within a single wait (30 lines >> ~3min / 6.5s).
  const orderRef = useRef<number[]>([])
  if (orderRef.current.length === 0) {
    const idxs = STORY.map((_, i) => i)
    for (let i = idxs.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[idxs[i], idxs[j]] = [idxs[j], idxs[i]]
    }
    orderRef.current = idxs
  }
  const [storyPos, setStoryPos] = useState(0)

  useEffect(() => {
    const t = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(t)
  }, [])

  useEffect(() => {
    const t = setInterval(
      () => setStoryPos((p) => (p + 1) % orderRef.current.length),
      6500
    )
    return () => clearInterval(t)
  }, [])

  const storyIdx = orderRef.current[storyPos] ?? 0

  const elapsed = startedAt ? now - startedAt : 0
  const overdue = elapsed > EXPECTED_MS

  // Status drives the floor; time gently fills the gap so the bar always
  // moves (never stalls, never lies past the real step).
  const stepIdx = Math.max(
    0,
    WAIT_STEPS.findIndex((x) => x.key === status)
  )
  const floor = stepIdx >= 0 ? WAIT_STEPS[stepIdx].pct : 8
  const ceil =
    stepIdx >= 0 && stepIdx < WAIT_STEPS.length - 1
      ? WAIT_STEPS[stepIdx + 1].pct
      : floor
  const timeFrac = Math.min(1, elapsed / EXPECTED_MS)
  const pct = Math.min(
    99,
    Math.max(floor, Math.round(floor + (ceil - floor) * timeFrac))
  )
  const displayPct = status === "awaiting_oauth" ? 100 : pct

  const currentLabel =
    WAIT_STEPS[stepIdx]?.label ?? "Setting things up"

  return (
    <div
      className="rounded-2xl p-8"
      style={{
        backgroundColor: "#fff",
        boxShadow:
          "0 1px 4px rgba(25,25,25,0.06), 0 4px 24px rgba(25,25,25,0.04)",
        border: "1px solid #f3efe5",
      }}
    >
      {/* Pulsing indicator */}
      <div className="mb-6 flex justify-center">
        <div className="relative flex h-14 w-14 items-center justify-center">
          <div
            className="absolute h-14 w-14 rounded-full animate-ping"
            style={{ backgroundColor: "rgba(204,120,92,0.15)" }}
          />
          <div
            className="relative h-8 w-8 rounded-full"
            style={{ backgroundColor: "rgba(204,120,92,0.2)" }}
          />
          <div
            className="absolute h-4 w-4 rounded-full"
            style={{ backgroundColor: "#cc785c" }}
          />
        </div>
      </div>

      <h2
        className="mb-1.5 text-center text-[22px] font-medium"
        style={{ color: "#191919" }}
      >
        Getting everything ready
      </h2>
      <p
        className="mx-auto mb-6 max-w-sm text-center text-[14px] leading-relaxed"
        style={{ color: "#8a847b" }}
      >
        This takes about three minutes. Keep this tab open and you&apos;ll
        be taken in automatically — nothing to click.
      </p>

      {/* Progress bar */}
      <div className="mb-2 flex items-center justify-between text-[12px]">
        <span style={{ color: "#191919", fontWeight: 500 }}>
          {currentLabel}
        </span>
        <span style={{ color: "#8a847b" }}>{displayPct}%</span>
      </div>
      <div
        className="mb-6 h-2 w-full overflow-hidden rounded-full"
        style={{ backgroundColor: "#f3efe5" }}
      >
        <div
          className="h-full rounded-full transition-all duration-700 ease-out"
          style={{
            width: `${displayPct}%`,
            backgroundColor: "#cc785c",
          }}
        />
      </div>

      {/* Step checklist */}
      <ol className="mb-6 space-y-2.5">
        {WAIT_STEPS.slice(0, 3).map((st, i) => {
          const done = stepIdx > i || status === "awaiting_oauth"
          const active = stepIdx === i && status !== "awaiting_oauth"
          return (
            <li key={st.key} className="flex items-center gap-3">
              <span
                className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold"
                style={{
                  backgroundColor: done
                    ? "rgba(34,197,94,0.12)"
                    : active
                    ? "rgba(204,120,92,0.14)"
                    : "#f3efe5",
                  color: done ? "#16a34a" : active ? "#cc785c" : "#b8b2a8",
                }}
              >
                {done ? "✓" : i + 1}
              </span>
              <span
                className="text-[13px]"
                style={{
                  color: done
                    ? "#16a34a"
                    : active
                    ? "#191919"
                    : "#b8b2a8",
                  fontWeight: active ? 500 : 400,
                }}
              >
                {st.label}
              </span>
            </li>
          )
        })}
      </ol>

      {/* Rotating storytelling / reassurance */}
      <div
        className="rounded-xl px-4 py-3 text-center text-[13px] leading-relaxed"
        style={{
          backgroundColor: "#faf9f5",
          border: "1px solid #f3efe5",
          color: "#8a847b",
          minHeight: "44px",
        }}
      >
        {overdue ? (
          <span>
            Still working on it — this occasionally takes a little
            longer. It almost always wraps up within another minute. ☕
          </span>
        ) : (
          <span
            key={storyIdx}
            className="animate-in fade-in"
            style={{ animationDuration: "400ms" }}
          >
            {STORY[storyIdx]}
          </span>
        )}
      </div>
    </div>
  )
}


export default function TrialPage() {
  const [email, setEmail] = useState("")
  const [phase, setPhase] = useState<Phase>("form")
  const [errorMsg, setErrorMsg] = useState("")
  const [busy, setBusy] = useState(false)
  // live backend status: paid_unprovisioned -> provisioning -> installing -> awaiting_oauth
  const [provStatus, setProvStatus] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const startedAtRef = useRef<number>(0)
  const router = useRouter()

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"

  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
  }, [])

  async function startTrial() {
    if (!email || busy) return
    setBusy(true)
    setErrorMsg("")
    try {
      const r = await fetch("/api/trial/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      })
      const ct = r.headers.get("content-type") || ""
      let parsed: { token?: string; dashboard_url?: string; error?: string; message?: string; detail?: unknown } = {}
      if (ct.includes("application/json")) {
        try { parsed = await r.json() } catch { /* fall through */ }
      }
      if (!r.ok) {
        const detail = parsed.detail && typeof parsed.detail === "object" ? parsed.detail : parsed
        const errLabel = (detail as { error?: string }).error || `HTTP ${r.status}`
        const errMsg = (detail as { message?: string }).message || ""
        setErrorMsg(`${errLabel}${errMsg ? ` — ${errMsg}` : ""}`)
        setPhase("error")
        return
      }
      if (parsed.token) {
        startedAtRef.current = Date.now()
        setPhase("waiting")
        startPolling(parsed.token)
      } else {
        const msg = "Trial started but no token returned. Contact support."
        setErrorMsg(msg)
        setPhase("error")
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err)
      setErrorMsg(`Network error — ${msg}`)
      setPhase("error")
    } finally {
      setBusy(false)
    }
  }

  function startPolling(tok: string) {
    if (pollRef.current) clearInterval(pollRef.current)
    pollRef.current = setInterval(async () => {
      try {
        const r = await fetch(`${backendUrl}/api/buyer/${tok}/status`)
        if (!r.ok) return
        const d = await r.json()
        if (d.status) setProvStatus(d.status as string)
        if (
          d.status === "awaiting_oauth" ||
          d.status === "active" ||
          d.mcp_url
        ) {
          if (pollRef.current) clearInterval(pollRef.current)
          // Zero intermediate clicks: go straight to the dashboard.
          router.push(`/dashboard/${tok}`)
        }
      } catch { /* ignore poll errors */ }
    }, 4000)
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter") startTrial()
  }

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: "#faf9f5" }}
    >
      {/* Header */}
      <header style={{ borderBottom: "1px solid #f3efe5", backgroundColor: "rgba(250,249,245,0.95)" }}>
        <div className="mx-auto flex max-w-2xl items-center justify-between px-5 py-3.5">
          <Link href="/" className="flex items-center gap-2.5">
            <LogoMark size={26} />
            <span className="text-[17px] font-medium" style={{ color: "#191919" }}>Concerto</span>
          </Link>
          <span
            className="rounded-full px-3 py-1 text-[12px] font-medium"
            style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}
          >
            30-minute trial · no card
          </span>
        </div>
      </header>

      {/* Main */}
      <main className="flex min-h-[calc(100vh-57px)] items-center justify-center px-5 py-12">
        <div
          className="w-full max-w-md animate-in fade-in"
          style={{ animationDuration: "200ms" }}
        >

          {/* Form phase */}
          {(phase === "form" || phase === "error") && (
            <div
              className="rounded-2xl p-8"
              style={{
                backgroundColor: "#fff",
                boxShadow: "0 1px 4px rgba(25,25,25,0.06), 0 4px 24px rgba(25,25,25,0.04)",
                border: phase === "error" ? "1px solid rgba(220,38,38,0.2)" : "1px solid #f3efe5",
              }}
            >
              {phase === "error" && (
                <div
                  className="mb-5 rounded-xl px-4 py-3 text-[13px] leading-relaxed"
                  style={{
                    backgroundColor: "rgba(220,38,38,0.05)",
                    borderLeft: "3px solid rgba(220,38,38,0.4)",
                    color: "#b91c1c",
                  }}
                >
                  {errorMsg}
                </div>
              )}

              <h1 className="mb-2 text-[28px] font-medium leading-tight" style={{ color: "#191919" }}>
                Try Concerto
              </h1>
              <p className="mb-7 text-[15px] leading-relaxed" style={{ color: "#8a847b" }}>
                Connect Claude to your own Claude Code orchestration in 5 minutes.
                No card. 30 minutes free.
              </p>

              <label
                htmlFor="trial-email"
                className="mb-2 block text-[13px] font-medium"
                style={{ color: "#191919" }}
              >
                Email
              </label>
              <input
                id="trial-email"
                type="email"
                value={email}
                onChange={(e) => { setEmail(e.target.value); if (phase === "error") setPhase("form") }}
                onKeyDown={handleKeyDown}
                placeholder="you@example.com"
                disabled={busy}
                className="mb-4 block w-full rounded-xl px-4 py-3 text-[15px] outline-none transition-all"
                style={{
                  backgroundColor: "#fff",
                  border: "1px solid #d4d0c8",
                  color: "#191919",
                  minHeight: "48px",
                }}
                onFocus={(e) => { e.currentTarget.style.borderColor = "#cc785c"; e.currentTarget.style.boxShadow = "0 0 0 3px rgba(204,120,92,0.12)" }}
                onBlur={(e) => { e.currentTarget.style.borderColor = "#d4d0c8"; e.currentTarget.style.boxShadow = "none" }}
              />

              <button
                type="button"
                onClick={startTrial}
                disabled={busy || !email}
                className="mb-7 flex w-full items-center justify-center rounded-xl text-[15px] font-medium transition-all"
                style={{
                  backgroundColor: busy || !email ? "#d4d0c8" : "#cc785c",
                  color: "#fff",
                  minHeight: "48px",
                  cursor: busy ? "wait" : !email ? "not-allowed" : "pointer",
                  boxShadow: !busy && email ? "0 2px 8px rgba(204,120,92,0.25)" : "none",
                }}
                onMouseEnter={(e) => {
                  if (!busy && email) {
                    e.currentTarget.style.transform = "translateY(-1px)"
                    e.currentTarget.style.boxShadow = "0 4px 16px rgba(204,120,92,0.35)"
                  }
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.transform = ""
                  e.currentTarget.style.boxShadow = !busy && email ? "0 2px 8px rgba(204,120,92,0.25)" : "none"
                }}
              >
                {busy ? (
                  <span className="flex items-center gap-1.5">
                    <span className="inline-block animate-bounce" style={{ animationDelay: "0ms" }}>·</span>
                    <span className="inline-block animate-bounce" style={{ animationDelay: "150ms" }}>·</span>
                    <span className="inline-block animate-bounce" style={{ animationDelay: "300ms" }}>·</span>
                  </span>
                ) : (
                  "Start free trial →"
                )}
              </button>

              {/* What happens next */}
              <div>
                <p className="mb-3 text-[11px] font-medium uppercase tracking-widest" style={{ color: "#8a847b" }}>
                  What happens next
                </p>
                <ol className="space-y-3">
                  {[
                    { n: "1", label: "Provisioning", detail: "Your environment is set up (~3 min)" },
                    { n: "2", label: "Add MCP connection", detail: "One command: claude mcp add — takes 30 seconds" },
                    { n: "3", label: "Start orchestrating", detail: "Ask Claude to run anything in code" },
                  ].map((step) => (
                    <li key={step.n} className="flex items-start gap-3">
                      <span
                        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold"
                        style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}
                      >
                        {step.n}
                      </span>
                      <div>
                        <span className="text-[13px] font-medium" style={{ color: "#191919" }}>{step.label}</span>
                        <span className="text-[13px]" style={{ color: "#8a847b" }}> — {step.detail}</span>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}

          {/* Waiting phase — single continuous experience, auto-redirects */}
          {phase === "waiting" && <WaitingExperience status={provStatus} startedAt={startedAtRef.current} />}

          {/* Footer */}
          <p className="mt-6 text-center text-[12px]" style={{ color: "#8a847b" }}>
            Questions?{" "}
            <a
              href="mailto:support@concerto.run"
              className="transition-opacity hover:opacity-70"
              style={{ color: "#cc785c" }}
            >
              support@concerto.run
            </a>
          </p>
        </div>
      </main>
    </div>
  )
}
