"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Shield, Lock, Server, Star } from "lucide-react"

type StatusLevel = "operational" | "degraded" | "outage" | "unknown"

function StatusDot({ level }: { level: StatusLevel }) {
  const color =
    level === "operational" ? "bg-green-500" :
    level === "degraded"    ? "bg-yellow-500" :
    level === "outage"      ? "bg-red-500" :
                              "bg-[#8a847b]"
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
      className="inline-flex items-center gap-2 rounded-full border px-3.5 py-1.5 text-[12px] text-[#555049] transition-colors hover:text-[#191919]"
      style={{ borderColor: "rgba(25,25,25,0.10)", background: "rgba(25,25,25,0.02)" }}
    >
      <StatusDot level={status.level} />
      <span className="text-[#8a847b]">Concerto infrastructure</span>
      <span className="text-[#8a847b] opacity-40">·</span>
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
      className="flex items-center gap-2 rounded-lg border px-3.5 py-2.5 text-[12px] text-[#8a847b] transition-colors hover:text-[#555049]"
      style={{ borderColor: "rgba(25,25,25,0.08)", background: "rgba(25,25,25,0.02)" }}
      onMouseEnter={(e) => { (e.currentTarget as HTMLAnchorElement).style.borderColor = "rgba(204,120,92,0.25)" }}
      onMouseLeave={(e) => { (e.currentTarget as HTMLAnchorElement).style.borderColor = "rgba(25,25,25,0.08)" }}
    >
      <span className="text-[#cc785c] opacity-75">{icon}</span>
      {label}
    </a>
  )
}

function TestimonialCard() {
  return (
    <div className="relative overflow-hidden rounded-lg border bg-white p-5" style={{ borderColor: "rgba(25,25,25,0.08)" }}>
      <div className="mb-3 flex gap-0.5">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className="h-3.5 w-3.5 fill-[rgba(25,25,25,0.08)] text-[rgba(25,25,25,0.08)]" />
        ))}
      </div>
      <div className="space-y-2">
        <div className="h-3 w-full rounded" style={{ background: "rgba(25,25,25,0.05)" }} />
        <div className="h-3 w-4/5 rounded" style={{ background: "rgba(25,25,25,0.05)" }} />
        <div className="h-3 w-3/5 rounded" style={{ background: "rgba(25,25,25,0.05)" }} />
      </div>
      <div className="mt-4 flex items-center gap-2.5">
        <div className="h-7 w-7 rounded-full" style={{ background: "rgba(25,25,25,0.07)" }} />
        <div className="space-y-1">
          <div className="h-2.5 w-20 rounded" style={{ background: "rgba(25,25,25,0.07)" }} />
          <div className="h-2 w-16 rounded" style={{ background: "rgba(25,25,25,0.05)" }} />
        </div>
      </div>
      <div className="absolute inset-0 flex items-center justify-center rounded-lg backdrop-blur-[2px]" style={{ background: "rgba(250,249,245,0.7)" }}>
        <span className="cursor-default rounded-full border px-3 py-1 text-[11px] text-[#8a847b] transition-all hover:text-[#555049]" style={{ borderColor: "rgba(25,25,25,0.12)", background: "rgba(250,249,245,0.8)" }}>
          Coming soon — be one of the first to share your story
        </span>
      </div>
    </div>
  )
}

export function TrustSection() {
  return (
    <section className="px-6 py-20" style={{ background: "#faf9f5" }}>
      <div className="mx-auto max-w-6xl space-y-14">

        {/* Built-by strip */}
        <div className="flex flex-col items-center gap-2 text-center">
          <p className="text-[13px] text-[#8a847b]">
            Built by a solo operator who runs the same infrastructure himself.
          </p>
          <p className="text-[13px] text-[#8a847b]">
            Real human support, real maintenance.
          </p>
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
            label="Your workspace is isolated from other customers"
            href="/legal/privacy"
          />
        </div>

        {/* Comparison teaser */}
        <div className="mx-auto max-w-xl rounded-lg border bg-white p-5 text-center" style={{ borderColor: "rgba(25,25,25,0.08)", boxShadow: "0 1px 2px rgba(25,25,25,0.04)" }}>
          <p className="mb-2 text-[13px] font-medium text-[#191919]">
            Why not Cursor / Devin / raw Claude Code?
          </p>
          <p className="text-[12px] leading-relaxed text-[#8a847b]">
            Cursor and Devin run agents on their infrastructure — you pay per-token and share
            compute. Raw Claude Code works locally but stops when you close your laptop. Concerto
            gives you persistent remote execution on a dedicated workspace: always-on, and
            fully under your control.
          </p>
          <Link
            href="/docs/COMPETITIVE_MATRIX.md"
            className="mt-3 inline-block text-[12px] text-[#cc785c] hover:underline"
          >
            Full comparison →
          </Link>
        </div>

        {/* Testimonials placeholder */}
        <div>
          <p className="mb-6 text-center text-[11px] font-medium uppercase tracking-widest text-[#8a847b]">
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
