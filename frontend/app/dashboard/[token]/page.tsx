"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import {
  Copy, Check, ExternalLink, Terminal, Zap,
  CalendarClock, AlertTriangle, Loader2,
  CreditCard, Ban, RefreshCw, RotateCcw,
} from "lucide-react"

function CopyField({ label, value }: { label: string; value: string }) {
  const [copied, setCopied]   = useState(false)
  const [flash, setFlash]     = useState(false)
  const timeoutRef            = useRef<ReturnType<typeof setTimeout> | null>(null)

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
    setFlash(true)
    if (timeoutRef.current) clearTimeout(timeoutRef.current)
    timeoutRef.current = setTimeout(() => {
      setCopied(false)
      setFlash(false)
    }, 2000)
  }

  return (
    <div className="space-y-1.5">
      <label className="text-[11px] font-medium uppercase tracking-widest text-white/35">
        {label}
      </label>
      <div
        className={`flex items-center gap-2 overflow-hidden rounded-lg border transition-colors duration-300 ${
          flash
            ? "border-green-500/30 bg-green-500/[0.06]"
            : "border-white/[0.07] bg-white/[0.03]"
        }`}
      >
        <code className="min-w-0 flex-1 break-all px-3 py-2.5 font-mono text-[13px] text-white/75">
          {value}
        </code>
        <button
          type="button"
          onClick={copy}
          aria-label={copied ? "Copied" : `Copy ${label}`}
          className={`mr-2 flex h-7 w-7 shrink-0 items-center justify-center rounded-md transition-all duration-200 ${
            copied
              ? "text-green-400"
              : "text-white/35 hover:bg-white/10 hover:text-white"
          }`}
        >
          {copied ? <Check className="h-3.5 w-3.5" /> : <Copy className="h-3.5 w-3.5" />}
        </button>
      </div>
      {copied && <p className="text-[11px] text-green-400">Copied to clipboard</p>}
    </div>
  )
}

function PastDueBanner() {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-yellow-500/25 bg-yellow-500/[0.07] px-5 py-4">
      <CreditCard className="mt-0.5 h-4.5 w-4.5 shrink-0 text-yellow-400" />
      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold text-yellow-300">Payment past due</p>
        <p className="mt-1 text-[13px] text-yellow-200/60 leading-relaxed">
          Your subscription payment failed. Update your payment method to avoid suspension.
        </p>
      </div>
      <a
        href="https://billing.stripe.com"
        target="_blank"
        rel="noopener noreferrer"
        className="shrink-0 mt-0.5 inline-flex items-center gap-1.5 rounded-lg bg-yellow-500/15 px-3 py-1.5 text-[13px] font-medium text-yellow-300 hover:bg-yellow-500/25 transition-colors"
      >
        Update billing <ExternalLink className="h-3.5 w-3.5" />
      </a>
    </div>
  )
}

function SuspendedBanner() {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-orange-500/25 bg-orange-500/[0.07] px-5 py-4">
      <Ban className="mt-0.5 h-4.5 w-4.5 shrink-0 text-orange-400" />
      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold text-orange-300">Workspace suspended</p>
        <p className="mt-1 text-[13px] text-orange-200/60 leading-relaxed">
          Your workspace is paused due to a failed payment. Your data is safe.
          Update your payment method to resume instantly.
        </p>
      </div>
      <a
        href="https://billing.stripe.com"
        target="_blank"
        rel="noopener noreferrer"
        className="shrink-0 mt-0.5 inline-flex items-center gap-1.5 rounded-lg bg-orange-500/15 px-3 py-1.5 text-[13px] font-medium text-orange-300 hover:bg-orange-500/25 transition-colors"
      >
        Resume billing <ExternalLink className="h-3.5 w-3.5" />
      </a>
    </div>
  )
}

function RefundedBanner() {
  return (
    <div role="alert" className="flex items-start gap-3 rounded-xl border border-blue-500/25 bg-blue-500/[0.07] px-5 py-4">
      <RotateCcw className="mt-0.5 h-4.5 w-4.5 shrink-0 text-blue-400" />
      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold text-blue-300">Refund processed</p>
        <p className="mt-1 text-[13px] text-blue-200/60 leading-relaxed">
          Your refund has been issued. Allow 5–10 business days.
          Questions? <a href="mailto:support@concerto.run" className="underline hover:text-blue-300">support@concerto.run</a>
        </p>
      </div>
    </div>
  )
}

