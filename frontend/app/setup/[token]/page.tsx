"use client"

import { useState, useEffect, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  ExternalLink, Eye, EyeOff, Loader2, CheckCircle, AlertCircle,
  Server, RefreshCw, CreditCard,
} from "lucide-react"

const DO_TOKEN_RE = /^dop_v1_[0-9a-f]{64}$/i

const REGIONS = [
  { value: "nyc1", label: "New York 1 (NYC)", flag: "🇺🇸" },
  { value: "sfo3", label: "San Francisco 3 (SFO)", flag: "🇺🇸" },
  { value: "fra1", label: "Frankfurt 1 (FRA)", flag: "🇩🇪" },
  { value: "ams3", label: "Amsterdam 3 (AMS)", flag: "🇳🇱" },
  { value: "sgp1", label: "Singapore 1 (SGP)", flag: "🇸🇬" },
  { value: "lon1", label: "London 1 (LON)", flag: "🇬🇧" },
  { value: "blr1", label: "Bangalore 1 (BLR)", flag: "🇮🇳" },
  { value: "syd1", label: "Sydney 1 (SYD)", flag: "🇦🇺" },
]

const SIZES = [
  { value: "s-2vcpu-2gb", label: "Basic", spec: "2 vCPU / 2 GB", price: "$18/mo" },
  { value: "s-2vcpu-4gb", label: "Standard", spec: "2 vCPU / 4 GB", price: "$24/mo", recommended: true },
  { value: "s-4vcpu-8gb", label: "Pro", spec: "4 vCPU / 8 GB", price: "$48/mo" },
]

const STATUS_STEPS = [
  { key: "paid",           label: "Payment confirmed" },
  { key: "provisioning",  label: "Creating droplet" },
  { key: "installing",    label: "Installing Claude Code" },
  { key: "awaiting_oauth",label: "Awaiting Claude OAuth" },
  { key: "ready",         label: "Ready!" },
]

type ProvisionStatus =
  | "idle" | "submitting" | "paid" | "provisioning"
  | "installing" | "awaiting_oauth" | "ready"
  | "provisioning_failed" | "provisioning_timeout"
  | "api_key_invalid" | "account_no_credit" | "failed_install"
  | "error"

const ERROR_STATES: ProvisionStatus[] = [
  "provisioning_failed", "provisioning_timeout",
  "api_key_invalid", "account_no_credit", "failed_install", "error",
]

interface ErrorCardDef {
  title: string
  titleFr: string
  description: string
  descriptionFr: string
  extraAction?: React.ReactNode
  retryable?: boolean
}

const ERROR_CARD_DEFS: Partial<Record<ProvisionStatus, ErrorCardDef>> = {
  api_key_invalid: {
    title: "Invalid API key",
    titleFr: "Clé API invalide",
    description:
      "Your DigitalOcean API token was rejected (401). Check that the token is correct, has write permissions, and hasn't expired.",
    descriptionFr:
      "Votre token DigitalOcean a été refusé. Vérifiez qu'il est correct et dispose des permissions d'écriture.",
    extraAction: (
      <a
        href="https://cloud.digitalocean.com/account/api/tokens"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-violet-400 hover:text-violet-300"
      >
        Get a new API token <ExternalLink className="h-3.5 w-3.5" />
      </a>
    ),
    retryable: true,
  },
  account_no_credit: {
    title: "Insufficient DigitalOcean credit",
    titleFr: "Crédit DigitalOcean insuffisant",
    description:
      "Your DigitalOcean account has insufficient credit. Top up your balance, then retry.",
    descriptionFr:
      "Votre compte DigitalOcean n'a pas assez de crédit. Rechargez votre solde, puis réessayez.",
    extraAction: (
      <a
        href="https://cloud.digitalocean.com/account/billing"
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center gap-1.5 text-[13px] font-medium text-violet-400 hover:text-violet-300"
      >
        <CreditCard className="h-3.5 w-3.5" />
        Top up at DigitalOcean billing <ExternalLink className="h-3.5 w-3.5" />
      </a>
    ),
    retryable: true,
  },
  provisioning_failed: {
    title: "Provisioning failed",
    titleFr: "Échec du provisionnement",
    description:
      "The droplet encountered an error during boot. A full refund has been issued automatically (5–10 business days). You can retry with a different region.",
    descriptionFr:
      "Le serveur a rencontré une erreur. Un remboursement intégral a été initié automatiquement.",
    retryable: false,
  },
  provisioning_timeout: {
    title: "Provisioning timed out",
    titleFr: "Délai de provisionnement dépassé",
    description:
      "The droplet took too long to become active. A full refund has been issued. Please retry or contact support@concerto.run.",
    descriptionFr:
      "Le serveur a mis trop longtemps à démarrer. Un remboursement a été initié. Veuillez réessayer.",
    retryable: false,
  },
  failed_install: {
    title: "Installation timed out",
    titleFr: "Délai d'installation dépassé",
    description:
      "The Concerto installer did not complete within 8 minutes. A full refund has been issued. Please retry or contact support@concerto.run.",
    descriptionFr:
      "L'installateur n'a pas terminé dans les 8 minutes. Un remboursement a été initié.",
    retryable: false,
  },
}

