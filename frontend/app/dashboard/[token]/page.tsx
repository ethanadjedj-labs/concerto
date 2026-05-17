"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Copy, Check, ExternalLink, Terminal,
  CheckCircle2, Loader2, ArrowRight, Zap,
} from "lucide-react"
import { OPERATOR_STYLE_TEXT } from "@/lib/operator-style"
import { SupportWidget } from "@/components/SupportWidget"

// ── Shared UI ────────────────────────────────────────────────────────────────

function CopyBtn({ value, label }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false)
  async function copy() {
    await navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={copy}
      className="shrink-0 text-white/40 hover:text-white hover:bg-white/10 gap-1.5"
    >
      {copied ? (
        <Check className="h-3.5 w-3.5 text-green-400" />
      ) : (
        <Copy className="h-3.5 w-3.5" />
      )}
      {label && <span className="text-xs">{copied ? "Copied!" : label}</span>}
    </Button>
  )
}

function CopyField({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-1.5">
      <label className="text-xs text-white/40 font-medium uppercase tracking-wider">
        {label}
      </label>
      <div className="flex items-center gap-2">
        <code className="flex-1 rounded-md border border-white/8 bg-white/[0.03] px-3 py-2 text-sm font-mono text-white/80 break-all min-w-0">
          {value}
        </code>
        <CopyBtn value={value} />
      </div>
    </div>
  )
}

// ── Step indicator ───────────────────────────────────────────────────────────

type StepState = "pending" | "active" | "done"

function StepHeader({
  number,
  title,
  state,
}: {
  number: number
  title: string
  state: StepState
}) {
  return (
    <div className="flex items-center gap-3">
      <div
        className={`h-7 w-7 rounded-full flex items-center justify-center shrink-0 transition-colors duration-300 ${
          state === "done"
            ? "bg-green-500/20 text-green-400"
            : state === "active"
            ? "bg-violet-500/20 text-violet-300"
            : "bg-white/5 text-white/20"
        }`}
      >
        {state === "done" ? (
          <CheckCircle2 className="h-4 w-4" />
        ) : (
          <span className="text-xs font-semibold">{number}</span>
        )}
      </div>
      <span
        className={`text-sm font-medium transition-colors duration-300 ${
          state === "done"
            ? "text-white/30"
            : state === "active"
            ? "text-white"
            : "text-white/25"
        }`}
      >
        {title}
      </span>
      {state === "done" && (
        <Badge className="ml-auto bg-green-500/10 text-green-400 border-green-500/20 text-xs px-2">
          Done
        </Badge>
      )}
    </div>
  )
}

// ── Main page ────────────────────────────────────────────────────────────────

