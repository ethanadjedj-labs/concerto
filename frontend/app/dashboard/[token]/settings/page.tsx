"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import {
  ExternalLink,
  CreditCard,
  RotateCcw,
  Ban,
  AlertTriangle,
  ArrowLeft,
  CalendarClock,
} from "lucide-react"

function LogoMark({ size = 28 }: { size?: number }) {
  return (
    <img
      src="/brand/logo-mark.png?v=3"
      alt="Concerto"
      width={size}
      height={size}
      style={{ display: "block", width: size, height: size }}
    />
  )
}

function PastDueBanner() {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl px-5 py-4"
      style={{
        border: "1px solid rgba(234,179,8,0.3)",
        backgroundColor: "rgba(234,179,8,0.07)",
      }}
    >
      <CreditCard
        className="mt-0.5 h-4 w-4 shrink-0"
        style={{ color: "#ca8a04" }}
      />
      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold" style={{ color: "#92400e" }}>
          Payment past due
        </p>
        <p
          className="mt-1 text-[13px] leading-relaxed"
          style={{ color: "#78350f" }}
        >
          Your subscription payment failed. Update your payment method to avoid
          suspension.
        </p>
      </div>
      <a
        href="https://billing.stripe.com"
        target="_blank"
        rel="noopener noreferrer"
        className="shrink-0 mt-0.5 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-opacity hover:opacity-80"
        style={{
          backgroundColor: "rgba(234,179,8,0.12)",
          color: "#92400e",
        }}
      >
        Update billing <ExternalLink className="h-3.5 w-3.5" />
      </a>
    </div>
  )
}

function SuspendedBanner() {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl px-5 py-4"
      style={{
        border: "1px solid rgba(249,115,22,0.3)",
        backgroundColor: "rgba(249,115,22,0.07)",
      }}
    >
      <Ban
        className="mt-0.5 h-4 w-4 shrink-0"
        style={{ color: "#ea580c" }}
      />
      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold" style={{ color: "#9a3412" }}>
          Access suspended
        </p>
        <p
          className="mt-1 text-[13px] leading-relaxed"
          style={{ color: "#7c2d12" }}
        >
          Your Concerto access is paused due to a failed payment. Your data is
          safe. Update your payment method to resume instantly.
        </p>
      </div>
      <a
        href="https://billing.stripe.com"
        target="_blank"
        rel="noopener noreferrer"
        className="shrink-0 mt-0.5 inline-flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-[13px] font-medium transition-opacity hover:opacity-80"
        style={{
          backgroundColor: "rgba(249,115,22,0.12)",
          color: "#9a3412",
        }}
      >
        Resume billing <ExternalLink className="h-3.5 w-3.5" />
      </a>
    </div>
  )
}

function RefundedBanner() {
  return (
    <div
      role="alert"
      className="flex items-start gap-3 rounded-xl px-5 py-4"
      style={{
        border: "1px solid rgba(59,130,246,0.3)",
        backgroundColor: "rgba(59,130,246,0.07)",
      }}
    >
      <RotateCcw
        className="mt-0.5 h-4 w-4 shrink-0"
        style={{ color: "#2563eb" }}
      />
      <div className="flex-1 min-w-0">
        <p className="text-[14px] font-semibold" style={{ color: "#1e40af" }}>
          Refund processed
        </p>
        <p
          className="mt-1 text-[13px] leading-relaxed"
          style={{ color: "#1e3a8a" }}
        >
          Your refund has been issued. Allow 5–10 business days. Questions?{" "}
          <a
            href="mailto:support@concerto.run"
            className="underline hover:opacity-80"
          >
            support@concerto.run
          </a>
        </p>
      </div>
    </div>
  )
}