function ErrorCard({
  def,
  onRetry,
}: {
  def: ErrorCardDef
  onRetry: () => void
}) {
  return (
    <div role="alert" className="mb-4 rounded-xl border border-red-500/20 bg-red-500/[0.06] p-5 space-y-3">
      <div className="flex items-start gap-2.5">
        <AlertCircle className="mt-0.5 h-4.5 w-4.5 shrink-0 text-red-400" />
        <div>
          <p className="text-[14px] font-semibold text-red-300">{def.title}</p>
          <p className="text-[12px] text-red-300/60 italic mt-0.5">{def.titleFr}</p>
        </div>
      </div>
      <p className="text-[13px] text-white/55 leading-relaxed">{def.description}</p>
      <p className="text-[12px] text-white/35 italic leading-relaxed">{def.descriptionFr}</p>
      <div className="flex flex-col gap-2 pt-1">
        {def.extraAction}
        {def.retryable && (
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="gap-2 border-white/10 bg-white/5 text-white/70 hover:bg-white/10"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Retry / Réessayer
          </Button>
        )}
        <a href="mailto:support@concerto.run" className="text-[12px] text-white/30 hover:text-white/50">
          Contact support@concerto.run
        </a>
      </div>
    </div>
  )
}

type PlanType = "solo" | "pro" | "byoc" | null

