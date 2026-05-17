"use client"

import { useEffect, useState } from "react"
import { Clock, ArrowRight } from "lucide-react"
import Link from "next/link"

interface Props {
  token: string
  expiresAt: number   // unix timestamp (seconds)
}

function fmt(seconds: number): string {
  if (seconds <= 0) return "0:00"
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, "0")}`
}

export function TrialCountdownBanner({ token, expiresAt }: Props) {
  const [remaining, setRemaining] = useState<number>(
    Math.max(0, expiresAt - Math.floor(Date.now() / 1000))
  )

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining(Math.max(0, expiresAt - Math.floor(Date.now() / 1000)))
    }, 1000)
    return () => clearInterval(id)
  }, [expiresAt])

  const expired = remaining === 0
  const urgent  = remaining > 0 && remaining < 5 * 60  // under 5 min

  return (
    <div
      role="alert"
      className={`flex items-center justify-between gap-3 rounded-xl border px-5 py-3.5 ${
        expired
          ? "border-red-500/30 bg-red-500/[0.07]"
          : urgent
          ? "border-orange-500/30 bg-orange-500/[0.07]"
          : "border-[rgba(217,119,87,0.3)] bg-[rgba(217,119,87,0.07)]"
      }`}
    >
      <div className="flex items-center gap-3 min-w-0">
        <Clock
          className={`h-4.5 w-4.5 shrink-0 ${
            expired ? "text-red-400" : urgent ? "text-orange-400" : "text-[#d97757]"
          }`}
        />
        <div className="min-w-0">
          {expired ? (
            <p className="text-[14px] font-semibold text-red-300">Trial expired</p>
          ) : (
            <p className="text-[14px] font-semibold text-[#f5f0e9]">
              Trial expires in{" "}
              <span
                className={`font-mono tabular-nums ${
                  urgent ? "text-orange-300" : "text-[#d97757]"
                }`}
              >
                {fmt(remaining)}
              </span>
            </p>
          )}
          <p className="mt-0.5 text-[12px] text-white/40 truncate">
            {expired
              ? "Your workspace has been destroyed."
              : "Upgrade to keep your workspace alive after the trial ends."}
          </p>
        </div>
      </div>

      <Link
        href={`/upgrade/${token}`}
        className={`shrink-0 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors ${
          expired
            ? "bg-red-500/15 text-red-300 hover:bg-red-500/25"
            : "bg-[rgba(217,119,87,0.15)] text-[#d97757] hover:bg-[rgba(217,119,87,0.25)]"
        }`}
      >
        Upgrade <ArrowRight className="h-3.5 w-3.5" />
      </Link>
    </div>
  )
}
