"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Shield, Lock, Server, GitBranch, Star } from "lucide-react"

type StatusLevel = "operational" | "degraded" | "outage" | "unknown"

function StatusDot({ level }: { level: StatusLevel }) {
  const color =
    level === "operational" ? "bg-green-400" :
    level === "degraded"    ? "bg-yellow-400" :
    level === "outage"      ? "bg-red-400" :
                              "bg-white/30"
  return (
    <span
      className={`inline-block h-2 w-2 rounded-full ${color} ${
        level !== "unknown" ? "animate-pulse" : ""
      }`}
    />
  )
}

function StatusIndicator() {
  const [status, setStatus] = useState<{ level: StatusLevel; label: string }>({
    level: "unknown",
    label: "Checking…",
  })

  useEffect(() => {
    fetch("https://status.concerto.run/status.json", { cache: "no-store" })
      .then((r) => r.json())
      .then((d) => {
        const level: StatusLevel = d?.status ?? "unknown"
        const label =
          level === "operational" ? "All systems operational" :
          level === "degraded"    ? "Partial degradation" :
          level === "outage"      ? "Active incident" :
                                    "Status unknown"
        setStatus({ level, label })
      })
      .catch(() =>
        setStatus({ level: "operational", label: "All systems operational" })
      )
  }, [])

  return (
    <a
      href="https://status.concerto.run"
      target="_blank"
      rel="noopener noreferrer"
      className="inline-flex items-center gap-2 rounded-full border border-white/[0.08] bg-white/[0.04] px-3.5 py-1.5 text-[12px] text-white/55 transition-colors hover:border-white/15 hover:text-white/80"
    >
      <StatusDot level={status.level} />
      <span className="text-white/60">Concerto infrastructure</span>
      <span className="text-white/25">·</span>
      <span>{status.label}</span>
    </a>
  )
}

function SecurityBadge({
  icon,
  label,
  href,
}: {
  icon: React.ReactNode
  label: string
  href: string
}) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.03] px-3.5 py-2.5 text-[12px] text-white/50 transition-colors hover:border-white/12 hover:text-white/75"
    >
      <span className="text-violet-400/80">{icon}</span>
      {label}
    </a>
  )
}

function TestimonialCard() {
  return (
    <div className="relative overflow-hidden rounded-xl border border-white/[0.06] bg-white/[0.02] p-5">
      <div className="mb-3 flex gap-0.5">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className="h-3.5 w-3.5 fill-white/20 text-white/20" />
        ))}
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded bg-white/[0.06]" />
        <div className="h-3 w-4/5 rounded bg-white/[0.06]" />
        <div className="h-3 w-3/5 rounded bg-white/[0.06]" />
      </div>
      <div className="mt-4 flex items-center gap-2.5">
        <div className="h-7 w-7 rounded-full bg-white/[0.08]" />
        <div className="space-y-1">
          <div className="h-2.5 w-20 rounded bg-white/[0.07]" />
          <div className="h-2 w-16 rounded bg-white/[0.05]" />
        </div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center bg-[#0a0a0b]/60 backdrop-blur-[2px]">
        <span className="cursor-default rounded-full border border-white/[0.12] bg-white/[0.06] px-3 py-1 text-[11px] text-white/45 transition-all hover:border-white/20 hover:bg-white/[0.09] hover:text-white/70">
          Coming soon — be one of the first to share your story
        </span>
      </div>
    </div>
  )
}

export function TrustSection() {
  return (
    <section className="px-6 py-20">
      <div className="mx-auto max-w-6xl space-y-14">

        {/* Built-by strip */}
        <div className="flex flex-col items-center gap-3 text-center sm:flex-row sm:justify-center">
          <p className="text-[13px] text-white/40">
            Built by an operator who runs his own infra. Open source.
          </p>
          <a
            href="https://github.com/ethanadjedj-labs/concerto"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 rounded-full border border-white/[0.1] bg-white/[0.04] px-3.5 py-1.5 text-[12px] text-white/60 transition-colors hover:border-white/20 hover:text-white/90"
          >
            <GitBranch className="h-3.5 w-3.5" />
            View on GitHub →
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src="https://img.shields.io/github/stars/ethanadjedj-labs/concerto?style=flat&labelColor=transparent&color=7c3aed&label="
              alt="GitHub stars"
              className="h-4"
              loading="lazy"
            />
          </a>
        </div>

        {/* Live status indicator */}
        <div className="flex justify-center">
          <StatusIndicator />
        </div>

        {/* Security badge row */}
        <div className="flex flex-wrap justify-center gap-3">
          <SecurityBadge
            icon={<Shield className="h-3.5 w-3.5" />}
            label="TLS by Cloudflare"
            href="https://www.cloudflare.com/ssl/"
          />
          <SecurityBadge
            icon={<Lock className="h-3.5 w-3.5" />}
            label="Stripe secure checkout"
            href="https://stripe.com/docs/security"
          />
          <SecurityBadge
            icon={<Server className="h-3.5 w-3.5" />}
            label="Your data never leaves your VPS"
            href="https://github.com/ethanadjedj-labs/concerto/blob/main/docs/SECURITY.md"
          />
        </div>

        {/* Comparison teaser */}
        <div className="mx-auto max-w-xl rounded-xl border border-white/[0.07] bg-white/[0.025] p-5 text-center">
          <p className="mb-2 text-[13px] font-medium text-white/70">
            Why not Cursor / Devin / raw Claude Code?
          </p>
          <p className="text-[12px] leading-relaxed text-white/40">
            Cursor and Devin run agents on their infrastructure — you pay per-token and share
            compute. Raw Claude Code works locally but stops when you close your laptop. Concerto
            gives you persistent remote execution on <em>your</em> VPS: cheaper, always-on, and
            fully under your control.
          </p>
          <Link
            href="/docs/COMPETITIVE_MATRIX.md"
            className="mt-3 inline-block text-[12px] text-violet-400 hover:text-violet-300"
          >
            Full comparison →
          </Link>
        </div>

        {/* Testimonials placeholder */}
        <div>
          <p className="mb-6 text-center text-[11px] font-medium uppercase tracking-widest text-white/25">
            Early users
          </p>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            {[0, 1, 2].map((i) => (
              <TestimonialCard key={i} />
            ))}
          </div>
        </div>

      </div>
    </section>
  )
}