function RefundButton({
  token,
  backendUrl,
  eligible,
}: {
  token: string
  backendUrl: string
  eligible: boolean
}) {
  const [step, setStep] = useState<"idle" | "confirming" | "done" | "error">(
    "idle"
  )
  const [loading, setLoading] = useState(false)
  const [errMsg, setErrMsg] = useState("")

  async function doRefund() {
    setLoading(true)
    try {
      const res = await fetch(`${backendUrl}/api/buyer/${token}/refund`, {
        method: "POST",
      })
      if (!res.ok) {
        const body = await res.json().catch(() => ({}))
        throw new Error(
          body?.detail?.message ?? body?.detail ?? "Refund request failed"
        )
      }
      setStep("done")
    } catch (err: unknown) {
      setStep("error")
      setErrMsg(err instanceof Error ? err.message : "Unexpected error")
    } finally {
      setLoading(false)
    }
  }

  if (!eligible) return null

  if (step === "done") {
    return (
      <p className="text-[13px]" style={{ color: "#16a34a" }}>
        ✓ Refund initiated — allow 5–10 business days.
      </p>
    )
  }

  if (step === "confirming") {
    return (
      <div className="flex flex-wrap items-center gap-2">
        <p className="text-[13px]" style={{ color: "#8a847b" }}>
          Are you sure? This cannot be undone.
        </p>
        <Button
          variant="ghost"
          size="sm"
          onClick={doRefund}
          disabled={loading}
          className="h-8 px-3 text-[13px]"
          style={{ color: "#dc2626" }}
        >
          {loading ? "Processing..." : "Yes, refund"}
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => setStep("idle")}
          disabled={loading}
          className="h-8 px-3 text-[13px]"
          style={{ color: "#8a847b" }}
        >
          Cancel
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setStep("confirming")}
        className="h-8 gap-1.5 px-3 text-[13px]"
        style={{ color: "#8a847b" }}
      >
        <RotateCcw className="h-3 w-3" />
        Request refund
      </Button>
      {step === "error" && (
        <p className="text-[12px]" style={{ color: "#dc2626" }}>
          {errMsg}
        </p>
      )}
    </div>
  )
}

