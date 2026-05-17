"use client"

import { useEffect, useState } from "react"
import { CheckCircle2, AlertTriangle, XCircle, Loader2, Clock } from "lucide-react"

interface Service {
  name: string
  status: "operational" | "degraded" | "down" | "unknown"
  latency_ms: number | null
}

interface StatusData {
  updated_at: number
  services: Service[]
  incidents: { id: string; title: string; body: string; resolved: boolean }[]
  _error?: string
}

function StatusIcon({ status }: { status: Service["status"] }) {
  if (status === "operational")
    return <CheckCircle2 className="h-5 w-5 text-green-400 shrink-0" />
  if (status === "degraded")
    return <AlertTriangle className="h-5 w-5 text-yellow-400 shrink-0" />
  if (status === "down")
    return <XCircle className="h-5 w-5 text-red-400 shrink-0" />
  return <Loader2 className="h-5 w-5 text-white/30 shrink-0 animate-spin" />
}

function StatusBadge({ status }: { status: Service["status"] }) {
  const map: Record<string, string> = {
    operational: "bg-green-500/10 text-green-400 border-green-500/20",
    degraded: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
    down: "bg-red-500/10 text-red-400 border-red-500/20",
    unknown: "bg-white/5 text-white/30 border-white/10",
  }
  return (
    <span
      className={`rounded-full border px-2.5 py-0.5 text-xs font-medium capitalize ${map[status] ?? map.unknown}`}
    >
      {status}
    </span>
  )
}

function overallStatus(services: Service[]): "operational" | "degraded" | "down" | "unknown" {
  if (!services.length) return "unknown"
  if (services.some((s) => s.status === "down")) return "down"
  if (services.some((s) => s.status === "degraded")) return "degraded"
  if (services.some((s) => s.status === "unknown")) return "unknown"
  return "operational"
}

function formatRelative(ts: number): string {
  const diff = Math.floor(Date.now() / 1000 - ts)
  if (diff < 60) return `${diff}s ago`
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`
  return `${Math.floor(diff / 3600)}h ago`
}

export default function StatusPage() {
  const [data, setData] = useState<StatusData | null>(null)
  const [loading, setLoading] = useState(true)

  async function refresh() {
    try {
      const res = await fetch("/api/status", { cache: "no-store" })
      const json: StatusData = await res.json()
      setData(json)
    } catch {
      // keep stale data
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, 60_000)
    return () => clearInterval(id)
  }, [])

  const overall = data ? overallStatus(data.services) : "unknown"

  const overallLabel: Record<string, string> = {
    operational: "All systems operational",
    degraded: "Partial degradation",
    down: "Service disruption",
    unknown: "Checking…",
  }

  const overallColor: Record<string, string> = {
    operational: "text-green-400",
    degraded: "text-yellow-400",
    down: "text-red-400",
    unknown: "text-white/40",
  }

  return (
    <div className="min-h-screen bg-[#080810] text-white">
      <div className="mx-auto max-w-2xl px-4 py-16">
        {/* Header */}
        <div className="mb-10 flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-violet-600">
            <span className="text-lg">◎</span>
          </div>
          <div>
            <h1 className="text-xl font-semibold">Concerto Status</h1>
            <p className="text-sm text-white/40">status.concerto.run</p>
          </div>
        </div>

        {/* Overall banner */}
        <div className="mb-8 rounded-2xl border border-white/8 bg-white/[0.02] p-6">
          {loading ? (
            <div className="flex items-center gap-3">
              <Loader2 className="h-6 w-6 animate-spin text-white/30" />
              <span className="text-white/50">Fetching status…</span>
            </div>
          ) : (
            <div className="flex items-center justify-between">
              <div>
                <p className={`text-lg font-semibold ${overallColor[overall]}`}>
                  {overallLabel[overall]}
                </p>
                {data && (
                  <p className="mt-1 flex items-center gap-1 text-xs text-white/30">
                    <Clock className="h-3 w-3" />
                    Updated {formatRelative(data.updated_at)} · auto-refreshes every 60 s
                  </p>
                )}
              </div>
              <StatusIcon status={overall} />
            </div>
          )}
        </div>

        {/* Services */}
        {data && (
          <div className="mb-8 space-y-2">
            <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-white/30">
              Services
            </h2>
            {data.services.map((svc) => (
              <div
                key={svc.name}
                className="flex items-center justify-between rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3"
              >
                <div className="flex items-center gap-3">
                  <StatusIcon status={svc.status} />
                  <span className="text-sm font-medium text-white/80">{svc.name}</span>
                </div>
                <div className="flex items-center gap-3">
                  {svc.latency_ms !== null && (
                    <span className="text-xs text-white/30">{svc.latency_ms} ms</span>
                  )}
                  <StatusBadge status={svc.status} />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Incidents */}
        {data && data.incidents.length > 0 && (
          <div className="mb-8">
            <h2 className="mb-3 text-xs font-medium uppercase tracking-wider text-white/30">
              Incidents
            </h2>
            <div className="space-y-3">
              {data.incidents.map((inc) => (
                <div
                  key={inc.id}
                  className="rounded-xl border border-yellow-500/20 bg-yellow-500/5 p-4"
                >
                  <div className="flex items-center gap-2">
                    <AlertTriangle className="h-4 w-4 text-yellow-400" />
                    <span className="text-sm font-medium text-yellow-300">{inc.title}</span>
                    {inc.resolved && (
                      <span className="ml-auto text-xs text-green-400">Resolved</span>
                    )}
                  </div>
                  {inc.body && (
                    <p className="mt-2 text-xs leading-relaxed text-white/50">{inc.body}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No incidents message */}
        {data && data.incidents.length === 0 && (
          <div className="mb-8 rounded-xl border border-white/8 bg-white/[0.02] px-4 py-3 text-center text-xs text-white/30">
            No incidents in the last 30 days
          </div>
        )}

        {/* Footer */}
        <div className="text-center text-xs text-white/20">
          <a href="/" className="hover:text-white/50 transition-colors">
            concerto.run
          </a>
          {" · "}
          <a href="/help" className="hover:text-white/50 transition-colors">
            Help center
          </a>
        </div>
      </div>
    </div>
  )
}
