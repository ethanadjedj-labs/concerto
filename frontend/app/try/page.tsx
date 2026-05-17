"use client"

import { useState } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { ArrowRight, Clock, Zap, Shield } from "lucide-react"

export default function TryPage() {
  const [email, setEmail]     = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError]     = useState("")
  const [done, setDone]       = useState(false)
  const [dashUrl, setDashUrl] = useState("")

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    if (!email.includes("@")) {
      setError("Please enter a valid email address.")
      return
    }
    setLoading(true)
    try {
      const res = await fetch(`${backendUrl}/api/trial/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email: email.trim(), honeypot: "" }),
      })
      if (res.status === 409) {
        setError("This email has already used a free trial. You can upgrade at any time.")
        return
      }
      if (res.status === 429) {
        setError("Only one trial per IP per 24 hours. Try again tomorrow.")
        return
      }
      if (!res.ok) {
        const data = await res.json().catch(() => ({}))
        setError(data?.detail?.message ?? "Something went wrong. Please try again.")
        return
      }
      const data = await res.json()
      setDashUrl(data.dashboard_url)
      setDone(true)
    } catch {
      setError("Network error. Please try again.")
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return (
      <div className="min-h-screen bg-[#0f0d10] text-[#f5f0e9] flex items-center justify-center px-6">
        <div className="max-w-md w-full text-center space-y-6">
          <div className="flex justify-center">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-[rgba(217,119,87,0.15)]">
              <Zap className="h-7 w-7 text-[#d97757]" />
            </div>
          </div>
          <div>
            <h1 className="font-display text-3xl font-[450] tracking-tight mb-3">
              Your workspace is spinning up.
            </h1>
            <p className="text-[#877c70] leading-relaxed">
              We&apos;re provisioning your droplet. Takes about 3 minutes.
              We&apos;ll send a confirmation to <strong className="text-[#c4b8aa]">{email}</strong> when it&apos;s ready.
            </p>
          </div>
          <a
            href={dashUrl}
            className="inline-flex items-center gap-2 rounded-xl bg-[#d97757] px-8 py-3.5 text-base font-medium text-white hover:bg-[#c96848] transition-colors"
          >
            Open Dashboard <ArrowRight className="h-4 w-4" />
          </a>
          <p className="text-sm text-[#6e645a]">
            <Clock className="inline h-3.5 w-3.5 mr-1 align-middle" />
            Trial lasts 30 minutes, then auto-destroyed.
          </p>
        </div>
      </div>
    )
  }

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
          <Link href="/#pricing" className="text-sm text-[#877c70] hover:text-[#f5f0e9] transition-colors">
            See pricing
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <div className="mx-auto max-w-4xl px-6 py-20">
        <div className="mx-auto max-w-lg text-center">
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-[rgba(217,119,87,0.3)] bg-[rgba(217,119,87,0.08)] px-4 py-1.5 text-sm font-medium text-[#e48a62]">
            <Clock className="h-3.5 w-3.5" />
            30-minute free trial — no card needed
          </div>

          <h1 className="font-display mb-4 text-4xl font-[400] leading-[1.08] tracking-[-0.02em] sm:text-5xl">
            Try Concerto free.{" "}
            <span className="bg-gradient-to-r from-[#d97757] to-[#8b7fff] bg-clip-text text-transparent">
              30 minutes on us.
            </span>
          </h1>

          <p className="mb-10 text-lg text-[#877c70] leading-relaxed">
            We provision a real workspace, you connect claude.ai, and run actual Claude Code sessions.
            No credit card. No commitment. Auto-destroyed at the end.
          </p>

          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Honeypot — hidden from real users */}
            <input
              type="text"
              name="website"
              tabIndex={-1}
              aria-hidden="true"
              className="absolute -left-[9999px]"
              autoComplete="off"
            />

            <div className="flex flex-col gap-3 sm:flex-row">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
                autoFocus
                className="flex-1 rounded-xl border border-[rgba(245,240,233,0.12)] bg-[rgba(245,240,233,0.04)] px-4 py-3 text-[#f5f0e9] placeholder-[#6e645a] outline-none focus:border-[rgba(217,119,87,0.5)] focus:ring-2 focus:ring-[rgba(217,119,87,0.15)] transition-all"
              />
              <Button
                type="submit"
                disabled={loading || !email}
                className="h-12 rounded-xl px-6 font-medium sm:shrink-0"
              >
                {loading ? "Starting…" : (
                  <>Start trial <ArrowRight className="ml-1.5 h-4 w-4" /></>
                )}
              </Button>
            </div>

            {error && (
              <p className="rounded-lg border border-red-500/25 bg-red-500/[0.07] px-4 py-2.5 text-sm text-red-300">
                {error}
              </p>
            )}
          </form>

          <p className="mt-4 text-xs text-[#6e645a]">
            One trial per email. We destroy the workspace when time runs out.
          </p>
        </div>

        {/* What you get */}
        <div className="mt-20 grid grid-cols-1 gap-4 sm:grid-cols-3">
          {[
            {
              icon: <Zap className="h-5 w-5 text-[#d97757]" />,
              bg: "bg-[rgba(217,119,87,0.12)]",
              title: "Real workspace",
              desc: "A dedicated s-2vcpu-4gb droplet. Not a sandbox. Real git, real tests, real deploys.",
            },
            {
              icon: <svg width="20" height="20" viewBox="0 0 200 200" fill="none" aria-hidden="true">
                <path d="M 105.69 121.25 A 22 22 0 1 1 121.25 105.69" fill="none" stroke="#d97757" strokeWidth={16} strokeLinecap="round"/>
                <circle cx="115.56" cy="115.56" r={20} fill="#d97757"/>
              </svg>,
              bg: "bg-[rgba(217,119,87,0.08)]",
              title: "Full OAuth connector",
              desc: "Connect claude.ai exactly like paying customers. Same MCP flow, same dashboard.",
            },
            {
              icon: <Shield className="h-5 w-5 text-[#8b7fff]" />,
              bg: "bg-[rgba(139,127,255,0.12)]",
              title: "Auto-destroyed",
              desc: "After 30 minutes the droplet is gone. No surprise charges. No cleanup needed.",
            },
          ].map(({ icon, bg, title, desc }) => (
            <div
              key={title}
              className="rounded-xl border border-[rgba(245,240,233,0.07)] bg-[#1a161c] p-6"
            >
              <div className={`mb-4 flex h-10 w-10 items-center justify-center rounded-lg ${bg}`}>
                {icon}
              </div>
              <h3 className="mb-1.5 text-[15px] font-medium text-[#f5f0e9]">{title}</h3>
              <p className="text-sm leading-relaxed text-[#877c70]">{desc}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
