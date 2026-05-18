"use client"

import { useState, useEffect, useRef } from "react"
import type { ReactNode } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Copy, Check, Eye, EyeOff, ExternalLink, RefreshCw } from "lucide-react"

/* ─── Brand tokens ────────────────────────────────────────────────
   cream:   #faf9f5
   peach:   #cc785c  (CTAs, progress, step pills)
   body:    #191919
   muted:   #8a847b
   card:    #fff
   divider: #f3efe5
─────────────────────────────────────────────────────────────────── */

// ─── State machine ────────────────────────────────────────────────
type UIState =
  | "loading"         // first fetch pending / null status
  | "preparing"       // paid_unprovisioned — simple spinner
  | "setting_up"      // provisioning | installing — spinner + timeline
  | "failed"          // provisioning_failed
  | "step1"           // awaiting_oauth
  | "step2"           // oauth_complete | mcp_active
  | "step3"           // connector_first_call_detected | active
  | "trial_expired"
  | "cancelled"       // cancelled | subscription_cancelled
  | "refunded"
  | "suspended"
  | "network_error"

function deriveUIState(status: string | null): UIState {
  switch (status) {
    case null:
    case undefined:
      return "loading"
    case "paid_unprovisioned":
      return "preparing"
    case "provisioning":
    case "installing":
      return "setting_up"
    case "provisioning_failed":
      return "failed"
    case "awaiting_oauth":
      return "step1"
    case "oauth_complete":
    case "mcp_active":
      return "step2"
    case "connector_first_call_detected":
    case "active":
      return "step3"
    case "trial_expired":
      return "trial_expired"
    case "cancelled":
    case "subscription_cancelled":
      return "cancelled"
    case "refunded":
      return "refunded"
    case "suspended":
      return "suspended"
    default:
      return "loading"
  }
}

const POLLING_STATES: UIState[] = ["loading", "preparing", "setting_up"]

function formatDate(ts: number): string {
  return new Date(ts * 1000).toLocaleDateString("en-US", {
    month: "long",
    day: "numeric",
    year: "numeric",
  })
}

// ─── Shared primitives ────────────────────────────────────────────

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

function ProgressBar({ step }: { step: 1 | 2 | 3 }) {
  return (
    <div className="flex flex-col items-center gap-2.5">
      <div className="flex items-center">
        {([1, 2, 3] as const).map((s, i) => (
          <div key={s} className="flex items-center">
            <div
              className="h-3 w-3 rounded-full transition-colors duration-300"
              style={{
                backgroundColor: s <= step ? "#cc785c" : "rgba(25,25,25,0.15)",
              }}
            />
            {i < 2 && (
              <div
                className="h-[2px] w-10"
                style={{ backgroundColor: "rgba(25,25,25,0.12)" }}
              />
            )}
          </div>
        ))}
      </div>
      <p className="text-[13px]" style={{ color: "#8a847b" }}>
        Step {step} of 3
      </p>
    </div>
  )
}

