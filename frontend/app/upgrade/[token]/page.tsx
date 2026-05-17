"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { ArrowRight, Check, Zap } from "lucide-react"

interface BuyerStatus {
  status: string
  plan: string
  expires_at?: number
}

function CheckItem({ children }: { children: React.ReactNode }) {
  return (
    <li className="flex items-start gap-3 text-sm">
      <span className="mt-0.5 flex h-4.5 w-4.5 shrink-0 items-center justify-center rounded-full bg-[rgba(217,119,87,0.15)]">
        <Check className="h-3 w-3 text-[#d97757]" />
      </span>
      <span className="text-[#c4b8aa]">{children}</span>
    </li>
  )
}

export default function UpgradePage({ params }: { params: { token: string } }) {
  const [status, setStatus] = useState<BuyerStatus | null>(null)
  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.ok ? r.json() : null)
      .then((d) => d && setStatus(d))
      .catch(() => {})
  }, [backendUrl, params.token])

  const checkoutSolo = `/api/checkout?plan=solo&trial_token=${params.token}`
  const checkoutPro  = `/api/checkout?plan=pro&trial_token=${params.token}`

  const expired = status?.status === "trial_expired"

  return (
    <div className="min-h-screen bg-[#0f0d10] text-[#f5f0e9]">
      {/* Nav */}
      <nav className="border-b border-[rgba(245,240,233,0.05)] px-6 py-4">
        <div className="mx-auto flex max-w-4xl items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5">
            <svg width="22" height="22" viewBox="0 0 200 200" fill="none" aria-hidden="true">
              <path d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69" fill="none" stroke="#d97757" strokeWidth={13} strokeLinecap="round"/>
              <path d="M 77.06 67.23 A 40 40 0 1 1 63.75 116.90"   fill="none" stroke="#b483ff" strokeWidth={13} strokeLinecap="round"/>
              <path d="M 157.12 110.07 A 58 58 0 1 1 119.84 45.50" fill="none" stroke="#8b7fff" strokeWidth={13} strokeLinecap="round"/>
              <circle cx="115.56" cy="115.56" r={16} fill="#d97757"/>
              <circle cx="61.36"  cy="89.65"  r={16} fill="#b483ff"/>
              <circle cx="150.23" cy="71.00"  r={16} fill="#8b7fff"/>
              <circle cx="100"    cy="100"    r={22} fill="#f5f0e9"/>
            </svg>
            <span className="font-medium tracking-tight">Concerto</span>
          </Link>
        </div>
      </nav>

      <div className="mx-auto max-w-3xl px-6 py-16">
        {/* Header */}
        <div className="mb-12 text-center">
          <div className="mb-4 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[rgba(217,119,87,0.15)]">
            <Zap className="h-6 w-6 text-[#d97757]" />
          </div>
          <h1 className="font-display mb-3 text-4xl font-[400] tracking-tight">
            {expired ? "Your trial ended." : "Keep your workspace alive."}
          </h1>
          <p className="text-lg text-[#877c70] leading-relaxed max-w-lg mx-auto">
            {expired
              ? "Your 30-minute trial workspace was destroyed. Upgrade to get a permanent workspace in 5 minutes."
              : "Your trial is running. Upgrade now to keep the workspace alive after the timer runs out."}
          </p>
        </div>

        {/* Pricing */}
        <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
          {/* Solo — recommended */}
          <div className="relative overflow-hidden rounded-2xl border border-[rgba(217,119,87,0.35)] bg-[#1a161c] p-8 shadow-[0_0_0_1px_rgba(217,119,87,0.15),0_8px_40px_rgba(217,119,87,0.10)]">
            <div className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-[rgba(217,119,87,0.55)] to-transparent" />
            <div className="relative">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-lg font-medium text-[#f5f0e9]">Solo</span>
                <Badge className="border-[rgba(217,119,87,0.35)] bg-[rgba(217,119,87,0.12)] text-xs text-[#e48a62]">
                  Recommended
                </Badge>
              </div>
              <p className="mb-1 text-sm text-[#877c70]">Dedicated workspace, 4GB memory</p>
              <div className="mt-5 flex items-baseline gap-2">
                <span className="font-display text-5xl font-[400] tracking-tight text-[#f5f0e9]">$49</span>
                <span className="text-sm text-[#877c70]">/month</span>
              </div>
              <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
              <ul className="space-y-3">
                {[
                  "Dedicated workspace, 4GB memory",
                  "Up to 2 parallel sessions",
                  "Email support included",
                  "Cancel anytime",
                ].map((f) => <CheckItem key={f}>{f}</CheckItem>)}
              </ul>
              <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
              <form action={checkoutSolo} method="POST">
                <Button type="submit" className="h-12 w-full rounded-xl text-base font-medium">
                  Start with Solo <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </form>
              <p className="mt-3 text-center text-xs text-[#877c70]">Secure via Stripe · Cancel anytime</p>
            </div>
          </div>

          {/* Pro */}
          <div className="relative overflow-hidden rounded-2xl border border-[rgba(245,240,233,0.08)] bg-[#1a161c] p-8">
            <div className="relative">
              <div className="mb-1 flex items-center justify-between">
                <span className="text-lg font-medium text-[#f5f0e9]">Pro</span>
              </div>
              <p className="mb-1 text-sm text-[#877c70]">Dedicated workspace, 8GB memory</p>
              <div className="mt-5 flex items-baseline gap-2">
                <span className="font-display text-5xl font-[400] tracking-tight text-[#f5f0e9]">$99</span>
                <span className="text-sm text-[#877c70]">/month</span>
              </div>
              <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
              <ul className="space-y-3">
                {[
                  "Dedicated workspace, 8GB memory",
                  "Up to 6–8 parallel sessions",
                  "Email support included",
                  "Cancel anytime",
                ].map((f) => <CheckItem key={f}>{f}</CheckItem>)}
              </ul>
              <Separator className="my-6 bg-[rgba(245,240,233,0.07)]" />
              <form action={checkoutPro} method="POST">
                <Button type="submit" variant="outline" className="h-12 w-full rounded-xl text-base font-medium">
                  Start with Pro
                </Button>
              </form>
              <p className="mt-3 text-center text-xs text-[#877c70]">Secure via Stripe · Cancel anytime</p>
            </div>
          </div>
        </div>

        <div className="mt-8 rounded-xl border border-[rgba(245,240,233,0.07)] bg-[#1a161c] px-6 py-4 text-center">
          <p className="text-sm text-[#877c70]">
            We recommend <strong className="text-[#c4b8aa]">Claude Max</strong> — Pro&apos;s token limits run out fast with agentic work.
          </p>
        </div>
      </div>
    </div>
  )
}
