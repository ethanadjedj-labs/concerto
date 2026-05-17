"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Separator } from "@/components/ui/separator"
import { ExternalLink, Eye, EyeOff, Loader2, CheckCircle } from "lucide-react"

const REGIONS = [
  { value: "nyc1", label: "New York 1 (NYC)" },
  { value: "sfo3", label: "San Francisco 3 (SFO)" },
  { value: "fra1", label: "Frankfurt 1 (FRA)" },
  { value: "ams3", label: "Amsterdam 3 (AMS)" },
  { value: "sgp1", label: "Singapore 1 (SGP)" },
  { value: "lon1", label: "London 1 (LON)" },
  { value: "blr1", label: "Bangalore 1 (BLR)" },
  { value: "syd1", label: "Sydney 1 (SYD)" },
]

const SIZES = [
  { value: "s-2vcpu-2gb", label: "Basic — 2 vCPU / 2 GB — $18/mo" },
  { value: "s-2vcpu-4gb", label: "Standard — 2 vCPU / 4 GB — $24/mo (recommended)" },
  { value: "s-4vcpu-8gb", label: "Pro — 4 vCPU / 8 GB — $48/mo" },
]

const STATUS_STEPS = [
  { key: "paid", label: "Payment confirmed" },
  { key: "provisioning", label: "Creating droplet" },
  { key: "installing", label: "Installing Claude Code" },
  { key: "awaiting_oauth", label: "Awaiting Claude OAuth" },
  { key: "ready", label: "Ready!" },
]

type ProvisionStatus =
  | "idle"
  | "submitting"
  | "paid"
  | "provisioning"
  | "installing"
  | "awaiting_oauth"
  | "ready"
  | "error"