function TerminalFallback({ vpsIp }: { vpsIp: string }) {
  return (
    <div className="p-5 space-y-3">
      <div className="flex items-center gap-2">
        <AlertTriangle className="h-4 w-4 text-yellow-400" />
        <span className="text-[13px] font-medium text-white/70">Terminal unavailable</span>
      </div>
      <p className="text-[13px] text-white/45 leading-relaxed">
        The browser terminal is temporarily unreachable. Connect via SSH while it recovers:
      </p>
      {vpsIp && (
        <pre className="rounded-lg bg-black/40 p-3 text-[12px] font-mono text-green-300 overflow-x-auto">
          {`ssh root@${vpsIp}`}
        </pre>
      )}
      <p className="text-[12px] text-white/30">
        Or{" "}
        <a href="mailto:support@concerto.run" className="text-violet-400 hover:text-violet-300">
          contact support
        </a>{" "}
        if the issue persists.
      </p>
    </div>
  )
}

function RefundButton({ token, backendUrl, eligible }: {
  token: string
  backendUrl: string
  eligible: boolean
}) {
  const [step, setStep]       = useState<"idle" | "confirming" | "done" | "error">("idle")
  const [loading, setLoading] = useState(false)
  const [errMsg, setErrMsg]   = useState("")

  async function doRefund() {
    setLoading(true)
    try {
      const res = await fetch(`${backendUrl}/api/buyer/${token}/refund`, { method: "POST" })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.detail?.message ?? body?.detail ?? "Refund request failed")
      }
      setStep("done")
    } catch (err: unknown) {
      setStep("error")
      setErrMsg(err instanceof Error ? err.message : "Unexpected error")
    } finally {
      setLoading(false)
    }
  }

  if (!eligible) return null

  if (step === "done") {
    return <p className="text-[12px] text-green-400">✓ Refund initiated — allow 5–10 business days.</p>
  }

  if (step === "confirming") {
    return (
      <div className="flex items-center gap-2 flex-wrap">
        <p className="text-[12px] text-white/50">Are you sure? This cannot be undone.</p>
        <Button
          variant="ghost"
          size="sm"
          onClick={doRefund}
          disabled={loading}
          className="h-7 px-3 text-[12px] text-red-400 hover:bg-red-500/10 hover:text-red-300"
        >
          {loading ? "Processing..." : "Yes, refund"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setStep("idle")}
          disabled={loading}
          className="h-7 px-3 text-[12px] text-white/30 hover:bg-white/5"
        >
          Cancel
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setStep("confirming")}
        className="h-7 gap-1.5 px-3 text-[12px] text-white/25 hover:bg-white/5 hover:text-white/50"
      >
        <RotateCcw className="h-3 w-3" />
        Request refund
      </Button>
      {step === "error" && <p className="text-[11px] text-red-400">{errMsg}</p>}
    </div>
  )
}

