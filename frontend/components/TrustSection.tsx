"use client"

import { useEffect, useState } from "react"
import { Shield, Lock } from "lucide-react"

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
      <span className="text-[#8a847b]">Concerto status</span>
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


export function TrustSection() {
  return (
    <section className="px-6 py-20" style={{ background: "#faf9f5" }}>
      <div className="mx-auto max-w-6xl space-y-14">

        {/* Built-by strip */}
        <div className="flex flex-col items-center gap-2 text-center">
          <p className="text-[13px] text-[#8a847b]">
            Built by an operator using Concerto himself.
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
            icon={<Shield className="h-3.5 w-3.5" />}
            label="Your Claude Code runs are isolated from other customers"
            href="/legal/privacy"
          />
        </div>

      </div>
    </section>
  )
}