function ValueCard({
  label,
  value,
  secret = false,
}: {
  label: string
  value: string
  secret?: boolean
}) {
  const [revealed, setRevealed] = useState(!secret)
  const [copied, setCopied] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const displayValue =
    !revealed && value && value !== "Loading..."
      ? `••••••••••${value.slice(-6)}`
      : value

  async function copy() {
    if (!value || value === "Loading...") return
    try {
      await navigator.clipboard.writeText(value)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = value
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      document.body.removeChild(ta)
    }
    setCopied(true)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div
      className="rounded-xl p-4"
      style={{ border: "1px solid #f3efe5", backgroundColor: "#fff" }}
    >
      <p
        className="mb-2 text-[11px] font-medium uppercase tracking-widest"
        style={{ color: "#8a847b" }}
      >
        {label}
      </p>
      <div className="flex items-center gap-2">
        <code
          className="min-w-0 flex-1 break-all font-mono text-[13px] leading-relaxed"
          style={{ color: "#191919" }}
        >
          {displayValue}
        </code>
        <div className="flex shrink-0 items-center gap-1">
          {secret && (
            <button
              type="button"
              onClick={() => setRevealed((r) => !r)}
              className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors hover:bg-[rgba(25,25,25,0.06)]"
              style={{ color: "#8a847b" }}
              aria-label={revealed ? "Hide value" : "Reveal value"}
            >
              {revealed ? (
                <EyeOff className="h-4 w-4" />
              ) : (
                <Eye className="h-4 w-4" />
              )}
            </button>
          )}
          <button
            type="button"
            onClick={copy}
            className="flex h-8 min-w-[64px] items-center justify-center gap-1.5 rounded-lg text-[12px] font-medium transition-all"
            style={{
              backgroundColor: copied
                ? "rgba(204,120,92,0.12)"
                : "rgba(204,120,92,0.1)",
              color: "#cc785c",
            }}
            aria-label={copied ? "Copied" : `Copy ${label}`}
          >
            {copied ? (
              <Check className="h-3.5 w-3.5" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>
    </div>
  )
}

function ConcertoStyleCard() {
  const [copied, setCopied] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  async function copyStyle() {
    const text = await fetch("/concerto-custom-style.txt").then(r => r.text())
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      document.body.removeChild(ta)
    }
    setCopied(true)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setCopied(false), 2500)
  }

  return (
    <div
      className="rounded-xl p-4"
      style={{ border: "1px solid #f3efe5", backgroundColor: "#fff" }}
    >
      <div className="mb-3 flex items-start gap-3">
        <span className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg text-[14px]"
          style={{ backgroundColor: "rgba(204,120,92,0.1)" }}>
          ✦
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[14px] font-medium" style={{ color: "#191919" }}>
            Use the Concerto style
          </p>
          <p className="mt-0.5 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
            Add our recommended Claude style for orchestration — Claude will spawn sessions
            more proactively and report back clearly.
          </p>
        </div>
      </div>
      <div className="flex items-center gap-2 flex-wrap">
        <button
          type="button"
          onClick={copyStyle}
          className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-all"
          style={{ backgroundColor: copied ? "rgba(204,120,92,0.15)" : "rgba(204,120,92,0.1)", color: "#cc785c" }}
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy style"}
        </button>
        <button
          type="button"
          onClick={() => setExpanded(e => !e)}
          className="flex items-center gap-1 rounded-lg px-3 py-1.5 text-[13px] transition-opacity hover:opacity-70"
          style={{ color: "#8a847b" }}
        >
          How to add it {expanded ? "↑" : "→"}
        </button>
      </div>
      {expanded && (
        <div className="mt-4 space-y-2 pt-4" style={{ borderTop: "1px solid #f3efe5" }}>
          {[
            "Open claude.ai → Settings → Custom Styles",
            "Click \"Add style\" and paste the copied text",
            "Name it \"Concerto Orchestrator\" and save",
          ].map((step, i) => (
            <p key={i} className="flex items-start gap-2 text-[13px]" style={{ color: "#8a847b" }}>
              <span className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[10px] font-semibold"
                style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}>
                {i + 1}
              </span>
              {step}
            </p>
          ))}
        </div>
      )}
    </div>
  )
}

function PromptCard({ text }: { text: string }) {
  const [copied, setCopied] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)

  async function copy() {
    try {
      await navigator.clipboard.writeText(text)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = text
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      document.body.removeChild(ta)
    }
    setCopied(true)
    if (timer.current) clearTimeout(timer.current)
    timer.current = setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button
      type="button"
      onClick={copy}
      className="w-full rounded-xl px-4 py-3.5 text-left text-[14px] leading-relaxed transition-all"
      style={{
        border: `1px solid ${copied ? "#cc785c" : "#f3efe5"}`,
        backgroundColor: copied ? "rgba(204,120,92,0.06)" : "#fff",
        color: "#191919",
      }}
    >
      <div className="flex items-start justify-between gap-3">
        <span className="flex-1">{text}</span>
        <span className="mt-0.5 shrink-0" style={{ color: "#cc785c" }}>
          {copied ? (
            <Check className="h-4 w-4" />
          ) : (
            <Copy className="h-4 w-4" />
          )}
        </span>
      </div>
    </button>
  )
}

// ─── State-card primitives ────────────────────────────────────────

function StatusCard({
  children,
  redBorder = false,
}: {
  children: ReactNode
  redBorder?: boolean
}) {
  return (
    <div
      className="rounded-2xl p-8 text-center"
      style={{
        backgroundColor: "#fff",
        border: "1px solid #f3efe5",
        ...(redBorder ? { borderLeft: "3px solid rgba(220,38,38,0.3)" } : {}),
      }}
    >
      {children}
    </div>
  )
}

function SupportLink() {
  return (
    <p className="mt-5 text-[12px]" style={{ color: "#8a847b" }}>
      <a
        href="mailto:support@concerto.run"
        className="underline transition-opacity hover:opacity-70"
        style={{ color: "#8a847b" }}
      >
        support@concerto.run
      </a>
    </p>
  )
}