export default function DashboardPage({ params }: { params: { token: string } }) {
  const [dashData, setDashData] = useState<{
    mcp_url?: string
    bearer_token?: string
    plan?: string
    status?: string
    vps_ip?: string
    subscription_status?: string
    next_renewal_at?: number
    refund_eligible?: boolean
    refund_window_open?: boolean
  } | null>(null)
  const [terminalError, setTerminalError] = useState(false)
  const [terminalRetry, setTerminalRetry] = useState(0)

  const backendUrl  = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"
  const terminalUrl = `${backendUrl}/terminal/${params.token}`

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.json())
      .then((d) => setDashData({
        mcp_url: d.mcp_url,
        bearer_token: d.bearer_token,
        plan: d.plan,
        status: d.status,
        vps_ip: d.vps_ip,
        subscription_status: d.subscription_status,
        next_renewal_at: d.next_renewal_at,
        refund_eligible: d.refund_eligible,
        refund_window_open: d.refund_window_open,
      }))
      .catch(() => {})
  }, [backendUrl, params.token])

  const mcpUrl      = dashData?.mcp_url      ?? `${backendUrl}/mcp/${params.token}`
  const bearerToken = dashData?.bearer_token ?? "Loading..."
  const plan        = dashData?.plan ?? "byoc"
  const isHosted    = plan === "solo" || plan === "pro" || plan === "hosted"
  const status      = dashData?.status ?? "active"
  const vpsIp       = dashData?.vps_ip ?? ""

  const isSuspended = status === "suspended"
  const isRefunded  = status === "refunded"
  const isPastDue   = status === "subscription_past_due" || dashData?.subscription_status === "past_due"
  const isBanned    = isSuspended || isRefunded

  const nextRenewal = dashData?.next_renewal_at
    ? new Date(dashData.next_renewal_at * 1000).toLocaleDateString("en-US", {
        year: "numeric", month: "long", day: "numeric",
      })
    : null

  const planLabel = plan === "pro" ? "Pro" : plan === "solo" ? "Solo" : "BYOC"

  function getBadge() {
    if (isRefunded)  return <Badge className="shrink-0 border-blue-500/25 bg-blue-500/12 text-[12px] text-blue-400">Refunded</Badge>
    if (isSuspended) return <Badge className="shrink-0 border-orange-500/25 bg-orange-500/12 text-[12px] text-orange-400"><span className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full bg-orange-400" />Suspended</Badge>
    if (isPastDue)   return <Badge className="shrink-0 border-yellow-500/25 bg-yellow-500/12 text-[12px] text-yellow-400">Payment due</Badge>
    return (
      <Badge className="shrink-0 border-green-500/25 bg-green-500/12 text-[12px] text-green-400">
        <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
        Online
      </Badge>
    )
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <header className="border-b border-white/[0.05] bg-[#0a0a0b]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
              <rect width="22" height="22" rx="6" fill="#7c3aed" />
              <circle cx="11" cy="11" r="5.5" stroke="white" strokeWidth="1.25" fill="none" />
              <circle cx="11" cy="11" r="2" fill="white" />
            </svg>
            <span className="font-semibold tracking-tight text-white">Concerto</span>
            <Separator orientation="vertical" className="mx-1 h-4 bg-white/[0.1]" />
            <span className="min-w-0 max-w-[110px] truncate font-mono text-[13px] text-white/30 sm:max-w-[180px]">
              {params.token}
            </span>
            <span className="hidden text-[11px] font-medium text-white/25 sm:inline">{planLabel}</span>
          </div>
          {getBadge()}
        </div>
      </header>

      <main className="mx-auto max-w-5xl space-y-4 px-6 py-8">

        {isPastDue   && <PastDueBanner />}
        {isSuspended && <SuspendedBanner />}
        {isRefunded  && <RefundedBanner />}

        {/* Connect card */}
        {!isBanned && (
          <div className="relative overflow-hidden rounded-2xl border border-violet-500/20 bg-white/[0.025]">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-violet-500/45 to-transparent" />
            <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,rgba(124,58,237,0.07)_0%,transparent_70%)]" />

            <div className="relative p-6 md:p-8">
              <div className="mb-5 flex items-center gap-2.5">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-violet-500/15">
                  <Zap className="h-4.5 w-4.5 text-violet-400" />
                </div>
                <div>
                  <h2 className="text-[15px] font-semibold text-white">Connect to claude.ai</h2>
                  <p className="text-[13px] text-white/40">Settings → Connectors → Add custom connector.</p>
                </div>
              </div>

              <div className="space-y-4">
                <CopyField label="MCP URL"        value={mcpUrl} />
                <CopyField label="Bearer Token"   value={bearerToken} />
                <CopyField label="Connector Name" value="Concerto" />
              </div>

              <Separator className="my-6 bg-white/[0.06]" />

              <div className="space-y-3">
                <p className="text-[11px] font-medium uppercase tracking-widest text-white/30">Step-by-step</p>
                <ol className="space-y-3">
                  {[
                    <>Open <a href="https://claude.ai" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 text-violet-400 hover:text-violet-300">claude.ai <ExternalLink className="h-3 w-3" /></a> → your avatar → <strong className="font-medium text-white/70">Settings</strong></>,
                    <>Navigate to <strong className="font-medium text-white/70">Connectors</strong> → <strong className="font-medium text-white/70">Add custom connector</strong></>,
                    <>Paste the <strong className="font-medium text-white/70">MCP URL</strong> and <strong className="font-medium text-white/70">Bearer Token</strong> above, name it <strong className="font-medium text-white/70">Concerto</strong>, and click Save</>,
                  ].map((step, i) => (
                    <li key={i} className="flex items-start gap-3 text-[13px]">
                      <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-violet-500/18 text-[11px] font-medium text-violet-300">{i + 1}</span>
                      <span className="leading-relaxed text-white/45">{step}</span>
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          </div>
        )}

        {/* Terminal card */}
        {!isBanned && (
          <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02]">
            <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3.5">
              <div className="flex items-center gap-2 text-white/50">
                <Terminal className="h-4 w-4" />
                <span className="text-[14px] font-medium">Browser Terminal</span>
                {terminalError && <span className="ml-1 text-[12px] text-yellow-400">— unavailable</span>}
              </div>
              <div className="flex items-center gap-2">
                {terminalError && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => { setTerminalError(false); setTerminalRetry(r => r + 1) }}
                    className="h-7 gap-1.5 px-2.5 text-[12px] text-white/35 hover:bg-white/8 hover:text-white"
                  >
                    <RefreshCw className="h-3 w-3" /> Retry
                  </Button>
                )}
                <Button
                  asChild
                  variant="ghost"
                  size="sm"
                  className="h-7 gap-1.5 px-2.5 text-[12px] text-white/35 hover:bg-white/8 hover:text-white"
                >
                  <a href={terminalUrl} target="_blank" rel="noopener noreferrer">
                    Open in new tab <ExternalLink className="h-3 w-3" />
                  </a>
                </Button>
              </div>
            </div>

            <div className="bg-[#0d0d10]">
              <div className="flex items-center gap-2 border-b border-white/[0.04] bg-black/20 px-4 py-2.5">
                <span className="h-2.5 w-2.5 rounded-full bg-red-500/55" />
                <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/55" />
                <span className="h-2.5 w-2.5 rounded-full bg-green-500/55" />
                <span className="ml-2 font-mono text-[11px] text-white/20">concerto · shell</span>
              </div>
              {terminalError ? (
                <TerminalFallback vpsIp={vpsIp} />
              ) : (
                <iframe
                  key={terminalRetry}
                  src={terminalUrl}
                  className="h-[500px] w-full border-0 md:h-[560px]"
                  title="Concerto Terminal"
                  allow="clipboard-read; clipboard-write"
                  onError={() => setTerminalError(true)}
                />
              )}
            </div>
          </div>
        )}

        {/* Subscription panel — Solo + Pro only */}
        {isHosted && !isBanned && (
          <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.025] p-6 space-y-4">
            <div className="flex items-center gap-2">
              <CalendarClock className="h-4 w-4 text-violet-400" />
              <span className="text-[14px] font-semibold text-white">Subscription</span>
            </div>
            <div className="h-px bg-white/[0.07]" />
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-white/40">Plan</span>
              <span className="text-white/70">{planLabel} — {plan === "pro" ? "$99/month" : "$49/month"}</span>
            </div>
            <div className="flex items-center justify-between text-[13px]">
              <span className="text-white/40">Status</span>
              <span className="text-white/70 capitalize">{dashData?.subscription_status ?? "active"}</span>
            </div>
            {nextRenewal && (
              <div className="flex items-center justify-between text-[13px]">
                <span className="text-white/40">Next renewal</span>
                <span className="text-white/70">{nextRenewal}</span>
              </div>
            )}
            <div className="h-px bg-white/[0.07]" />
            <a
              href="https://billing.stripe.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-[13px] text-white/60 transition-colors hover:border-violet-500/30 hover:bg-violet-500/8 hover:text-white"
            >
              <CreditCard className="h-3.5 w-3.5" />
              Manage subscription via Stripe
              <ExternalLink className="h-3.5 w-3.5" />
            </a>
            <p className="text-center text-[11px] text-white/20">
              Cancel, update payment method, or download invoices. Need to upgrade Solo → Pro? Email support@concerto.run.
            </p>
          </div>
        )}

        {/* BYOC: one-time purchase note */}
        {!isHosted && !isBanned && (
          <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.025] p-6">
            <p className="text-[13px] text-white/40">
              BYOC — one-time purchase. No subscription to manage.
              Your droplet runs in your own DigitalOcean account.
            </p>
          </div>
        )}

        {/* Refund + Support */}
        <div className="flex flex-col items-center gap-2 pb-4">
          {dashData?.refund_window_open && (
            <RefundButton
              token={params.token}
              backendUrl={backendUrl}
              eligible={dashData?.refund_eligible ?? false}
            />
          )}
          <p className="text-center text-[13px] text-white/25">
            Need help?{" "}
            <a href="mailto:support@concerto.run" className="text-violet-400 transition-colors hover:text-violet-300">
              support@concerto.run
            </a>
          </p>
        </div>
      </main>
    </div>
  )
}
