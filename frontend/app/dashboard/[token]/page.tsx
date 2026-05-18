"use client"

import { useState, useEffect, useRef } from "react"
import type { ReactNode } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Copy, Check, Eye, EyeOff, ExternalLink } from "lucide-react"

/* ─── Brand tokens ────────────────────────────────────────────────
   cream:   #faf9f5
   peach:   #cc785c  (CTAs, progress, step pills)
   body:    #191919
   muted:   #8a847b
   card:    #fff
   divider: #f3efe5
─────────────────────────────────────────────────────────────────── */

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
  const labels = ["Sign in to Claude", "Connect to claude.ai", "You're ready"]
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

export default function DashboardPage({
  params,
}: {
  params: { token: string }
}) {
  const [step, setStep] = useState<1 | 2 | 3>(1)
  const [dashData, setDashData] = useState<{
    mcp_url?: string
    bearer_token?: string
  } | null>(null)
  const [terminalVisible, setTerminalVisible] = useState(false)
  const [oauthSuccess, setOauthSuccess] = useState(false)

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"
  const terminalUrl = `${backendUrl}/terminal/${params.token}`

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.json())
      .then((d) =>
        setDashData({ mcp_url: d.mcp_url, bearer_token: d.bearer_token })
      )
      .catch(() => {})
  }, [backendUrl, params.token])

  // Poll oauth-status every 5s when terminal is shown (Step 1)
  useEffect(() => {
    if (step !== 1 || !terminalVisible) return
    const id = setInterval(async () => {
      try {
        const r = await fetch(
          `${backendUrl}/api/buyer/${params.token}/oauth-status`
        )
        const d = await r.json()
        if (d.oauth_complete) {
          setOauthSuccess(true)
          clearInterval(id)
          setTimeout(() => setStep(2), 1800)
        }
      } catch {
        // network blip — ignore, retry next tick
      }
    }, 5000)
    return () => clearInterval(id)
  }, [step, terminalVisible, backendUrl, params.token])

  // Poll first-call-detected every 5s when on Step 2
  useEffect(() => {
    if (step !== 2) return
    const id = setInterval(async () => {
      try {
        const r = await fetch(
          `${backendUrl}/api/buyer/${params.token}/first-call-detected`
        )
        const d = await r.json()
        if (d.detected) {
          clearInterval(id)
          setTimeout(() => setStep(3), 800)
        }
      } catch {
        // ignore
      }
    }, 5000)
    return () => clearInterval(id)
  }, [step, backendUrl, params.token])

  const mcpUrl = dashData?.mcp_url ?? "Loading..."
  const bearerToken = dashData?.bearer_token ?? "Loading..."

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: "#faf9f5", color: "#191919" }}
    >
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
          <Link
            href={`/dashboard/${params.token}/settings`}
            className="text-[13px] transition-opacity hover:opacity-70"
            style={{ color: "#8a847b" }}
          >
            Account settings
          </Link>
        </div>
      </header>

      {/* ── Wizard ── */}
      <main className="mx-auto max-w-md px-5 py-10">
        {/* Progress */}
        <div className="mb-8">
          <ProgressBar step={step} />
        </div>

        {/* ── Step 1: Sign in to Claude ── */}
        {step === 1 && (
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
                  Concerto needs to authenticate with your Claude account to
                  launch Claude Code sessions on your behalf.
                </p>
              </div>

              {!terminalVisible && !oauthSuccess && (
                <Button
                  onClick={() => setTerminalVisible(true)}
                  className="w-full rounded-xl text-[15px] font-medium"
                  style={{
                    backgroundColor: "#cc785c",
                    color: "#fff",
                    minHeight: "48px",
                  }}
                >
                  Start sign-in
                </Button>
              )}

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

              {terminalVisible && !oauthSuccess && (
                <div className="space-y-3">
                  {/* overflow:hidden on wrapper suppresses iOS Safari reader-mode overlay */}
                  <div
                    style={{
                      overflow: "hidden",
                      borderRadius: "12px",
                      border: "1px solid #f3efe5",
                      WebkitTextSizeAdjust: "100%",
                    }}
                  >
                    <iframe
                      src={terminalUrl}
                      className="w-full border-0"
                      style={{
                        display: "block",
                        height: "320px",
                        maxHeight: "520px",
                      }}
                      title="Concerto Terminal"
                      allow="clipboard-read; clipboard-write"
                      sandbox="allow-scripts allow-same-origin allow-forms"
                    />
                  </div>
                  <p
                    className="text-[13px] leading-relaxed"
                    style={{ color: "#8a847b" }}
                  >
                    Type{" "}
                    <code
                      className="rounded px-1 py-0.5 text-[12px]"
                      style={{
                        backgroundColor: "#f3efe5",
                        color: "#191919",
                      }}
                    >
                      claude login
                    </code>{" "}
                    if not already started, then follow the OAuth prompts in
                    the browser tab that opens.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── Step 2: Connect to claude.ai ── */}
        {step === 2 && (
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
                onClick={() => setStep(3)}
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
        {step === 3 && (
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
