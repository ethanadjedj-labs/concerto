"use client"

import { useState, useEffect, useRef } from "react"
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

type Phase = "form" | "provisioning" | "ready" | "error"

export default function TrialPage() {
  const [email, setEmail] = useState("")
  const [phase, setPhase] = useState<Phase>("form")
  const [errorMsg, setErrorMsg] = useState("")
  const [dashUrl, setDashUrl] = useState("")
  const [token, setToken] = useState("")
  const [busy, setBusy] = useState(false)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

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
        const url = parsed.dashboard_url || `/dashboard/${parsed.token}`
        setToken(parsed.token)
        setDashUrl(url)
        setPhase("provisioning")
        startPolling(parsed.token)
      } else {
        setPhase("provisioning")
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
        if (d.status === "awaiting_oauth" || d.status === "active" || d.mcp_url) {
          if (pollRef.current) clearInterval(pollRef.current)
          setPhase("ready")
        }
      } catch { /* ignore poll errors */ }
    }, 5000)
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
                    { n: "2", label: "Sign in to Claude", detail: "Quick OAuth — takes 30 seconds" },
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

          {/* Provisioning phase */}
          {phase === "provisioning" && (
            <div
              className="rounded-2xl p-8 text-center"
              style={{
                backgroundColor: "#fff",
                boxShadow: "0 1px 4px rgba(25,25,25,0.06), 0 4px 24px rgba(25,25,25,0.04)",
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

              <h2 className="mb-2 text-[22px] font-medium" style={{ color: "#191919" }}>
                Provisioning your environment
              </h2>
              <p className="mb-6 text-[14px] leading-relaxed" style={{ color: "#8a847b" }}>
                Usually takes about 3 minutes. We&apos;ll send you an email when it&apos;s ready.
              </p>

              {dashUrl && (
                <a
                  href={dashUrl}
                  className="inline-flex items-center justify-center rounded-xl px-6 text-[14px] font-medium transition-opacity hover:opacity-80"
                  style={{
                    backgroundColor: "#191919",
                    color: "#faf9f5",
                    minHeight: "44px",
                  }}
                >
                  Open dashboard →
                </a>
              )}
            </div>
          )}

          {/* Ready phase */}
          {phase === "ready" && (
            <div
              className="rounded-2xl p-8 text-center"
              style={{
                backgroundColor: "#fff",
                boxShadow: "0 1px 4px rgba(25,25,25,0.06), 0 4px 24px rgba(25,25,25,0.04)",
                border: "1px solid #f3efe5",
              }}
            >
              <div className="mb-4 flex justify-center">
                <span className="text-[40px]" aria-hidden>✓</span>
              </div>
              <h2 className="mb-2 text-[22px] font-medium" style={{ color: "#191919" }}>
                Your environment is live
              </h2>
              <p className="mb-6 text-[14px] leading-relaxed" style={{ color: "#8a847b" }}>
                Check your email for the setup link, or open the dashboard directly.
              </p>
              {dashUrl && (
                <a
                  href={dashUrl}
                  className="flex items-center justify-center rounded-xl text-[15px] font-medium transition-opacity hover:opacity-80"
                  style={{
                    backgroundColor: "#cc785c",
                    color: "#fff",
                    minHeight: "48px",
                  }}
                >
                  Open dashboard →
                </a>
              )}
            </div>
          )}

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