export default function SetupPage({ params }: { params: { token: string } }) {
  const router = useRouter()
  const [plan, setPlan]           = useState<PlanType>(null)
  const [doKey, setDoKey]         = useState("")
  const [doKeyErr, setDoKeyErr]   = useState("")
  const [showKey, setShowKey]     = useState(false)
  const [region, setRegion]       = useState("nyc1")
  const [size, setSize]           = useState("s-2vcpu-4gb")
  const [status, setStatus]       = useState<ProvisionStatus>("idle")
  const [serverErr, setServerErr] = useState("")
  const [retrying, setRetrying]   = useState(false)

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"
  const isHosted = plan === "solo" || plan === "pro"

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.json())
      .then((d) => {
        const p = d.plan as string
        if (p === "solo" || p === "pro" || p === "byoc") {
          setPlan(p)
        } else if (p === "hosted") {
          setPlan("solo") // legacy grandfathered
        } else {
          setPlan("byoc")
        }
      })
      .catch(() => setPlan("byoc"))
  }, [backendUrl, params.token])

  const validateKey = useCallback((val: string): string => {
    if (isHosted) return ""
    if (!val.trim()) return "API key is required."
    if (!DO_TOKEN_RE.test(val.trim()))
      return "Invalid format — DigitalOcean tokens start with dop_v1_ followed by 64 hex characters."
    return ""
  }, [isHosted])

  function pollStatus(token: string) {
    let attempts = 0
    const MAX = 120
    const poll = async () => {
      attempts++
      if (attempts > MAX) {
        setStatus("provisioning_timeout")
        return
      }
      try {
        const res = await fetch(`${backendUrl}/api/buyer/${token}/status`)
        if (!res.ok) { setTimeout(poll, 5000); return }
        const data = await res.json()
        const s = data.status as ProvisionStatus
        setStatus(s)
        if (s === "ready" || s === "awaiting_oauth") {
          setTimeout(() => router.push(`/dashboard/${token}`), 1200)
          return
        }
        if (!ERROR_STATES.includes(s)) setTimeout(poll, 5000)
      } catch {
        setTimeout(poll, 5000)
      }
    }
    poll()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const err = validateKey(doKey)
    if (err) { setDoKeyErr(err); return }

    setDoKeyErr("")
    setServerErr("")
    setStatus("submitting")
    setRetrying(false)

    try {
      // Pre-flight: validate DO key before provisioning (BYOC only)
      if (!isHosted) {
        const pf = await fetch(`${backendUrl}/api/preflight-do-key`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ do_api_key: doKey.trim() }),
        })
        if (!pf.ok) {
          const pfBody = await pf.json().catch(() => ({}))
          const detail = pfBody?.detail ?? pfBody
          const msg = typeof detail === "object" ? (detail.error ?? "Invalid API key") : String(detail)
          setDoKeyErr(msg)
          setStatus("idle")
          return
        }
      }

      const res = await fetch(`${backendUrl}/api/provision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          isHosted
            ? { token: params.token, region }
            : { token: params.token, do_api_key: doKey.trim(), region, size }
        ),
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.detail ?? `Server error ${res.status}`)
      }
      setStatus("paid")
      pollStatus(params.token)
    } catch (err: unknown) {
      setStatus("error")
      setServerErr(err instanceof Error ? err.message : "Unexpected error. Please try again.")
    }
  }

  const currentStepIndex = STATUS_STEPS.findIndex((s) => s.key === status)
  const isErrorState     = ERROR_STATES.includes(status)
  const isProvisioning   = !["idle", "submitting", "error"].includes(status) && !isErrorState
  const selectedSize     = SIZES.find((s) => s.value === size)
  const errorDef         = ERROR_CARD_DEFS[status]
  const showForm         = !isProvisioning || retrying

  const hostedSpec = plan === "pro"
    ? "Includes an 8 GB / 2-vCPU droplet — handles up to 6–8 parallel sessions."
    : "Includes a 4 GB / 2-vCPU droplet — handles up to 2 parallel sessions."

  const setupSubtitle = isHosted
    ? `Pick a region — we'll provision your ${plan === "pro" ? "8 GB / 2-vCPU" : "4 GB / 2-vCPU"} droplet automatically.`
    : "Enter your DigitalOcean API key to provision your dedicated droplet."

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#0a0a0b] px-6 py-16 text-white">
      <div className="w-full max-w-[440px]">

        {/* Logo */}
        <div className="mb-9 flex flex-col items-center gap-1.5 text-center">
          <svg width="32" height="32" viewBox="0 0 22 22" fill="none" aria-hidden="true">
            <rect width="22" height="22" rx="6" fill="#7c3aed" />
            <circle cx="11" cy="11" r="5.5" stroke="white" strokeWidth="1.25" fill="none" />
            <circle cx="11" cy="11" r="2" fill="white" />
          </svg>
          <h1 className="mt-3 text-2xl font-bold tracking-tight">Set up your Concerto</h1>
          <p className="text-sm text-white/40">{setupSubtitle}</p>
        </div>

        {/* Bilingual error card */}
        {isErrorState && errorDef && (
          <ErrorCard
            def={errorDef}
            onRetry={() => { setStatus("idle"); setRetrying(true) }}
          />
        )}

        {/* ── Form or Stepper ─────────────────────────────────── */}
        <div className="overflow-hidden rounded-2xl border border-white/[0.07] bg-white/[0.025]">

          {showForm ? (
            <div className="p-7">
              <form onSubmit={handleSubmit} className="space-y-6" noValidate>

                {/* Hosted: info banner */}
                {isHosted && (
                  <div className="flex items-start gap-3 rounded-xl border border-violet-500/20 bg-violet-500/8 px-4 py-3">
                    <Server className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" />
                    <p className="text-[13px] text-violet-300">
                      {hostedSpec} No DigitalOcean account required.
                    </p>
                  </div>
                )}

                {/* BYOC: DO API Key */}
                {!isHosted && (
                  <div className="space-y-2">
                    <Label htmlFor="do-key" className="text-[13px] font-medium text-white/60">
                      DigitalOcean API Key
                    </Label>
                    <div className="relative">
                      <Input
                        id="do-key"
                        type={showKey ? "text" : "password"}
                        value={doKey}
                        onChange={(e) => {
                          setDoKey(e.target.value)
                          if (doKeyErr) setDoKeyErr(validateKey(e.target.value))
                        }}
                        onBlur={() => setDoKeyErr(validateKey(doKey))}
                        placeholder="dop_v1_..."
                        aria-describedby={doKeyErr ? "do-key-err" : undefined}
                        aria-invalid={!!doKeyErr}
                        className={`h-11 bg-white/[0.04] pr-10 font-mono text-[13px] placeholder:text-white/20 focus-visible:ring-violet-500/50 ${
                          doKeyErr
                            ? "border-red-500/40 focus-visible:ring-red-500/40"
                            : "border-white/[0.08]"
                        }`}
                      />
                      <button
                        type="button"
                        onClick={() => setShowKey(!showKey)}
                        aria-label={showKey ? "Hide API key" : "Show API key"}
                        className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 transition-colors hover:text-white/60"
                      >
                        {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>

                    {doKeyErr && (
                      <div id="do-key-err" role="alert" className="flex items-start gap-1.5 text-[12px] text-red-400">
                        <AlertCircle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
                        {doKeyErr}
                      </div>
                    )}

                    <a
                      href="https://cloud.digitalocean.com/account/api/tokens"
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-[12px] text-violet-400 transition-colors hover:text-violet-300"
                    >
                      Get your API token <ExternalLink className="h-3 w-3" />
                    </a>
                  </div>
                )}

                {/* Region picker */}
                <div className="space-y-2">
                  <Label className="text-[13px] font-medium text-white/60">Region</Label>
                  <Select value={region} onValueChange={setRegion}>
                    <SelectTrigger className="h-11 border-white/[0.08] bg-white/[0.04] focus:ring-violet-500/50">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="border-white/[0.08] bg-[#18181c]">
                      {REGIONS.map((r) => (
                        <SelectItem
                          key={r.value}
                          value={r.value}
                          className="text-white focus:bg-white/10 focus:text-white"
                        >
                          <span className="mr-2">{r.flag}</span>
                          {r.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-[12px] text-white/25">Choose the region closest to you for lowest latency.</p>
                </div>

                {/* Size picker — BYOC only */}
                {!isHosted && (
                  <div className="space-y-2">
                    <Label className="text-[13px] font-medium text-white/60">VPS Size</Label>
                    <div className="grid grid-cols-3 gap-2">
                      {SIZES.map((s) => (
                        <button
                          key={s.value}
                          type="button"
                          onClick={() => setSize(s.value)}
                          className={`relative rounded-lg border p-3 text-left transition-all ${
                            size === s.value
                              ? "border-violet-500/50 bg-violet-500/10 ring-1 ring-violet-500/30"
                              : "border-white/[0.07] bg-white/[0.02] hover:border-white/20 hover:bg-white/[0.04]"
                          }`}
                        >
                          {s.recommended && (
                            <span className="absolute -top-2 left-1/2 -translate-x-1/2 rounded-full bg-violet-600 px-2 py-0.5 text-[10px] font-medium text-white">
                              Best
                            </span>
                          )}
                          <div className="text-[12px] font-semibold text-white">{s.label}</div>
                          <div className="mt-0.5 text-[11px] text-white/35">{s.spec}</div>
                          <div className="mt-1.5 text-[12px] font-medium text-violet-400">{s.price}</div>
                        </button>
                      ))}
                    </div>
                    <p className="text-[12px] text-white/25">
                      Billed directly by DigitalOcean to your account.
                      Selected: <span className="text-white/50">{selectedSize?.spec} — {selectedSize?.price}</span>
                    </p>
                  </div>
                )}

                {serverErr && (
                  <div role="alert" className="flex items-start gap-2 rounded-lg border border-red-500/20 bg-red-500/8 px-4 py-3 text-[13px] text-red-300">
                    <AlertCircle className="mt-0.5 h-4 w-4 shrink-0" />
                    {serverErr}
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={status === "submitting"}
                  className="h-11 w-full rounded-xl bg-white text-[14px] font-semibold text-black hover:bg-white/92 disabled:opacity-60"
                >
                  {status === "submitting" ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Provisioning…</>
                  ) : retrying ? (
                    "Retry Provisioning"
                  ) : (
                    "Provision My Concerto"
                  )}
                </Button>
              </form>
            </div>
          ) : (
            /* ── Provisioning stepper ──────────────────────────── */
            <div className="p-7">
              <div className="mb-5">
                <h2 className="text-[15px] font-semibold text-white">Provisioning your Concerto</h2>
                <p className="mt-1 text-[13px] text-white/40">This takes about 3–5 minutes. Don&apos;t close this tab.</p>
              </div>

              <div className="space-y-0">
                {STATUS_STEPS.map((step, i) => {
                  const isDone    = currentStepIndex > i
                  const isCurrent = currentStepIndex === i
                  const isLast    = i === STATUS_STEPS.length - 1

                  return (
                    <div key={step.key} className="flex gap-4">
                      <div className="flex flex-col items-center">
                        <div className="flex h-8 w-8 shrink-0 items-center justify-center">
                          {isDone ? (
                            <CheckCircle className="h-5 w-5 text-green-400" />
                          ) : isCurrent ? (
                            <Loader2 className="h-5 w-5 animate-spin text-violet-400" />
                          ) : (
                            <div className="h-5 w-5 rounded-full border-2 border-white/15" />
                          )}
                        </div>
                        {!isLast && (
                          <div className={`mt-0.5 w-px flex-1 ${isDone ? "bg-green-500/30" : "bg-white/8"}`} style={{ minHeight: "24px" }} />
                        )}
                      </div>

                      <div className="pb-6 pt-1">
                        <span
                          className={`text-[14px] ${
                            isDone    ? "text-green-400"
                            : isCurrent ? "font-medium text-white"
                            : "text-white/25"
                          }`}
                        >
                          {step.label}
                        </span>
                        {isCurrent && step.key === "installing" && (
                          <p className="mt-1 text-[12px] text-white/30">Installing npm, claude-code, cloudflared...</p>
                        )}
                        {isCurrent && step.key === "awaiting_oauth" && (
                          <p className="mt-1 text-[12px] text-white/30">A browser window will open — log in to Claude.</p>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