export default function DashboardPage({
  params,
}: {
  params: { token: string }
}) {
  const [step, setStep] = useState(0)
  const [buyerData, setBuyerData] = useState<{
    status?: string
    vps_ip?: string
    mcp_url?: string
    bearer_token?: string
  } | null>(null)
  const [firstCallDetected, setFirstCallDetected] = useState(false)

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.maestro.run"
  const terminalUrl = `${backendUrl}/terminal/${params.token}`

  // Step 0 → 1: poll buyer status until VPS is ready
  useEffect(() => {
    if (step !== 0) return
    let cancelled = false
    ;(async () => {
      while (!cancelled) {
        try {
          const r = await fetch(
            `${backendUrl}/api/buyer/${params.token}/status`
          )
          const d = await r.json()
          setBuyerData(d)
          if (d.mcp_url || d.status === "ready") {
            setStep(1)
            return
          }
        } catch {}
        await new Promise((r) => setTimeout(r, 3000))
      }
    })()
    return () => { cancelled = true }
  }, [backendUrl, params.token, step])

  // Step 1 → 2: poll oauth-status until Claude is authenticated
  useEffect(() => {
    if (step !== 1) return
    let cancelled = false
    ;(async () => {
      while (!cancelled) {
        try {
          const r = await fetch(
            `${backendUrl}/api/buyer/${params.token}/oauth-status`
          )
          const d = await r.json()
          if (d.oauth_complete) {
            setStep(2)
            return
          }
        } catch {}
        await new Promise((r) => setTimeout(r, 5000))
      }
    })()
    return () => { cancelled = true }
  }, [backendUrl, params.token, step])

  // Step 4: poll first-call-detected
  useEffect(() => {
    if (step !== 4) return
    let cancelled = false
    ;(async () => {
      while (!cancelled) {
        try {
          const r = await fetch(
            `${backendUrl}/api/buyer/${params.token}/first-call-detected`
          )
          const d = await r.json()
          if (d.detected) {
            setFirstCallDetected(true)
            return
          }
        } catch {}
        await new Promise((r) => setTimeout(r, 5000))
      }
    })()
    return () => { cancelled = true }
  }, [backendUrl, params.token, step])

  const mcpUrl = buyerData?.mcp_url ?? `${backendUrl}/mcp/${params.token}`
  const bearerToken = buyerData?.bearer_token ?? "Loading…"
  const vpsIp = buyerData?.vps_ip

  function ss(n: number): StepState {
    if (step > n) return "done"
    if (step === n) return "active"
    return "pending"
  }

  const titles = [
    "Provisioning your VPS",
    "Authenticate Claude",
    "Connect to claude.ai",
    "Install Operator Style",
    "Send your first prompt",
  ]

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white">
      {/* Header */}
      <header className="border-b border-white/5 bg-[#0a0a0a]/80 backdrop-blur-xl sticky top-0 z-10">
        <div className="mx-auto max-w-2xl px-4 sm:px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3 min-w-0">
            <div className="h-6 w-6 rounded bg-gradient-to-br from-violet-500 to-indigo-600 shrink-0" />
            <span className="font-semibold text-white tracking-tight">Maestro</span>
            <Separator
              orientation="vertical"
              className="h-4 bg-white/10 mx-1 hidden sm:block"
            />
            <span className="text-white/30 text-xs font-mono truncate hidden sm:block max-w-[100px]">
              {params.token}
            </span>
          </div>
          {firstCallDetected && (
            <Badge className="bg-green-500/15 text-green-400 border-green-500/20 text-xs">
              <span className="h-1.5 w-1.5 rounded-full bg-green-400 mr-1.5 inline-block animate-pulse" />
              Live!
            </Badge>
          )}
        </div>
      </header>

      <main className="mx-auto max-w-2xl px-4 sm:px-6 py-6 space-y-3">
        {/* Success banner */}
        {firstCallDetected && (
          <div className="rounded-xl border border-green-500/30 bg-green-500/10 px-5 py-4 flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0" />
            <div>
              <p className="text-green-300 font-medium text-sm">
                Your Maestro is live!
              </p>
              <p className="text-green-400/60 text-xs mt-0.5">
                First MCP call detected. You're all set.
              </p>
            </div>
          </div>
        )}

        {/* ── Step 1: Provisioning ── */}
        <Card
          className={`border-white/8 transition-all duration-300 ${
            ss(0) === "active"
              ? "bg-white/[0.04] border-violet-500/20"
              : "bg-white/[0.02]"
          }`}
        >
          <CardContent className={ss(0) === "done" ? "py-3 px-5" : "p-5"}>
            <StepHeader number={1} title={titles[0]} state={ss(0)} />
            {ss(0) === "active" && (
              <div className="mt-4 ml-10 space-y-3">
                <div className="flex items-center gap-2 text-white/50 text-sm">
                  <Loader2 className="h-4 w-4 animate-spin text-violet-400 shrink-0" />
                  <span>Provisioning your VPS — takes ~2 min…</span>
                </div>
                <p className="text-white/25 text-xs leading-relaxed">
                  Installing Claude Code, the MCP server, and a secure Cloudflare
                  tunnel on your dedicated droplet.
                </p>
              </div>
            )}
            {ss(0) === "done" && vpsIp && (
              <p className="ml-10 text-xs text-white/30 mt-1">
                VPS live at {vpsIp}
              </p>
            )}
          </CardContent>
        </Card>

        {/* ── Step 2: OAuth Claude ── */}
        <Card
          className={`border-white/8 transition-all duration-300 ${
            ss(1) === "active"
              ? "bg-white/[0.04] border-violet-500/20"
              : "bg-white/[0.02]"
          }`}
        >
          <CardContent className={ss(1) === "done" ? "py-3 px-5" : "p-5"}>
            <StepHeader number={2} title={titles[1]} state={ss(1)} />
            {ss(1) === "active" && (
              <div className="mt-4 ml-10 space-y-4">
                <p className="text-white/50 text-sm leading-relaxed">
                  Open the terminal, type{" "}
                  <code className="text-violet-300 bg-white/5 px-1.5 py-0.5 rounded text-xs">
                    claude
                  </code>{" "}
                  and follow the browser prompt to sign in with your Anthropic account.
                </p>
                <Button
                  asChild
                  className="bg-violet-600 hover:bg-violet-500 text-white gap-2 w-full sm:w-auto"
                >
                  <a
                    href={terminalUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    <Terminal className="h-4 w-4" />
                    Open Terminal
                    <ExternalLink className="h-3 w-3 opacity-60" />
                  </a>
                </Button>
                <div className="rounded-lg border border-white/5 bg-black/40 overflow-hidden">
                  <div className="flex items-center gap-2 px-4 py-2 border-b border-white/5">
                    <div className="h-2.5 w-2.5 rounded-full bg-red-500/50" />
                    <div className="h-2.5 w-2.5 rounded-full bg-yellow-500/50" />
                    <div className="h-2.5 w-2.5 rounded-full bg-green-500/50" />
                    <span className="ml-1 text-white/20 text-xs font-mono">
                      maestro · shell
                    </span>
                  </div>
                  <iframe
                    src={terminalUrl}
                    className="w-full h-56 sm:h-72 border-0"
                    title="Maestro Terminal"
                    allow="clipboard-read; clipboard-write"
                  />
                </div>
                <div className="flex items-center gap-2 text-white/30 text-xs">
                  <Loader2 className="h-3 w-3 animate-spin shrink-0" />
                  Waiting for Claude auth to complete…
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Step 3: Install Connector ── */}
        <Card
          className={`border-white/8 transition-all duration-300 ${
            ss(2) === "active"
              ? "bg-white/[0.04] border-violet-500/20"
              : "bg-white/[0.02]"
          }`}
        >
          <CardContent className={ss(2) === "done" ? "py-3 px-5" : "p-5"}>
            <StepHeader number={3} title={titles[2]} state={ss(2)} />
            {ss(2) === "active" && (
              <div className="mt-4 ml-10 space-y-5">
                <p className="text-white/50 text-sm leading-relaxed">
                  Paste these 3 values into{" "}
                  <a
                    href="https://claude.ai/settings/integrations"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-violet-400 hover:text-violet-300 inline-flex items-center gap-0.5"
                  >
                    claude.ai → Settings → Connectors
                    <ExternalLink className="h-3 w-3" />
                  </a>
                  {" "}→{" "}
                  <strong className="text-white/70">Add custom connector</strong>.
                </p>
                <div className="space-y-4">
                  <CopyField label="MCP URL" value={mcpUrl} />
                  <CopyField label="Bearer Token" value={bearerToken} />
                  <CopyField label="Header Name" value="Authorization" />
                </div>
                <Button
                  onClick={() => setStep(3)}
                  className="bg-violet-600 hover:bg-violet-500 text-white gap-2 w-full sm:w-auto"
                >
                  I've done this
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Step 4: Install Operator Style ── */}
        <Card
          className={`border-white/8 transition-all duration-300 ${
            ss(3) === "active"
              ? "bg-white/[0.04] border-violet-500/20"
              : "bg-white/[0.02]"
          }`}
        >
          <CardContent className={ss(3) === "done" ? "py-3 px-5" : "p-5"}>
            <StepHeader number={4} title={titles[3]} state={ss(3)} />
            {ss(3) === "active" && (
              <div className="mt-4 ml-10 space-y-4">
                <p className="text-white/50 text-sm leading-relaxed">
                  Copy this style and paste it into{" "}
                  <a
                    href="https://claude.ai/settings/styles"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-violet-400 hover:text-violet-300 inline-flex items-center gap-0.5"
                  >
                    claude.ai → Settings → Styles → New custom style
                    <ExternalLink className="h-3 w-3" />
                  </a>
                  . Name it{" "}
                  <strong className="text-white/70">Maestro Operator</strong>.
                </p>
                <div className="relative rounded-lg border border-white/8 bg-black/40 overflow-hidden">
                  <div className="absolute top-2.5 right-2.5 z-10">
                    <CopyBtn value={OPERATOR_STYLE_TEXT} label="Copy Style" />
                  </div>
                  <pre className="text-xs text-white/45 leading-relaxed p-4 pr-28 overflow-x-auto max-h-56 whitespace-pre-wrap font-mono">
                    {OPERATOR_STYLE_TEXT}
                  </pre>
                </div>
                <Button
                  onClick={() => setStep(4)}
                  className="bg-violet-600 hover:bg-violet-500 text-white gap-2 w-full sm:w-auto"
                >
                  I've done this
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* ── Step 5: First prompt ── */}
        <Card
          className={`border-white/8 transition-all duration-300 ${
            ss(4) === "active"
              ? "bg-white/[0.04] border-violet-500/20"
              : "bg-white/[0.02]"
          }`}
        >
          <CardContent className={ss(4) === "done" ? "py-3 px-5" : "p-5"}>
            <StepHeader number={5} title={titles[4]} state={ss(4)} />
            {ss(4) === "active" && (
              <div className="mt-4 ml-10 space-y-4">
                <p className="text-white/50 text-sm leading-relaxed">
                  Open a new{" "}
                  <a
                    href="https://claude.ai"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-violet-400 hover:text-violet-300"
                  >
                    claude.ai
                  </a>{" "}
                  conversation with your Maestro connector and{" "}
                  <strong className="text-white/70">Maestro Operator</strong> style
                  active. Paste this prompt:
                </p>
                <div className="relative rounded-lg border border-white/8 bg-black/40">
                  <div className="absolute top-2.5 right-2.5">
                    <CopyBtn
                      value="Spawn a Maestro session to print hello world from my VPS."
                      label="Copy"
                    />
                  </div>
                  <div className="flex items-start gap-2 p-4 pr-20">
                    <Zap className="h-4 w-4 text-violet-400 mt-0.5 shrink-0" />
                    <p className="text-sm text-violet-200 font-mono leading-relaxed">
                      Spawn a Maestro session to print hello world from my VPS.
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2 text-white/30 text-xs">
                  <Loader2 className="h-3 w-3 animate-spin shrink-0" />
                  Watching for your first MCP call…
                </div>
              </div>
            )}
            {ss(4) === "done" && firstCallDetected && (
              <p className="ml-10 text-xs text-green-400/60 mt-1">
                First call detected.
              </p>
            )}
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center py-4">
          <p className="text-white/20 text-xs">
            Need help?{" "}
            <a
              href="mailto:support@maestro.run"
              className="text-violet-400/60 hover:text-violet-300 transition-colors"
            >
              support@maestro.run
            </a>
          </p>
        </div>
      </main>
      <SupportWidget />
    </div>
  )
}
