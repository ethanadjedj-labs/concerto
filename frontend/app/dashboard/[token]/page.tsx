"use client"

import { useState, useEffect, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Copy, Check, ExternalLink, Terminal, Zap, CalendarClock, AlertTriangle, Loader2 } from "lucide-react"

/* ─── Copy field with flash feedback ─────────────────────────── */

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
          {copied ? (
            <Check className="h-3.5 w-3.5" />
          ) : (
            <Copy className="h-3.5 w-3.5" />
          )}
        </button>
      </div>
      {copied && (
        <p className="text-[11px] text-green-400">Copied to clipboard</p>
      )}
    </div>
  )
}

/* ─── Dashboard page ─────────────────────────────────────────── */

export default function DashboardPage({ params }: { params: { token: string } }) {
  const [dashData, setDashData] = useState<{
    mcp_url?: string
    bearer_token?: string
    plan?: string
    subscription_status?: string
    next_renewal_at?: number
  } | null>(null)
  const [cancelling, setCancelling] = useState(false)
  const [cancelDone, setCancelDone] = useState(false)

  const backendUrl  = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.maestro.run"
  const terminalUrl = `${backendUrl}/terminal/${params.token}`

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.json())
      .then((d) => setDashData({
        mcp_url: d.mcp_url,
        bearer_token: d.bearer_token,
        plan: d.plan,
        subscription_status: d.subscription_status,
        next_renewal_at: d.next_renewal_at,
      }))
      .catch(() => {})
  }, [backendUrl, params.token])

  const mcpUrl      = dashData?.mcp_url      ?? `${backendUrl}/mcp/${params.token}`
  const bearerToken = dashData?.bearer_token ?? "Loading..."
  const isHosted    = dashData?.plan === "hosted"
  const nextRenewal = dashData?.next_renewal_at
    ? new Date(dashData.next_renewal_at * 1000).toLocaleDateString("en-US", {
        year: "numeric", month: "long", day: "numeric",
      })
    : null

  async function cancelSubscription() {
    if (!confirm("Cancel your Hosted subscription? Your droplet stays live for 72 hours after cancellation.")) return
    setCancelling(true)
    try {
      const res = await fetch(`${backendUrl}/api/buyer/${params.token}/cancel`, { method: "POST" })
      if (res.ok) setCancelDone(true)
    } finally {
      setCancelling(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      {/* ── Top bar ──────────────────────────────────────────── */}
      <header className="border-b border-white/[0.05] bg-[#0a0a0b]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
          <div className="flex min-w-0 items-center gap-3">
            <svg width="22" height="22" viewBox="0 0 22 22" fill="none" aria-hidden="true">
              <rect width="22" height="22" rx="6" fill="#7c3aed" />
              <circle cx="11" cy="11" r="5.5" stroke="white" strokeWidth="1.25" fill="none" />
              <circle cx="11" cy="11" r="2" fill="white" />
            </svg>
            <span className="font-semibold tracking-tight text-white">Maestro</span>
            <Separator orientation="vertical" className="mx-1 h-4 bg-white/[0.1]" />
            <span className="min-w-0 max-w-[110px] truncate font-mono text-[13px] text-white/30 sm:max-w-[180px]">
              {params.token}
            </span>
          </div>

          <Badge className="shrink-0 border-green-500/25 bg-green-500/12 text-[12px] text-green-400">
            <span className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full bg-green-400" />
            Online
          </Badge>
        </div>
      </header>

      {/* ── Main ─────────────────────────────────────────────── */}
      <main className="mx-auto max-w-5xl space-y-6 px-6 py-8">

        {/* Connect card */}
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
                <p className="text-[13px] text-white/40">
                  Settings → Connectors → Add custom connector.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <CopyField label="MCP URL"       value={mcpUrl} />
              <CopyField label="Bearer Token"  value={bearerToken} />
              <CopyField label="Connector Name" value="Maestro" />
            </div>

            <Separator className="my-6 bg-white/[0.06]" />

            <div className="space-y-3">
              <p className="text-[11px] font-medium uppercase tracking-widest text-white/30">
                Step-by-step
              </p>
              <ol className="space-y-3">
                {[
                  <>Open <a href="https://claude.ai" target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-0.5 text-violet-400 hover:text-violet-300">claude.ai <ExternalLink className="h-3 w-3" /></a> → your avatar → <strong className="font-medium text-white/70">Settings</strong></>,
                  <>Navigate to <strong className="font-medium text-white/70">Connectors</strong> → <strong className="font-medium text-white/70">Add custom connector</strong></>,
                  <>Paste the <strong className="font-medium text-white/70">MCP URL</strong> and <strong className="font-medium text-white/70">Bearer Token</strong> above, name it <strong className="font-medium text-white/70">Maestro</strong>, and click Save</>,
                ].map((step, i) => (
                  <li key={i} className="flex items-start gap-3 text-[13px]">
                    <span className="mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-violet-500/18 text-[11px] font-medium text-violet-300">
                      {i + 1}
                    </span>
                    <span className="leading-relaxed text-white/45">{step}</span>
                  </li>
                ))}
              </ol>
            </div>
          </div>
        </div>

        {/* Terminal card */}
        <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.02]">
          <div className="flex items-center justify-between border-b border-white/[0.06] px-5 py-3.5">
            <div className="flex items-center gap-2 text-white/50">
              <Terminal className="h-4 w-4" />
              <span className="text-[14px] font-medium">Browser Terminal</span>
            </div>
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

          <div className="bg-[#0d0d10]">
            {/* Fake terminal titlebar */}
            <div className="flex items-center gap-2 border-b border-white/[0.04] bg-black/20 px-4 py-2.5">
              <span className="h-2.5 w-2.5 rounded-full bg-red-500/55" />
              <span className="h-2.5 w-2.5 rounded-full bg-yellow-500/55" />
              <span className="h-2.5 w-2.5 rounded-full bg-green-500/55" />
              <span className="ml-2 font-mono text-[11px] text-white/20">maestro · shell</span>
            </div>
            <iframe
              src={terminalUrl}
              className="h-[500px] w-full border-0 md:h-[560px]"
              title="Maestro Terminal"
              allow="clipboard-read; clipboard-write"
            />
          </div>
        </div>

        {/* Support */}
        <p className="pb-4 text-center text-[13px] text-white/25">
          Need help?{" "}
          <a href="mailto:support@maestro.run" className="text-violet-400 transition-colors hover:text-violet-300">
            support@maestro.run
          </a>
        </p>
      </main>
    </div>
  )
}