function SpinnerDots() {
  return (
    <div className="mb-4 flex justify-center gap-1.5">
      {[0, 1, 2].map((i) => (
        <span
          key={i}
          className="_cdot"
          style={{ animationDelay: `${[-0.32, -0.16, 0][i]}s` }}
        />
      ))}
    </div>
  )
}

function UpgradeCTAs({ token }: { token: string }) {
  return (
    <div className="flex flex-col gap-2">
      <form method="POST" action={`/api/checkout?plan=solo&trial_token=${token}`}>
        <button
          type="submit"
          className="w-full rounded-xl px-4 py-2.5 text-[14px] font-medium transition-opacity hover:opacity-90"
          style={{ backgroundColor: "#cc785c", color: "#fff" }}
        >
          Subscribe to Solo — $49/mo
        </button>
      </form>
      <form method="POST" action={`/api/checkout?plan=pro&trial_token=${token}`}>
        <button
          type="submit"
          className="w-full rounded-xl px-4 py-2.5 text-[14px] font-medium transition-opacity hover:opacity-75"
          style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}
        >
          or Pro — $99/mo
        </button>
      </form>
    </div>
  )
}

// ─── Main page component ──────────────────────────────────────────

export default function DashboardPage({
  params,
}: {
  params: { token: string }
}) {
  const [uiState, setUIState] = useState<UIState>("loading")
  const uiStateRef = useRef<UIState>("loading")
  const [rawStatus, setRawStatus] = useState<string | null>(null)
  const [dashData, setDashData] = useState<{
    mcp_url?: string
    bearer_token?: string
    expires_at?: number
    next_renewal_at?: number
  } | null>(null)
  // GitHub-style sign-in flow:
  //   idle -> starting -> awaiting_code (authUrl ready) -> submitting -> success
  const [signInPhase, setSignInPhase] = useState<
    | "idle"
    | "starting"
    | "awaiting_code"
    | "submitting"
    | "finishing"
    | "success"
  >("idle")
  const [authUrl, setAuthUrl] = useState<string | null>(null)
  const [oauthCode, setOauthCode] = useState("")
  const [signInError, setSignInError] = useState("")
  const [oauthSuccess, setOauthSuccess] = useState(false)
  // Increments on manual retry to restart the polling effect
  const [fetchTrigger, setFetchTrigger] = useState(0)

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"

  async function startSignIn() {
    setSignInError("")
    setSignInPhase("starting")
    // The first call launches `claude setup-token` on the box (~7s) and may
    // 504 while it boots. Retry a few times before surfacing an error so a
    // cold start doesn't look like a failure.
    const MAX_TRIES = 4
    for (let attempt = 1; attempt <= MAX_TRIES; attempt++) {
      try {
        const r = await fetch(
          `${backendUrl}/api/buyer/${params.token}/oauth/start`,
          { method: "POST" }
        )
        const d = await r.json().catch(() => ({}))
        if (r.ok && d.auth_url) {
          setAuthUrl(d.auth_url)
          setSignInPhase("awaiting_code")
          // Best-effort auto-open; browsers may block window.open() after an
          // await. The prominent "Open Anthropic authorization" button is
          // the reliable path (direct user gesture = never blocked).
          window.open(d.auth_url, "_blank", "noopener,noreferrer")
          return
        }
        // 504 = still preparing on the box → retry; other errors → stop.
        if (r.status !== 504 || attempt === MAX_TRIES) {
          throw new Error(
            d.detail ?? "Couldn't start sign-in. Please retry."
          )
        }
      } catch (e) {
        if (attempt === MAX_TRIES) {
          setSignInError(
            e instanceof Error ? e.message : "Couldn't start sign-in."
          )
          setSignInPhase("idle")
          return
        }
      }
      // brief backoff before next try
      await new Promise((res) => setTimeout(res, 2500))
    }
  }

  async function submitCode() {
    const code = oauthCode.trim()
    if (!code) {
      setSignInError("Paste the code from the Anthropic page first.")
      return
    }
    setSignInError("")
    setSignInPhase("submitting")
    try {
      const r = await fetch(
        `${backendUrl}/api/buyer/${params.token}/oauth/submit-code`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code }),
        }
      )
      const d = await r.json().catch(() => ({}))
      // 4xx with a detail = real rejection (bad code / expired session).
      if (!r.ok) {
        throw new Error(d.detail ?? "Sign-in failed. Please try again.")
      }
      // Backend accepted the code and is finalizing in the background.
      // Poll oauth-status until the box is credentialed (the request itself
      // returns instantly so we never hit the tunnel timeout).
      setSignInPhase("finishing")
      const deadline = Date.now() + 90_000
      const tick = async (): Promise<void> => {
        if (Date.now() > deadline) {
          setSignInError(
            "This is taking longer than usual. Your code may still be processing — wait a moment, or click \"Sign in with Claude\" to retry."
          )
          setSignInPhase("awaiting_code")
          return
        }
        try {
          const sr = await fetch(
            `${backendUrl}/api/buyer/${params.token}/oauth-status`
          )
          const sd = await sr.json().catch(() => ({}))
          if (sd.oauth_complete) {
            setSignInPhase("success")
            setOauthSuccess(true)
            setTimeout(() => {
              setUIState("step2")
              uiStateRef.current = "step2"
            }, 1400)
            return
          }
        } catch {
          /* transient — keep polling */
        }
        setTimeout(tick, 3500)
      }
      tick()
    } catch (e) {
      setSignInError(e instanceof Error ? e.message : "Sign-in failed.")
      setSignInPhase("awaiting_code")
    }
  }

  // Keep ref in sync for use inside interval callbacks
  useEffect(() => {
    uiStateRef.current = uiState
  }, [uiState])

  // Main status poll — active while in loading/preparing/setting_up
  useEffect(() => {
    let failCount = 0

    async function poll() {
      if (!POLLING_STATES.includes(uiStateRef.current)) return
      try {
        const r = await fetch(`${backendUrl}/api/buyer/${params.token}/status`)
        if (!r.ok) throw new Error(`HTTP ${r.status}`)
        const d = await r.json()
        failCount = 0
        setRawStatus(d.status ?? null)
        setDashData({
          mcp_url: d.mcp_url,
          bearer_token: d.bearer_token,
          expires_at: d.expires_at,
          next_renewal_at: d.next_renewal_at,
        })
        const next = deriveUIState(d.status ?? null)
        setUIState(next)
        uiStateRef.current = next
      } catch {
        failCount++
        if (failCount >= 3) {
          setUIState("network_error")
          uiStateRef.current = "network_error"
        }
      }
    }

    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  }, [backendUrl, params.token, fetchTrigger])

  // OAuth safety-net poll — if the box gets credentialed by any path
  // (e.g. submit-code finalized server-side), auto-advance.
  useEffect(() => {
    if (uiState !== "step1" || oauthSuccess) return
    const id = setInterval(async () => {
      try {
        const r = await fetch(
          `${backendUrl}/api/buyer/${params.token}/oauth-status`
        )
        const d = await r.json()
        if (d.oauth_complete) {
          setOauthSuccess(true)
          clearInterval(id)
          setTimeout(() => {
            setUIState("step2")
            uiStateRef.current = "step2"
          }, 1600)
        }
      } catch {
        // network blip — ignore, retry next tick
      }
    }, 6000)
    return () => clearInterval(id)
  }, [uiState, oauthSuccess, backendUrl, params.token])

  // First-call poll — active in step2
  useEffect(() => {
    if (uiState !== "step2") return
    const id = setInterval(async () => {
      try {
        const r = await fetch(
          `${backendUrl}/api/buyer/${params.token}/first-call-detected`
        )
        const d = await r.json()
        if (d.detected) {
          clearInterval(id)
          setTimeout(() => {
            setUIState("step3")
            uiStateRef.current = "step3"
          }, 800)
        }
      } catch {
        // ignore
      }
    }, 5000)
    return () => clearInterval(id)
  }, [uiState, backendUrl, params.token])

  const mcpUrl = dashData?.mcp_url ?? "Loading..."
  const bearerToken = dashData?.bearer_token ?? "Loading..."

  const hideAccountSettings = ["trial_expired", "cancelled", "refunded"].includes(
    uiState
  )
  const isWizardState =
    uiState === "step1" || uiState === "step2" || uiState === "step3"
  const wizardStep: 1 | 2 | 3 =
    uiState === "step2" ? 2 : uiState === "step3" ? 3 : 1

  async function openCustomerPortal() {
    try {
      const r = await fetch(`${backendUrl}/api/customer-portal-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: params.token }),
      })
      if (!r.ok) throw new Error("Portal unavailable")
      const d = await r.json()
      if (d.url) window.location.href = d.url
    } catch {
      alert(
        "Couldn't open the billing portal. Email support@concerto.run for help."
      )
    }
  }

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: "#faf9f5", color: "#191919" }}
    >
      {/* Keyframes for dot-spinner and SVG arc */}
      <style>{`
        @keyframes _cdp{0%,80%,100%{transform:scale(0);opacity:0}40%{transform:scale(1);opacity:1}}
        ._cdot{display:inline-block;width:8px;height:8px;background:#cc785c;border-radius:50%;animation:_cdp 1.4s infinite ease-in-out both}
        @keyframes _cspin{to{transform:rotate(360deg)}}
        ._cspin{animation:_cspin 1.2s linear infinite;transform-origin:22px 22px}
      `}</style>

      {/* ── Header ── */}
      <header
        className="sticky top-0 z-10"
        style={{
          borderBottom: "1px solid rgba(25,25,25,0.07)",
          backgroundColor: "rgba(250,249,245,0.90)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div className="mx-auto flex max-w-2xl items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <LogoMark size={28} />
            <span
              className="text-[18px] font-medium leading-none tracking-tight"
              style={{ color: "#191919" }}
            >
              Concerto
            </span>
          </div>
          {!hideAccountSettings && (
            <Link
              href={`/dashboard/${params.token}/settings`}
              className="text-[13px] transition-opacity hover:opacity-70"
              style={{ color: "#8a847b" }}
            >
              Account settings
            </Link>
          )}
        </div>
      </header>

      {/* ── Main ── */}
      <main className="mx-auto max-w-md px-5 py-10">
        {/* Progress bar — wizard states only */}
        {isWizardState && (
          <div className="mb-8">
            <ProgressBar step={wizardStep} />
          </div>
        )}

        {/* ── Loading ── */}
        {uiState === "loading" && (
          <StatusCard>
            <SpinnerDots />
            <p className="text-[15px] font-medium" style={{ color: "#191919" }}>
              Loading your account…
            </p>
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Preparing (paid_unprovisioned) ── */}
        {uiState === "preparing" && (
          <StatusCard>
            <SpinnerDots />
            <p className="mb-2 text-[15px] font-medium" style={{ color: "#191919" }}>
              Preparing your environment
            </p>
            <p className="text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              This takes about 3 minutes. The page will refresh automatically
              when ready.
            </p>
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Setting up (provisioning / installing) ── */}
        {uiState === "setting_up" && (
          <StatusCard>
            <div className="mb-5 flex justify-center">
              <svg width="44" height="44" viewBox="0 0 44 44">
                <circle
                  cx="22"
                  cy="22"
                  r="18"
                  fill="none"
                  stroke="#f3efe5"
                  strokeWidth="3"
                />
                <circle
                  cx="22"
                  cy="22"
                  r="18"
                  fill="none"
                  stroke="#cc785c"
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeDasharray="32 82"
                  className="_cspin"
                />
              </svg>
            </div>
            <p className="mb-4 text-[15px] font-medium" style={{ color: "#191919" }}>
              Setting up your environment…
            </p>
            {/* Micro-timeline */}
            <div className="flex items-center justify-center text-[12px]">
              {(
                [
                  ["Provisioning", "provisioning"],
                  ["Installing tools", "installing"],
                  ["Starting services", null],
                ] as [string, string | null][]
              ).map(([label, matchStatus], i) => {
                const active =
                  matchStatus !== null && rawStatus === matchStatus
                const done =
                  rawStatus === "installing" && matchStatus === "provisioning"
                return (
                  <span key={label} className="flex items-center">
                    <span
                      style={{
                        color: active
                          ? "#cc785c"
                          : done
                          ? "rgba(204,120,92,0.5)"
                          : "#c5bfb7",
                        fontWeight: active ? 500 : 400,
                      }}
                    >
                      {label}
                    </span>
                    {i < 2 && (
                      <span className="mx-2" style={{ color: "#e5e0d8" }}>
                        ·
                      </span>
                    )}
                  </span>
                )
              })}
            </div>
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Provisioning failed ── */}
        {uiState === "failed" && (
          <StatusCard redBorder>
            <p className="mb-2 text-[15px] font-medium" style={{ color: "#191919" }}>
              Setup didn&apos;t complete
            </p>
            <p className="text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              Email{" "}
              <a
                href="mailto:support@concerto.run"
                className="underline transition-opacity hover:opacity-70"
                style={{ color: "#cc785c" }}
              >
                support@concerto.run
              </a>{" "}
              and we&apos;ll fix it manually within a few hours.
            </p>
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Network error ── */}
        {uiState === "network_error" && (
          <StatusCard>
            <p className="mb-2 text-[15px] font-medium" style={{ color: "#191919" }}>
              Connection issue
            </p>
            <p className="mb-4 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              Couldn&apos;t reach your account. Check your connection and retry.
            </p>
            <button
              type="button"
              onClick={() => {
                setUIState("loading")
                uiStateRef.current = "loading"
                setFetchTrigger((c) => c + 1)
              }}
              className="mx-auto flex items-center gap-1.5 rounded-lg px-4 py-2 text-[13px] font-medium transition-opacity hover:opacity-75"
              style={{ backgroundColor: "rgba(204,120,92,0.1)", color: "#cc785c" }}
            >
              <RefreshCw className="h-3.5 w-3.5" /> Retry
            </button>
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Trial expired ── */}
        {uiState === "trial_expired" && (
          <StatusCard>
            <p className="mb-2 text-[15px] font-medium" style={{ color: "#191919" }}>
              Your free trial ended
            </p>
            <p className="mb-5 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              To keep building, subscribe to a plan.
            </p>
            <UpgradeCTAs token={params.token} />
            <p className="mt-4 text-[12px] leading-relaxed" style={{ color: "#8a847b" }}>
              Trials are limited to 4 hours by design — your environment was
              destroyed when it ended. A paid plan provisions a fresh persistent
              environment in about 5 minutes.
            </p>
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Cancelled ── */}
        {uiState === "cancelled" && (
          <StatusCard>
            <p className="mb-2 text-[15px] font-medium" style={{ color: "#191919" }}>
              Your subscription ended
              {dashData?.next_renewal_at
                ? ` on ${formatDate(dashData.next_renewal_at)}`
                : ""}
            </p>
            <p className="mb-5 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              Resubscribe to restart with a fresh environment.
            </p>
            <UpgradeCTAs token={params.token} />
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Refunded ── */}
        {uiState === "refunded" && (
          <StatusCard>
            <p className="mb-2 text-[15px] font-medium" style={{ color: "#191919" }}>
              Your refund was processed
            </p>
            <p className="mb-5 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              To start again, subscribe below.
            </p>
            <UpgradeCTAs token={params.token} />
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Suspended (payment past-due) ── */}
        {uiState === "suspended" && (
          <StatusCard>
            <p className="mb-2 text-[15px] font-medium" style={{ color: "#191919" }}>
              Payment couldn&apos;t be processed
            </p>
            <p className="mb-5 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              Update your payment method to keep your environment.
            </p>
            <button
              type="button"
              onClick={openCustomerPortal}
              className="w-full rounded-xl px-4 py-2.5 text-[14px] font-medium transition-opacity hover:opacity-90"
              style={{ backgroundColor: "#cc785c", color: "#fff" }}
            >
              Update payment
            </button>
            <SupportLink />
          </StatusCard>
        )}

        {/* ── Step 1: Sign in to Claude (GitHub-style) ── */}
        {uiState === "step1" && (
          <div
            className="rounded-2xl"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <div className="space-y-5 px-6 py-6 md:px-8 md:py-8">
              <div>
                <h1
                  className="mb-2 text-[22px] font-semibold"
                  style={{ color: "#191919" }}
                >
                  Sign in to Claude
                </h1>
                <p
                  className="text-[15px] leading-relaxed"
                  style={{ color: "#8a847b" }}
                >
                  Authorize Concerto with your Claude account so it can run
                  Claude Code on your behalf. Same one-click flow you use to
                  link GitHub.
                </p>
              </div>

              {/* idle / starting → primary button */}
              {(signInPhase === "idle" || signInPhase === "starting") &&
                !oauthSuccess && (
                  <Button
                    onClick={startSignIn}
                    disabled={signInPhase === "starting"}
                    className="w-full rounded-xl text-[15px] font-medium"
                    style={{
                      backgroundColor: "#cc785c",
                      color: "#fff",
                      minHeight: "48px",
                    }}
                  >
                    {signInPhase === "starting" ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Preparing sign-in…
                      </>
                    ) : (
                      "Sign in with Claude"
                    )}
                  </Button>
                )}

              {/* awaiting_code / submitting → authorize link + code input */}
              {(signInPhase === "awaiting_code" ||
                signInPhase === "submitting" ||
                signInPhase === "finishing") &&
                !oauthSuccess && (
                  <div className="space-y-4">
                    <ol
                      className="space-y-3 text-[14px] leading-relaxed"
                      style={{ color: "#191919" }}
                    >
                      <li className="flex gap-3">
                        <span
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold"
                          style={{
                            backgroundColor: "rgba(204,120,92,0.12)",
                            color: "#cc785c",
                          }}
                        >
                          1
                        </span>
                        <span>
                          Open the Anthropic authorization page, sign in, and
                          click <strong>Authorize</strong>.
                        </span>
                      </li>
                      <li className="flex gap-3">
                        <span
                          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold"
                          style={{
                            backgroundColor: "rgba(204,120,92,0.12)",
                            color: "#cc785c",
                          }}
                        >
                          2
                        </span>
                        <span>Copy the code Anthropic shows you and paste it below.</span>
                      </li>
                    </ol>

                    {authUrl && (
                      <a
                        href={authUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex w-full items-center justify-center gap-2 rounded-xl text-[15px] font-medium"
                        style={{
                          backgroundColor: "#191919",
                          color: "#fff",
                          minHeight: "48px",
                        }}
                      >
                        Open Anthropic authorization
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}

                    <p
                      className="text-[12px] leading-relaxed"
                      style={{ color: "#8a847b" }}
                    >
                      A tab may have opened automatically. If your browser
                      blocked the pop-up, use the button above to open it
                      manually.
                    </p>

                    <div className="space-y-2">
                      <input
                        type="text"
                        value={oauthCode}
                        onChange={(e) => setOauthCode(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") submitCode()
                        }}
                        placeholder="Paste authorization code"
                        autoComplete="off"
                        spellCheck={false}
                        disabled={
                          signInPhase === "submitting" ||
                          signInPhase === "finishing"
                        }
                        className="w-full rounded-xl px-4 py-3 text-[14px] outline-none"
                        style={{
                          backgroundColor: "#faf9f5",
                          border: "1px solid #f3efe5",
                          color: "#191919",
                        }}
                      />
                      <Button
                        onClick={submitCode}
                        disabled={
                          signInPhase === "submitting" ||
                          signInPhase === "finishing" ||
                          !oauthCode.trim()
                        }
                        className="w-full rounded-xl text-[15px] font-medium"
                        style={{
                          backgroundColor: "#cc785c",
                          color: "#fff",
                          minHeight: "48px",
                        }}
                      >
                        {signInPhase === "submitting" ||
                        signInPhase === "finishing" ? (
                          <>
                            <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                            {signInPhase === "finishing"
                              ? "Finalizing on your server…"
                              : "Sending code…"}
                          </>
                        ) : (
                          "Complete sign-in"
                        )}
                      </Button>
                    </div>
                  </div>
                )}

              {/* error */}
              {signInError && !oauthSuccess && (
                <div
                  className="rounded-xl px-4 py-3 text-[13px] leading-relaxed"
                  style={{
                    backgroundColor: "rgba(220,38,38,0.06)",
                    color: "#b91c1c",
                    border: "1px solid rgba(220,38,38,0.2)",
                  }}
                >
                  {signInError}
                </div>
              )}

              {/* success */}
              {oauthSuccess && (
                <div
                  className="flex items-center gap-2 rounded-xl px-4 py-3 text-[15px] font-medium"
                  style={{
                    backgroundColor: "rgba(34,197,94,0.08)",
                    color: "#16a34a",
                    border: "1px solid rgba(34,197,94,0.2)",
                  }}
                >
                  <Check className="h-4 w-4 shrink-0" />
                  Signed in. Moving to next step…
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Step 2: Connect to claude.ai ── */}
        {uiState === "step2" && (
          <div
            className="rounded-2xl"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <div className="space-y-6 px-6 py-6 md:px-8 md:py-8">
              <div>
                <h1
                  className="mb-2 text-[22px] font-semibold"
                  style={{ color: "#191919" }}
                >
                  Connect Concerto to claude.ai
                </h1>
                <p
                  className="text-[15px] leading-relaxed"
                  style={{ color: "#8a847b" }}
                >
                  In Claude&apos;s Settings → Connectors, add a custom connector
                  with the values below.
                </p>
              </div>

              {/* Value sub-cards */}
              <div className="space-y-3">
                <ValueCard label="MCP URL" value={mcpUrl} />
                <ValueCard label="Bearer token" value={bearerToken} secret />
                <ValueCard label="Connector name" value="Concerto" />
              </div>

              {/* Instructions */}
              <div
                className="space-y-4 pt-5"
                style={{ borderTop: "1px solid #f3efe5" }}
              >
                <p
                  className="text-[11px] font-medium uppercase tracking-widest"
                  style={{ color: "#8a847b" }}
                >
                  Step-by-step
                </p>
                <ol className="space-y-3">
                  {(
                    [
                      <>
                        Open claude.ai → click your avatar →{" "}
                        <strong
                          className="font-medium"
                          style={{ color: "#191919" }}
                        >
                          Settings
                        </strong>
                      </>,
                      <>
                        <strong
                          className="font-medium"
                          style={{ color: "#191919" }}
                        >
                          Connectors
                        </strong>{" "}
                        →{" "}
                        <strong
                          className="font-medium"
                          style={{ color: "#191919" }}
                        >
                          Add custom connector
                        </strong>
                      </>,
                      <>
                        Paste the values above →{" "}
                        <strong
                          className="font-medium"
                          style={{ color: "#191919" }}
                        >
                          Save
                        </strong>
                      </>,
                    ] as ReactNode[]
                  ).map((item, i) => (
                    <li
                      key={i}
                      className="flex items-start gap-3 text-[14px]"
                      style={{ color: "#8a847b" }}
                    >
                      <span
                        className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] font-semibold"
                        style={{
                          backgroundColor: "rgba(204,120,92,0.1)",
                          color: "#cc785c",
                        }}
                      >
                        {i + 1}
                      </span>
                      <span className="leading-relaxed">{item}</span>
                    </li>
                  ))}
                </ol>

                <a
                  href="https://claude.ai"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 rounded-lg border px-4 py-2 text-[14px] font-medium transition-opacity hover:opacity-75"
                  style={{ borderColor: "#f3efe5", color: "#191919" }}
                >
                  Open claude.ai <ExternalLink className="h-3.5 w-3.5" />
                </a>
              </div>

              <Button
                onClick={() => {
                  setUIState("step3")
                  uiStateRef.current = "step3"
                }}
                className="w-full rounded-xl text-[15px] font-medium"
                style={{
                  backgroundColor: "#cc785c",
                  color: "#fff",
                  minHeight: "48px",
                }}
              >
                I&apos;ve connected → Continue
              </Button>
            </div>
          </div>
        )}

        {/* ── Step 3: You're ready ── */}
        {uiState === "step3" && (
          <div
            className="rounded-2xl"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <div className="space-y-6 px-6 py-6 md:px-8 md:py-8">
              <div>
                <h1
                  className="mb-2 text-[22px] font-semibold"
                  style={{ color: "#191919" }}
                >
                  You&apos;re ready.
                </h1>
                <p
                  className="text-[15px] leading-relaxed"
                  style={{ color: "#8a847b" }}
                >
                  In your Claude chat, ask Claude to do anything that needs
                  code or shell. Concerto will spawn Claude Code sessions for
                  you.
                </p>
              </div>

              {/* Example prompt cards */}
              <div className="space-y-2">
                <p
                  className="mb-3 text-[11px] font-medium uppercase tracking-widest"
                  style={{ color: "#8a847b" }}
                >
                  Try asking Claude
                </p>
                {[
                  "Build and deploy a landing page for X",
                  "Try three fixes for this bug in parallel and tell me which one passes the tests cleanly",
                  "Audit my repo and return a structured report",
                  "Refactor this feature while another session checks for regressions",
                ].map((prompt) => (
                  <PromptCard key={prompt} text={prompt} />
                ))}
              </div>

              <ConcertoStyleCard />

              <a
                href="https://claude.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center gap-2 rounded-xl text-[15px] font-medium transition-opacity hover:opacity-90"
                style={{
                  backgroundColor: "#cc785c",
                  color: "#fff",
                  minHeight: "48px",
                }}
              >
                Open claude.ai <ExternalLink className="h-4 w-4" />
              </a>

              {/* Subtle footer */}
              <div
                className="flex flex-col items-center gap-1.5 pt-2"
                style={{ borderTop: "1px solid #f3efe5" }}
              >
                <p className="text-[13px]" style={{ color: "#8a847b" }}>
                  Need help?{" "}
                  <a
                    href="mailto:support@concerto.run"
                    className="underline transition-opacity hover:opacity-70"
                    style={{ color: "#cc785c" }}
                  >
                    support@concerto.run
                  </a>
                </p>
                <Link
                  href={`/dashboard/${params.token}/settings`}
                  className="text-[13px] transition-opacity hover:opacity-70"
                  style={{ color: "#8a847b" }}
                >
                  Account settings →
                </Link>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
