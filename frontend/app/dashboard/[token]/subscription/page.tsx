"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Loader2, ExternalLink, ArrowLeft, CreditCard, FileText, XCircle } from "lucide-react"
import Link from "next/link"

export default function SubscriptionPage({ params }: { params: { token: string } }) {
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState<string | null>(null)

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.maestro.run"

  async function openPortal() {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${backendUrl}/api/customer-portal-session`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token: params.token }),
      })
      if (!res.ok) {
        const d = await res.json().catch(() => ({}))
        throw new Error((d as { detail?: string }).detail ?? `HTTP ${res.status}`)
      }
      const { url } = (await res.json()) as { url: string }
      window.location.href = url
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to open portal")
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#0a0a0b] text-white">
      <header className="border-b border-white/[0.05] bg-[#0a0a0b]/80 backdrop-blur-xl">
        <div className="mx-auto flex max-w-5xl items-center px-6 py-4">
          <Link
            href={`/dashboard/${params.token}`}
            className="flex items-center gap-2 text-[13px] text-white/40 transition-colors hover:text-white/70"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-md px-6 py-16 text-center">
        <div className="mx-auto mb-6 flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-500/15">
          <CreditCard className="h-7 w-7 text-violet-400" />
        </div>

        <h1 className="mb-2 text-2xl font-bold tracking-tight">Manage Subscription</h1>
        <p className="mb-8 text-[14px] leading-relaxed text-white/40">
          Update your payment method, download invoices, or cancel your Maestro Hosted plan.
          You&apos;ll be taken to Stripe&apos;s secure customer portal.
        </p>

        <div className="mb-8 rounded-xl border border-white/[0.07] bg-white/[0.025] p-5 text-left">
          <p className="mb-3 text-[11px] font-medium uppercase tracking-widest text-white/30">
            Available in portal
          </p>
          <ul className="space-y-2.5">
            {[
              { icon: <CreditCard className="h-3.5 w-3.5 text-violet-400" />, text: "Update payment method" },
              { icon: <FileText    className="h-3.5 w-3.5 text-violet-400" />, text: "View & download invoices" },
              { icon: <XCircle     className="h-3.5 w-3.5 text-red-400/70"  />, text: "Cancel subscription (72h grace period)" },
            ].map(({ icon, text }) => (
              <li key={text} className="flex items-center gap-2.5 text-[13px] text-white/55">
                {icon}
                {text}
              </li>
            ))}
          </ul>
        </div>

        <Button
          onClick={openPortal}
          disabled={loading}
          className="w-full bg-violet-600 py-5 font-medium text-white hover:bg-violet-500 disabled:opacity-60"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Opening Stripe Portal…
            </>
          ) : (
            <>
              Manage Subscription
              <ExternalLink className="ml-2 h-4 w-4" />
            </>
          )}
        </Button>

        {error && (
          <p className="mt-4 text-[13px] text-red-400">{error}</p>
        )}

        <p className="mt-6 text-[12px] text-white/25">
          Questions?{" "}
          <a href="mailto:support@maestro.run" className="text-violet-400/70 hover:text-violet-400">
            support@maestro.run
          </a>
        </p>
      </main>
    </div>
  )
}