export default function SettingsPage({
  params,
}: {
  params: { token: string }
}) {
  const [data, setData] = useState<{
    plan?: string
    status?: string
    subscription_status?: string
    next_renewal_at?: number
    refund_eligible?: boolean
    refund_window_open?: boolean
    email?: string
    created_at?: number
  } | null>(null)

  const backendUrl =
    process.env.NEXT_PUBLIC_BACKEND_URL ?? "https://api.concerto.run"

  useEffect(() => {
    fetch(`${backendUrl}/api/buyer/${params.token}/status`)
      .then((r) => r.json())
      .then((d) =>
        setData({
          plan: d.plan,
          status: d.status,
          subscription_status: d.subscription_status,
          next_renewal_at: d.next_renewal_at,
          refund_eligible: d.refund_eligible,
          refund_window_open: d.refund_window_open,
          email: d.email,
          created_at: d.created_at,
        })
      )
      .catch(() => {})
  }, [backendUrl, params.token])

  const plan = data?.plan ?? "solo"
  const status = data?.status ?? "active"
  const planLabel = plan === "pro" ? "Pro" : "Solo"
  const planPrice = plan === "pro" ? "$99/month" : "$49/month"
  const isHosted = plan === "solo" || plan === "pro" || plan === "hosted"
  const isSuspended = status === "suspended"
  const isRefunded = status === "refunded"
  const isPastDue =
    status === "subscription_past_due" ||
    data?.subscription_status === "past_due"

  const nextRenewal = data?.next_renewal_at
    ? new Date(data.next_renewal_at * 1000).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : null

  const createdAt = data?.created_at
    ? new Date(data.created_at * 1000).toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      })
    : null

  function getStatusBadge() {
    if (isRefunded)
      return (
        <Badge
          style={{
            border: "1px solid rgba(59,130,246,0.25)",
            backgroundColor: "rgba(59,130,246,0.08)",
            color: "#2563eb",
          }}
        >
          Refunded
        </Badge>
      )
    if (isSuspended)
      return (
        <Badge
          style={{
            border: "1px solid rgba(249,115,22,0.25)",
            backgroundColor: "rgba(249,115,22,0.08)",
            color: "#ea580c",
          }}
        >
          <span
            className="mr-1.5 inline-block h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: "#ea580c" }}
          />
          Suspended
        </Badge>
      )
    if (isPastDue)
      return (
        <Badge
          style={{
            border: "1px solid rgba(234,179,8,0.25)",
            backgroundColor: "rgba(234,179,8,0.08)",
            color: "#ca8a04",
          }}
        >
          Payment due
        </Badge>
      )
    return (
      <Badge
        style={{
          border: "1px solid rgba(34,197,94,0.25)",
          backgroundColor: "rgba(34,197,94,0.08)",
          color: "#16a34a",
        }}
      >
        <span
          className="mr-1.5 inline-block h-1.5 w-1.5 animate-pulse rounded-full"
          style={{ backgroundColor: "#16a34a" }}
        />
        Active
      </Badge>
    )
  }

  return (
    <div
      className="min-h-screen"
      style={{ backgroundColor: "#faf9f5", color: "#191919" }}
    >
      {/* ── Header ── */}
      <header
        className="sticky top-0 z-10"
        style={{
          borderBottom: "1px solid rgba(25,25,25,0.07)",
          backgroundColor: "rgba(250,249,245,0.90)",
          backdropFilter: "blur(12px)",
        }}
      >
        <div className="mx-auto flex max-w-2xl items-center justify-between px-5 py-3.5">
          <div className="flex items-center gap-2.5">
            <LogoMark size={28} />
            <span
              className="text-[18px] font-medium leading-none tracking-tight"
              style={{ color: "#191919" }}
            >
              Concerto
            </span>
          </div>
          <Link
            href={`/dashboard/${params.token}`}
            className="flex items-center gap-1.5 text-[13px] transition-opacity hover:opacity-70"
            style={{ color: "#8a847b" }}
          >
            <ArrowLeft className="h-3.5 w-3.5" />
            Back to dashboard
          </Link>
        </div>
      </header>

      <main className="mx-auto max-w-md space-y-4 px-5 py-10">
        <h1
          className="mb-6 text-[24px] font-semibold"
          style={{ color: "#191919" }}
        >
          Account settings
        </h1>

        {/* Status banners */}
        {isPastDue && <PastDueBanner />}
        {isSuspended && <SuspendedBanner />}
        {isRefunded && <RefundedBanner />}

        {/* Subscription card */}
        {isHosted && (
          <div
            className="rounded-2xl p-6 space-y-4"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <div className="flex items-center gap-2">
              <CalendarClock className="h-4 w-4" style={{ color: "#cc785c" }} />
              <span
                className="text-[15px] font-semibold"
                style={{ color: "#191919" }}
              >
                Subscription
              </span>
            </div>

            <div style={{ borderTop: "1px solid #f3efe5" }} />

            <div className="space-y-3">
              <div className="flex items-center justify-between text-[14px]">
                <span style={{ color: "#8a847b" }}>Plan</span>
                <span style={{ color: "#191919" }}>
                  {planLabel} — {planPrice}
                </span>
              </div>
              <div className="flex items-center justify-between text-[14px]">
                <span style={{ color: "#8a847b" }}>Status</span>
                {getStatusBadge()}
              </div>
              {nextRenewal && (
                <div className="flex items-center justify-between text-[14px]">
                  <span style={{ color: "#8a847b" }}>Next renewal</span>
                  <span style={{ color: "#191919" }}>{nextRenewal}</span>
                </div>
              )}
              {data?.email && (
                <div className="flex items-center justify-between text-[14px]">
                  <span style={{ color: "#8a847b" }}>Email</span>
                  <span style={{ color: "#191919" }}>{data.email}</span>
                </div>
              )}
              {createdAt && (
                <div className="flex items-center justify-between text-[14px]">
                  <span style={{ color: "#8a847b" }}>Member since</span>
                  <span style={{ color: "#191919" }}>{createdAt}</span>
                </div>
              )}
            </div>

            <div style={{ borderTop: "1px solid #f3efe5" }} />

            <a
              href="https://billing.stripe.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex w-full items-center justify-center gap-2 rounded-xl border px-4 py-2.5 text-[14px] font-medium transition-opacity hover:opacity-80"
              style={{
                borderColor: "#f3efe5",
                color: "#191919",
              }}
            >
              <CreditCard className="h-4 w-4" />
              Manage subscription via Stripe
              <ExternalLink className="h-3.5 w-3.5" />
            </a>

            <p
              className="text-center text-[12px]"
              style={{ color: "#8a847b" }}
            >
              Cancel, update payment method, or download invoices. Need to
              upgrade Solo → Pro? Email support@concerto.run.
            </p>
          </div>
        )}

        {/* Refund section */}
        {data?.refund_window_open && (
          <div
            className="rounded-2xl p-6"
            style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
          >
            <p
              className="mb-3 text-[11px] font-medium uppercase tracking-widest"
              style={{ color: "#8a847b" }}
            >
              14-day refund window
            </p>
            <RefundButton
              token={params.token}
              backendUrl={backendUrl}
              eligible={data?.refund_eligible ?? false}
            />
          </div>
        )}

        {/* Support */}
        <div
          className="rounded-2xl p-6 text-center"
          style={{ backgroundColor: "#fff", border: "1px solid #f3efe5" }}
        >
          <AlertTriangle
            className="mx-auto mb-2 h-4 w-4"
            style={{ color: "#8a847b" }}
          />
          <p className="text-[14px]" style={{ color: "#8a847b" }}>
            Need help?{" "}
            <a
              href="mailto:support@concerto.run"
              className="underline transition-opacity hover:opacity-70"
              style={{ color: "#cc785c" }}
            >
              support@concerto.run
            </a>
          </p>
        </div>
      </main>
    </div>
  )
}