export default function SetupPage({ params }: { params: { token: string } }) {
  const router = useRouter()
  const [doKey, setDoKey] = useState("")
  const [showKey, setShowKey] = useState(false)
  const [region, setRegion] = useState("nyc1")
  const [size, setSize] = useState("s-2vcpu-4gb")
  const [status, setStatus] = useState<ProvisionStatus>("idle")
  const [error, setError] = useState("")

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.maestro.run"

  async function pollStatus(token: string) {
    const maxAttempts = 120
    let attempts = 0

    const poll = async () => {
      attempts++
      if (attempts > maxAttempts) {
        setStatus("error")
        setError("Provisioning timed out. Please contact support@maestro.run.")
        return
      }

      try {
        const res = await fetch(`${backendUrl}/api/buyer/${token}/status`)
        if (!res.ok) {
          setTimeout(poll, 5000)
          return
        }
        const data = await res.json()
        const s = data.status as ProvisionStatus

        setStatus(s)

        if (s === "ready") {
          setTimeout(() => router.push(`/dashboard/${token}`), 1200)
          return
        }

        if (s !== "error") {
          setTimeout(poll, 5000)
        }
      } catch {
        setTimeout(poll, 5000)
      }
    }

    poll()
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!doKey.trim()) {
      setError("DigitalOcean API key is required.")
      return
    }

    setError("")
    setStatus("submitting")

    try {
      const res = await fetch(`${backendUrl}/api/provision`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          token: params.token,
          do_api_key: doKey,
          region,
          size,
        }),
      })

      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(body?.detail ?? `Server error ${res.status}`)
      }

      setStatus("paid")
      pollStatus(params.token)
    } catch (err: unknown) {
      setStatus("error")
      setError(err instanceof Error ? err.message : "Unexpected error. Please try again.")
    }
  }

  const currentStepIndex = STATUS_STEPS.findIndex((s) => s.key === status)
  const isProvisioning = !["idle", "submitting", "error"].includes(status)

  return (
    <div className="min-h-screen bg-[#0a0a0a] text-white flex items-center justify-center px-6 py-12">
      <div className="max-w-lg w-full">
        <div className="mb-8 text-center">
          <div className="flex items-center justify-center gap-2 mb-6">
            <div className="h-7 w-7 rounded bg-gradient-to-br from-violet-500 to-indigo-600" />
            <span className="font-semibold text-white text-lg">Maestro</span>
          </div>
          <h1 className="text-2xl font-bold mb-2">Set up your Maestro</h1>
          <p className="text-white/40 text-sm">
            Enter your DigitalOcean API key to provision your dedicated droplet.
          </p>
        </div>

        {!isProvisioning ? (
          <Card className="bg-white/[0.04] border-white/8">
            <CardContent className="pt-6">
              <form onSubmit={handleSubmit} className="space-y-6">
                <div className="space-y-2">
                  <Label htmlFor="do-key" className="text-white/70">
                    DigitalOcean API Key
                  </Label>
                  <div className="relative">
                    <Input
                      id="do-key"
                      type={showKey ? "text" : "password"}
                      value={doKey}
                      onChange={(e) => setDoKey(e.target.value)}
                      placeholder="dop_v1_..."
                      className="bg-white/5 border-white/10 text-white placeholder:text-white/20 pr-10"
                      required
                    />
                    <button
                      type="button"
                      onClick={() => setShowKey(!showKey)}
                      className="absolute right-3 top-1/2 -translate-y-1/2 text-white/30 hover:text-white/60 transition-colors"
                    >
                      {showKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                    </button>
                  </div>
                  <a
                    href="https://cloud.digitalocean.com/account/api/tokens"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-xs text-violet-400 hover:text-violet-300 transition-colors mt-1"
                  >
                    Get your API token <ExternalLink className="h-3 w-3" />
                  </a>
                </div>

                <div className="space-y-2">
                  <Label className="text-white/70">Region</Label>
                  <Select value={region} onValueChange={setRegion}>
                    <SelectTrigger className="bg-white/5 border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#1a1a1a] border-white/10">
                      {REGIONS.map((r) => (
                        <SelectItem key={r.value} value={r.value} className="text-white focus:bg-white/10 focus:text-white">
                          {r.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-white/25 text-xs">Choose the region closest to you.</p>
                </div>

                <div className="space-y-2">
                  <Label className="text-white/70">VPS Size</Label>
                  <Select value={size} onValueChange={setSize}>
                    <SelectTrigger className="bg-white/5 border-white/10 text-white">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent className="bg-[#1a1a1a] border-white/10">
                      {SIZES.map((s) => (
                        <SelectItem key={s.value} value={s.value} className="text-white focus:bg-white/10 focus:text-white">
                          {s.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                  <p className="text-white/25 text-xs">
                    Billed directly by DigitalOcean to your account.
                  </p>
                </div>

                {error && (
                  <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                    {error}
                  </div>
                )}

                <Button
                  type="submit"
                  disabled={status === "submitting"}
                  className="w-full bg-white text-black hover:bg-white/90 font-semibold h-11 rounded-lg"
                >
                  {status === "submitting" ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Provisioning...
                    </>
                  ) : (
                    "Provision My Maestro →"
                  )}
                </Button>
              </form>
            </CardContent>
          </Card>
        ) : (
          <Card className="bg-white/[0.04] border-white/8">
            <CardHeader>
              <CardTitle className="text-white text-lg">Provisioning your Maestro</CardTitle>
              <p className="text-white/40 text-sm">This takes about 3–5 minutes. Don&apos;t close this tab.</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <Separator className="bg-white/10" />
              {STATUS_STEPS.map((step, i) => {
                const isDone = currentStepIndex > i
                const isCurrent = currentStepIndex === i
                return (
                  <div key={step.key} className="flex items-center gap-4">
                    <div className="h-8 w-8 rounded-full flex items-center justify-center shrink-0">
                      {isDone ? (
                        <CheckCircle className="h-5 w-5 text-green-400" />
                      ) : isCurrent ? (
                        <Loader2 className="h-5 w-5 text-violet-400 animate-spin" />
                      ) : (
                        <div className="h-5 w-5 rounded-full border-2 border-white/15" />
                      )}
                    </div>
                    <span
                      className={
                        isDone
                          ? "text-green-400 text-sm"
                          : isCurrent
                          ? "text-white text-sm font-medium"
                          : "text-white/25 text-sm"
                      }
                    >
                      {step.label}
                    </span>
                  </div>
                )
              })}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
