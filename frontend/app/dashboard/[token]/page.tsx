"use client"

import { useState, useEffect, useRef } from "react"
import type { ReactNode } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Copy, Check, Eye, EyeOff, ExternalLink, RefreshCw, ChevronDown, ChevronUp, Github } from "lucide-react"

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
  const labels = ["Sign in", "Connect", "Build"] as const
  return (
    <div className="flex flex-col items-center gap-3">
      <div className="flex items-center">
        {([1, 2, 3] as const).map((s, i) => (
          <div key={s} className="flex items-center">
            <div className="flex flex-col items-center gap-1.5" style={{ width: 64 }}>
              <div
                className="flex h-6 w-6 items-center justify-center rounded-full text-[11px] font-semibold transition-colors duration-300"
                style={{
                  backgroundColor:
                    s < step
                      ? "#cc785c"
                      : s === step
                        ? "#cc785c"
                        : "rgba(25,25,25,0.08)",
                  color: s <= step ? "#fff" : "#8a847b",
                }}
              >
                {s < step ? "\u2713" : s}
              </div>
              <span
                className="text-[11px] font-medium transition-colors duration-300"
                style={{ color: s === step ? "#191919" : "#8a847b" }}
              >
                {labels[i]}
              </span>
            </div>
            {i < 2 && (
              <div
                className="mb-5 h-[2px] w-8"
                style={{
                  backgroundColor:
                    s < step ? "#cc785c" : "rgba(25,25,25,0.12)",
                }}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

/* A keyword that maps to a clickable element inside Claude's UI.
   Rendered as a small pill so users can visually match it on screen. */
function UIChip({ children }: { children: React.ReactNode }) {
  return (
    <span
      className="mx-0.5 inline-flex items-center rounded-md px-1.5 py-0.5 text-[12px] font-medium align-baseline"
      style={{
        backgroundColor: "rgba(204,120,92,0.10)",
        color: "#b3613f",
        border: "1px solid rgba(204,120,92,0.22)",
        whiteSpace: "nowrap",
      }}
    >
      {children}
    </span>
  )
}

function ValueCard({
  label,
  value,
  secret = false,
  emphasis = false,
}: {
  label: string
  value: string
  secret?: boolean
  emphasis?: boolean
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
      className="rounded-xl p-4 transition-shadow"
      style={
        emphasis
          ? {
              border: "1.5px solid #cc785c",
              backgroundColor: "#fffaf7",
              boxShadow: "0 2px 10px rgba(204,120,92,0.10)",
            }
          : { border: "1px solid #f3efe5", backgroundColor: "#fff" }
      }
    >
      <p
        className="mb-2 text-[11px] font-semibold uppercase tracking-widest"
        style={{ color: emphasis ? "#b3613f" : "#8a847b" }}
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

function ConcertoSkillCard() {
  const [copiedDesc, setCopiedDesc] = useState(false)
  const [copiedInstr, setCopiedInstr] = useState(false)
  const dt = useRef<ReturnType<typeof setTimeout> | null>(null)
  const it = useRef<ReturnType<typeof setTimeout> | null>(null)

  const DESCRIPTION =
    "Use whenever the user asks to build, create, ship, scaffold, prototype, fix, refactor, test, or deploy software, an app, a website, a backend, a feature, or any non-trivial code project. Activates Concerto orchestration so Claude decomposes the work, announces a parallel plan, and fans out multiple autonomous Claude Code sessions on the user's machine instead of asking scoping questions or writing code inline in chat."

  async function copyText(
    t: string,
    set: (b: boolean) => void,
    ref: React.MutableRefObject<ReturnType<typeof setTimeout> | null>,
  ) {
    try {
      await navigator.clipboard.writeText(t)
    } catch {
      const ta = document.createElement("textarea")
      ta.value = t
      document.body.appendChild(ta)
      ta.select()
      document.execCommand("copy")
      document.body.removeChild(ta)
    }
    set(true)
    if (ref.current) clearTimeout(ref.current)
    ref.current = setTimeout(() => set(false), 2500)
  }

  async function copyInstructions() {
    const full = await fetch("/concerto-custom-style.txt").then((r) => r.text())
    // Strip YAML frontmatter — the Skill UI has separate name/description fields
    const body = full.replace(/^---[\s\S]*?---\s*/, "").trim()
    copyText(body, setCopiedInstr, it)
  }

  return (
    <div
      className="rounded-xl p-4 text-left"
      style={{ border: "1px solid #f3efe5", backgroundColor: "#fff" }}
    >
      <div className="mb-4">
        <p className="text-[15px] font-semibold" style={{ color: "#191919" }}>
          Add the Concerto Skill
        </p>
        <p
          className="mt-1 text-[13px] leading-relaxed"
          style={{ color: "#8a847b" }}
        >
          This is what makes Claude orchestrate builds in parallel
          automatically — so you never have to say &ldquo;use Concerto&rdquo;.
          One-time setup.
        </p>
      </div>
      {true && (
        <div className="space-y-4">
          <div
            className="rounded-xl p-4"
            style={{ backgroundColor: "#fffaf7", border: "1.5px solid #cc785c" }}
          >
            <p className="text-[13px] font-semibold" style={{ color: "#191919" }}>
              Fastest way — upload the ready-made file
            </p>
            <p
              className="mb-3 mt-1 text-[12px] leading-relaxed"
              style={{ color: "#8a847b" }}
            >
              Download the Skill, then in Claude open Skills and use
              &ldquo;Upload skill&rdquo;. Nothing to fill in by hand.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row">
              <a
                href="/downloads/concerto-skill.zip"
                download
                className="flex flex-1 items-center justify-center gap-2 rounded-lg text-[13px] font-semibold transition-opacity hover:opacity-90"
                style={{ backgroundColor: "#cc785c", color: "#fff", minHeight: "42px" }}
              >
                Download Concerto Skill
              </a>
              <a
                href="https://claude.ai/customize/skills"
                target="_blank"
                rel="noopener noreferrer"
                className="flex flex-1 items-center justify-center gap-2 rounded-lg text-[13px] font-semibold transition-opacity hover:opacity-90"
                style={{ backgroundColor: "#fff", color: "#cc785c", border: "1px solid #cc785c", minHeight: "42px" }}
              >
                Open Skills <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </div>
            <p className="mt-2 text-[12px]" style={{ color: "#8a847b" }}>
              Make sure <strong style={{ color: "#191919" }}>Code execution</strong>{" "}
              is on (Settings &rarr; Capabilities) first.
            </p>
          </div>

          <details className="group">
            <summary
              className="cursor-pointer list-none text-[13px] font-medium transition-opacity hover:opacity-70"
              style={{ color: "#8a847b" }}
            >
              Or create it manually with the three fields &rarr;
            </summary>
            <p className="mb-3 mt-3 text-[13px] leading-relaxed" style={{ color: "#8a847b" }}>
              In Skills, click <strong style={{ color: "#191919" }}>Create skill</strong>{" "}
              and fill these three fields:
            </p>

          <div className="space-y-1">
            <p className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8a847b" }}>
              Skill name
            </p>
            <div
              className="rounded-lg px-3 py-2 font-mono text-[13px]"
              style={{ backgroundColor: "#faf9f5", border: "1px solid #f3efe5", color: "#191919" }}
            >
              Concerto
            </div>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#b3613f" }}>
                Description (required — triggers it)
              </p>
              <button
                type="button"
                onClick={() => copyText(DESCRIPTION, setCopiedDesc, dt)}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-all"
                style={{ backgroundColor: copiedDesc ? "rgba(204,120,92,0.15)" : "rgba(204,120,92,0.1)", color: "#cc785c" }}
              >
                {copiedDesc ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {copiedDesc ? "Copied" : "Copy"}
              </button>
            </div>
            <p
              className="max-h-20 overflow-y-auto rounded-lg px-3 py-2 text-[12px] leading-relaxed"
              style={{ backgroundColor: "#fffaf7", border: "1.5px solid #cc785c", color: "#191919" }}
            >
              {DESCRIPTION}
            </p>
            <p className="text-[12px]" style={{ color: "#8a847b" }}>
              If this field is empty, the Skill never auto-activates. Don&apos;t skip it.
            </p>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <p className="text-[11px] font-semibold uppercase tracking-widest" style={{ color: "#8a847b" }}>
                Instructions
              </p>
              <button
                type="button"
                onClick={copyInstructions}
                className="flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-medium transition-all"
                style={{ backgroundColor: copiedInstr ? "rgba(204,120,92,0.15)" : "rgba(204,120,92,0.1)", color: "#cc785c" }}
              >
                {copiedInstr ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                {copiedInstr ? "Copied" : "Copy instructions"}
              </button>
            </div>
            <p className="text-[12px]" style={{ color: "#8a847b" }}>
              Paste into the Instructions field, then Create. Make sure the
              Skill is toggled on.
            </p>
          </div>
          </details>
        </div>
      )}
    </div>
  )
}

function StarterPrompt() {
  const [copied, setCopied] = useState(false)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const text = "Use Concerto to build me a "

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
    <div
      className="mb-5 w-full rounded-xl p-4 text-left"
      style={{ border: "1px solid #f3d9cd", backgroundColor: "#fffaf7" }}
    >
      <p
        className="text-[13px] font-semibold"
        style={{ color: "#b3613f" }}
      >
        To start, just tell Claude what to build:
      </p>
      <div className="mt-2 flex items-center gap-2">
        <code
          className="min-w-0 flex-1 rounded-lg px-3 py-2 font-mono text-[13px]"
          style={{ backgroundColor: "#fff", border: "1px solid #f3efe5", color: "#191919" }}
        >
          &ldquo;Build me a&hellip;&rdquo; <span style={{ color: "#8a847b" }}>— with the Skill on, Concerto runs automatically</span>
        </code>
        <button
          type="button"
          onClick={copy}
          className="flex h-9 shrink-0 items-center justify-center gap-1.5 rounded-lg px-3 text-[12px] font-medium transition-all"
          style={{ backgroundColor: copied ? "rgba(204,120,92,0.15)" : "rgba(204,120,92,0.1)", color: "#cc785c" }}
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
          {copied ? "Copied" : "Copy"}
        </button>
      </div>
      <p
        className="mt-2 text-[12px] leading-relaxed"
        style={{ color: "#8a847b" }}
      >
        Saying &ldquo;Use Concerto&rdquo; is what tells Claude to run the work
        on your machine. It works in any language.
      </p>
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
  const [finishingMsg, setFinishingMsg] = useState("Finishing sign-in\u2026")
  const [authUrl, setAuthUrl] = useState<string | null>(null)
  const [oauthCode, setOauthCode] = useState("")
  const [signInError, setSignInError] = useState("")
  const [oauthSuccess, setOauthSuccess] = useState(false)
  // Increments on manual retry to restart the polling effect
  const [fetchTrigger, setFetchTrigger] = useState(0)
  // Code-source selector state (step3)
  const [codeSource, setCodeSource] = useState<"github" | "elsewhere" | "fresh" | null>("github")
  const [githubConnected, setGithubConnected] = useState(false)
  const [githubAvailable, setGithubAvailable] = useState(true)
  const [githubNotice, setGithubNotice] = useState<string | null>(null)

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
      // Poll /status until the buyer flips to oauth_complete. (We do NOT use
      // /oauth-status: it checks ~/.claude/.credentials.json, which
      // `claude setup-token` never writes — it would stay false forever.)
      setSignInPhase("finishing")
      const deadline = Date.now() + 150_000
      const tick = async (): Promise<void> => {
        if (Date.now() > deadline) {
          setSignInError(
            "Still finalizing — this can take a minute. If it doesn\u2019t complete shortly, get a fresh code: tap \u201cOpen Anthropic authorization\u201d again, authorize, and paste the new code."
          )
          setSignInPhase("awaiting_code")
          return
        }
        try {
          const sr = await fetch(
            `${backendUrl}/api/buyer/${params.token}/status`
          )
          const sd = await sr.json().catch(() => ({}))
          if (
            sd.status === "oauth_complete" ||
            sd.status === "mcp_active" ||
            sd.status === "active"
          ) {
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
        setTimeout(tick, 2000)
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

  // Rotating reassurance while the sign-in finalizes (can take ~30-60s).
  useEffect(() => {
    if (signInPhase !== "finishing") {
      setFinishingMsg("Finishing sign-in\u2026")
      return
    }
    const msgs = [
      "Finishing sign-in\u2026",
      "Securing your access\u2026",
      "Locking it in\u2026",
      "Almost done\u2026",
      "Just a few more seconds\u2026",
    ]
    let i = 0
    setFinishingMsg(msgs[0])
    const id = setInterval(() => {
      i = (i + 1) % msgs.length
      setFinishingMsg(msgs[i])
    }, 4000)
    return () => clearInterval(id)
  }, [signInPhase])

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

  // OAuth safety-net poll — if the buyer flips to oauth_complete by any
  // path (e.g. submit-code finalized server-side), auto-advance.
  useEffect(() => {
    if (uiState !== "step1" || oauthSuccess) return
    const id = setInterval(async () => {
      try {
        const r = await fetch(
          `${backendUrl}/api/buyer/${params.token}/status`
        )
        const d = await r.json()
        if (
          d.status === "oauth_complete" ||
          d.status === "mcp_active" ||
          d.status === "active"
        ) {
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

  // Apply a GitHub OAuth result (used by both the popup postMessage path
  // and the same-tab fallback that reads ?github= on mount).
  function applyGithubStatus(g: string | null) {
    if (g === "connected") {
      setGithubConnected(true)
      setCodeSource("github")
      setGithubNotice(null)
    } else if (g === "cancelled") {
      setCodeSource("github")
      setGithubNotice(
        "GitHub connection cancelled \u2014 you can try again anytime."
      )
    } else if (g === "unavailable") {
      setCodeSource("github")
      setGithubNotice(null)
    } else if (g === "error") {
      setCodeSource("github")
      setGithubNotice(
        "Something went wrong connecting GitHub. Please try again, or use a git clone URL for now."
      )
    }
  }

  // Option B seamless: listen for the popup telling us it finished.
  useEffect(() => {
    function onMsg(e: MessageEvent) {
      const d = e.data
      if (d && d.source === "concerto-github" && typeof d.status === "string") {
        applyGithubStatus(d.status)
      }
    }
    window.addEventListener("message", onMsg)
    return () => window.removeEventListener("message", onMsg)
  }, [])

  // Open GitHub OAuth in a centered popup (never leaves the dashboard).
  function openGithubPopup() {
    const w = 600
    const h = 720
    const left = window.screenX + Math.max(0, (window.outerWidth - w) / 2)
    const top = window.screenY + Math.max(0, (window.outerHeight - h) / 2)
    const url = `${backendUrl}/api/buyer/${params.token}/github/connect`
    const popup = window.open(
      url,
      "concerto-github",
      `width=${w},height=${h},left=${left},top=${top},resizable=yes,scrollbars=yes`
    )
    if (!popup) {
      // Popup blocked: fall back to a full-page redirect (still works,
      // the callback page redirects back to the dashboard).
      window.location.href = url
    }
  }

  // Same-tab fallback: if the popup was blocked the callback page redirects
  // here with ?github=<status>. Reuse the shared handler, then clean the URL.
  useEffect(() => {
    const sp = new URLSearchParams(window.location.search)
    const g = sp.get("github")
    if (g) {
      applyGithubStatus(g)
      const url = new URL(window.location.href)
      url.searchParams.delete("github")
      window.history.replaceState({}, "", url.toString())
    }
  }, [])

  // Poll /github/status while on step3 and not yet confirmed connected
  useEffect(() => {
    if (uiState !== "step3" || githubConnected) return
    const id = setInterval(async () => {
      try {
        const r = await fetch(
          `${backendUrl}/api/buyer/${params.token}/github/status`
        )
        if (r.ok) {
          const d = await r.json()
          if (typeof d.available === "boolean")
            setGithubAvailable(d.available)
          if (d.connected) setGithubConnected(true)
        }
      } catch {
        // network blip — ignore
      }
    }, 10000)
    return () => clearInterval(id)
  }, [uiState, githubConnected, backendUrl, params.token])

  const mcpUrl = dashData?.mcp_url ?? "Loading..."

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
          <a
            href="https://concerto.run"
            className="flex items-center gap-2.5 transition-opacity hover:opacity-70"
            aria-label="Concerto home"
          >
            <LogoMark size={28} />
            <span
              className="text-[18px] font-medium leading-none tracking-tight"
              style={{ color: "#191919" }}
            >
              Concerto
            </span>
          </a>
        </div>
      </header>

      {/* ── Main ── */}
      <main className="mx-auto w-full max-w-md px-5 py-10">
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
                    {authUrl && (
                      <a
                        href={authUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex w-full items-center justify-center gap-2 rounded-xl text-[15px] font-semibold"
                        style={{
                          backgroundColor: "#191919",
                          color: "#fff",
                          minHeight: "48px",
                        }}
                      >
                        Open Anthropic, then click Authorize
                        <ExternalLink className="h-4 w-4" />
                      </a>
                    )}

                    <div className="space-y-2">
                      <label
                        htmlFor="oauth-code-input"
                        className="block text-[13px] font-semibold"
                        style={{ color: "#191919" }}
                      >
                        Paste the code Anthropic gave you
                      </label>
                      <input
                        id="oauth-code-input"
                        type="text"
                        value={oauthCode}
                        onChange={(e) => setOauthCode(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") submitCode()
                        }}
                        placeholder="Paste the code here…"
                        autoComplete="off"
                        spellCheck={false}
                        autoFocus
                        disabled={
                          signInPhase === "submitting" ||
                          signInPhase === "finishing"
                        }
                        className="w-full rounded-xl px-4 py-3.5 text-[15px] font-mono outline-none transition-shadow focus:shadow-[0_0_0_3px_rgba(204,120,92,0.15)]"
                        style={{
                          backgroundColor: "#fff",
                          border: "2px solid #cc785c",
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
                              ? finishingMsg
                              : "Sending code…"}
                          </>
                        ) : (
                          "Complete sign-in"
                        )}
                      </Button>
                      <p
                        className="text-[12px] leading-relaxed"
                        style={{ color: "#8a847b" }}
                      >
                        The code looks like{" "}
                        <code
                          className="rounded px-1 py-0.5 font-mono text-[11px]"
                          style={{ backgroundColor: "#f3efe5", color: "#191919" }}
                        >
                          sk-ant-oat01-…
                        </code>
                        . A tab may have opened on its own — if not, use the
                        button above.
                      </p>
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

        {/* ── Step 2: Connect to Claude ── */}
        {uiState === "step2" && (
          <div
            className="rounded-2xl"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <div className="space-y-7 px-6 py-7 md:px-8 md:py-9">
              <div>
                <h1
                  className="mb-2 text-[22px] font-semibold"
                  style={{ color: "#191919" }}
                >
                  Connect Concerto to Claude
                </h1>
                <p
                  className="text-[15px] leading-relaxed"
                  style={{ color: "#8a847b" }}
                >
                  The button opens Claude with everything already filled in.
                  You just confirm — nothing to copy.
                </p>
              </div>

              <a
                href={`https://claude.ai/customize/connectors?modal=add-custom-connector&connectorName=Concerto&connectorUrl=${encodeURIComponent(mcpUrl)}`}
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center gap-2 rounded-xl text-[15px] font-semibold transition-opacity hover:opacity-90"
                style={{
                  backgroundColor: "#cc785c",
                  color: "#fff",
                  minHeight: "54px",
                  boxShadow: "0 1px 2px rgba(204,120,92,0.25)",
                }}
              >
                Open Claude &amp; add Concerto
                <ExternalLink className="h-4 w-4" />
              </a>

              <div
                className="rounded-xl p-5"
                style={{ backgroundColor: "#faf9f5", border: "1px solid #f3efe5" }}
              >
                <p
                  className="mb-3 text-[13px] font-semibold"
                  style={{ color: "#191919" }}
                >
                  In the window that opens, Claude shows the form already
                  filled in. Just:
                </p>
                <ol className="space-y-2.5">
                  {[
                    "Click Add — the name and link are already there",
                    "Click Connect on the new Concerto connector",
                    "Click Authorize — Claude returns on its own",
                  ].map((t, i) => (
                    <li key={i} className="flex gap-3 text-[14px] leading-relaxed" style={{ color: "#191919" }}>
                      <span
                        className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[12px] font-semibold"
                        style={{ backgroundColor: "rgba(204,120,92,0.12)", color: "#cc785c" }}
                      >
                        {i + 1}
                      </span>
                      <span>{t}</span>
                    </li>
                  ))}
                </ol>
              </div>

              <details className="group">
                <summary
                  className="cursor-pointer list-none text-[13px] font-medium transition-opacity hover:opacity-70"
                  style={{ color: "#8a847b" }}
                >
                  The form was empty? Copy the values manually →
                </summary>
                <div className="mt-3 space-y-3">
                  <ValueCard label="Name" value="Concerto" />
                  <ValueCard label="Remote MCP server URL" value={mcpUrl} emphasis />
                </div>
              </details>

              <div
                className="rounded-xl"
                style={{ border: "1px solid #f3efe5", backgroundColor: "#fdfcfa" }}
              >
                <details className="group">
                  <summary
                    className="flex cursor-pointer list-none items-center justify-between px-4 py-3.5"
                  >
                    <div className="min-w-0 pr-3">
                      <p className="text-[14px] font-medium" style={{ color: "#191919" }}>
                        Optional: supercharge it with the Concerto Skill
                      </p>
                      <p className="mt-0.5 text-[12px] leading-relaxed" style={{ color: "#8a847b" }}>
                        Concerto already works. Add the Skill if you want Claude
                        to fan out parallel builds automatically, with no
                        prompting.
                      </p>
                    </div>
                    <span
                      className="shrink-0 text-[12px] font-medium transition-transform group-open:rotate-180"
                      style={{ color: "#cc785c" }}
                    >
                      ▾
                    </span>
                  </summary>
                  <div className="px-4 pb-4">
                    <ConcertoSkillCard />
                  </div>
                </details>
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
          <div className="flex flex-col items-center">
            {/* Headline + single GitHub action */}
            <div className="w-full">
              <h1
                className="text-[22px] font-semibold tracking-tight"
                style={{ color: "#191919" }}
              >
                Already have a project? Connect your GitHub.
              </h1>
              <p
                className="mt-1.5 text-[14px] leading-relaxed"
                style={{ color: "#8a847b" }}
              >
                One click and Claude can build on your existing code right
                away.
              </p>

              {githubNotice && !githubConnected && (
                <div
                  className="mt-4 rounded-lg px-3 py-2 text-[13px] leading-relaxed"
                  style={{
                    backgroundColor: "#fef8f5",
                    color: "#b3613f",
                    border: "1px solid #f3d9cd",
                  }}
                >
                  {githubNotice}
                </div>
              )}

              {githubConnected ? (
                <div
                  className="mt-5 flex items-center justify-center gap-2 rounded-xl px-4 py-3.5 text-[14px] font-medium"
                  style={{ backgroundColor: "#f0fdf4", color: "#15803d" }}
                >
                  <Check className="h-4 w-4 flex-shrink-0" strokeWidth={2.5} />
                  GitHub connected — Claude can now work directly on your repos
                </div>
              ) : githubAvailable ? (
                <button
                  onClick={openGithubPopup}
                  className="mt-5 flex w-full items-center justify-center gap-2.5 rounded-xl text-[15px] font-semibold transition-opacity hover:opacity-90"
                  style={{
                    backgroundColor: "#24292f",
                    color: "#fff",
                    minHeight: "52px",
                  }}
                >
                  <Github className="h-5 w-5" />
                  Connect your GitHub in one click
                </button>
              ) : (
                <div
                  className="mt-5 rounded-xl px-4 py-3 text-[13px] leading-relaxed"
                  style={{
                    backgroundColor: "#faf7f2",
                    color: "#8a847b",
                    border: "1px solid #f3efe5",
                  }}
                >
                  Direct GitHub connect is coming soon. For now, ask Claude to{" "}
                  <code
                    className="rounded px-1 py-0.5 font-mono text-[12px]"
                    style={{ backgroundColor: "#f3efe5", color: "#191919" }}
                  >
                    git clone
                  </code>{" "}
                  your repo URL — it works today.
                </div>
              )}
            </div>

            {/* Two small secondary options */}
            <div className="mt-4 flex w-full flex-col gap-2">
              <div
                className="w-full cursor-pointer rounded-xl border px-4 py-3 text-left transition-all"
                style={{
                  backgroundColor:
                    codeSource === "elsewhere" ? "#fef8f5" : "#fff",
                  borderColor:
                    codeSource === "elsewhere" ? "#cc785c" : "#f3efe5",
                }}
                onClick={() =>
                  setCodeSource(codeSource === "elsewhere" ? null : "elsewhere")
                }
              >
                <div className="flex items-center justify-between">
                  <span
                    className="text-[14px] font-medium"
                    style={{ color: "#191919" }}
                  >
                    My code is elsewhere
                  </span>
                  {codeSource === "elsewhere" ? (
                    <ChevronUp
                      className="h-4 w-4 flex-shrink-0"
                      style={{ color: "#8a847b" }}
                    />
                  ) : (
                    <ChevronDown
                      className="h-4 w-4 flex-shrink-0"
                      style={{ color: "#8a847b" }}
                    />
                  )}
                </div>
                {codeSource === "elsewhere" && (
                  <p
                    className="mt-2 text-[13px] leading-relaxed"
                    style={{ color: "#8a847b" }}
                  >
                    Ask Claude to{" "}
                    <code
                      className="rounded px-1 py-0.5 text-[12px]"
                      style={{ backgroundColor: "#f3efe5", color: "#191919" }}
                    >
                      git clone
                    </code>{" "}
                    any URL. For private repos, paste a personal access token
                    when Claude asks — it&apos;ll set it up.
                  </p>
                )}
              </div>

              <div
                className="w-full cursor-pointer rounded-xl border px-4 py-3 text-left transition-all"
                style={{
                  backgroundColor: codeSource === "fresh" ? "#fef8f5" : "#fff",
                  borderColor: codeSource === "fresh" ? "#cc785c" : "#f3efe5",
                }}
                onClick={() =>
                  setCodeSource(codeSource === "fresh" ? null : "fresh")
                }
              >
                <div className="flex items-center justify-between">
                  <span
                    className="text-[14px] font-medium"
                    style={{ color: "#191919" }}
                  >
                    I&apos;m starting fresh
                  </span>
                  {codeSource === "fresh" ? (
                    <ChevronUp
                      className="h-4 w-4 flex-shrink-0"
                      style={{ color: "#8a847b" }}
                    />
                  ) : (
                    <ChevronDown
                      className="h-4 w-4 flex-shrink-0"
                      style={{ color: "#8a847b" }}
                    />
                  )}
                </div>
                {codeSource === "fresh" && (
                  <p
                    className="mt-2 text-[13px] leading-relaxed"
                    style={{ color: "#8a847b" }}
                  >
                    Nothing to connect — just ask Claude to create the project.
                    It&apos;ll scaffold, write, and iterate from scratch.
                  </p>
                )}
              </div>
            </div>

            {/* You're all set */}
            <div
              className="mt-9 flex w-full flex-col items-center text-center"
              style={{ borderTop: "1px solid #efeae0", paddingTop: "2rem" }}
            >
              <div
                className="mb-4 flex h-12 w-12 items-center justify-center rounded-full"
                style={{
                  background:
                    "radial-gradient(circle at 50% 45%, rgba(204,120,92,0.18) 0%, rgba(204,120,92,0.06) 60%, transparent 100%)",
                }}
              >
                <div
                  className="flex h-9 w-9 items-center justify-center rounded-full"
                  style={{ backgroundColor: "#cc785c" }}
                >
                  <Check
                    className="h-5 w-5"
                    style={{ color: "#fff" }}
                    strokeWidth={3}
                  />
                </div>
              </div>
              <h2
                className="text-[20px] font-semibold tracking-tight"
                style={{ color: "#191919" }}
              >
                You&apos;re all set.
              </h2>
              <p
                className="mb-6 mt-1.5 max-w-[22rem] text-[14px] leading-relaxed"
                style={{ color: "#8a847b" }}
              >
                Concerto is connected. Open Claude and tell it what to
                build — it runs the work for you.
              </p>

              <div className="w-full">
                <StarterPrompt />
              </div>

              <a
                href="https://claude.ai"
                target="_blank"
                rel="noopener noreferrer"
                className="flex w-full items-center justify-center gap-2 rounded-xl text-[15px] font-semibold transition-opacity hover:opacity-90"
                style={{
                  backgroundColor: "#cc785c",
                  color: "#fff",
                  minHeight: "48px",
                  boxShadow: "0 1px 2px rgba(204,120,92,0.25)",
                }}
              >
                Open Claude <ExternalLink className="h-4 w-4" />
              </a>

              <p
                className="mt-8 text-[13px]"
                style={{ color: "#8a847b" }}
              >
                Need help?{" "}
                <a
                  href="mailto:support@concerto.run"
                  className="underline transition-opacity hover:opacity-70"
                  style={{ color: "#cc785c" }}
                >
                  support@concerto.run
                </a>
              </p>
            </div>
          </div>
        )}
              </main>
    </div>
  )
}
